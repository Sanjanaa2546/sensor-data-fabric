import re
import logging
import sqlglot
from sqlglot import exp, parse_one, transpile
from typing import Set, Tuple, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Dangerous DuckDB extensions/functions that could interact with OS or external files
DISALLOWED_FUNCTIONS: Set[str] = {
    "read_csv", "read_csv_auto", "read_parquet", "read_json", "read_json_auto",
    "readcsv", "readparquet", "readjson",
    "httpfs", "load", "install", "copy", "export_database", "import_database",
    "getenv", "current_setting", "system"
}

class SQLValidationError(Exception):
    """Raised when proposed SQL violates Data Fabric security guardrails."""
    pass

class SQLValidator:
    def __init__(
        self,
        allowed_tables: Optional[Set[str]] = None,
        default_limit: int = settings.DEFAULT_ROW_LIMIT,
        max_limit: int = settings.MAX_ROW_LIMIT
    ):
        self.allowed_tables = set(t.lower() for t in (allowed_tables or settings.ALLOWED_TABLES))
        self.default_limit = default_limit
        self.max_limit = max_limit

    def validate_and_sanitize(self, raw_sql: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validates the proposed SQL query using sqlglot AST parsing.
        
        Returns:
            Tuple[is_safe (bool), sanitized_sql (str), rejection_reason (Optional[str])]
        """
        clean_sql = raw_sql.strip()
        
        # 1. Reject empty queries
        if not clean_sql:
            return False, "", "Empty query string provided."

        # 2. Check for multiple statements (semicolon attacks)
        try:
            parsed_statements = sqlglot.parse(clean_sql, read="duckdb")
        except Exception as e:
            return False, clean_sql, f"SQL Syntax Error: Unable to parse query ({str(e)})"

        valid_statements = [stmt for stmt in parsed_statements if stmt is not None]
        if len(valid_statements) > 1:
            return False, clean_sql, "Multiple SQL statements detected. Only single SELECT queries are permitted."

        if not valid_statements:
            return False, clean_sql, "No valid SQL statement parsed."

        ast: exp.Expression = valid_statements[0]

        # 3. SELECT-Only Check
        if not isinstance(ast, (exp.Select, exp.Union)):
            return False, clean_sql, f"Security Violation: Statement type '{ast.key.upper()}' is forbidden. Only SELECT queries are permitted."

        # Walk entire AST to ensure no destructive nodes anywhere in subqueries or CTEs
        destructive_types = (
            exp.Drop, exp.Delete, exp.Insert, exp.Update, exp.Create, 
            exp.Alter, exp.Command, exp.Pragma, exp.TruncateTable
        )
        for node in ast.walk():
            if isinstance(node, destructive_types):
                return False, clean_sql, f"Security Violation: Found prohibited operation '{node.key.upper()}' in AST."

        # 4. Dangerous Function / System Intrinsic Call Check
        for node in ast.walk():
            key_name = getattr(node, "key", "").lower()
            if key_name in DISALLOWED_FUNCTIONS:
                return False, clean_sql, f"Security Violation: Operation '{key_name}' is blocked by security policy."
            
            node_name = getattr(node, "name", "").lower()
            if node_name in DISALLOWED_FUNCTIONS:
                return False, clean_sql, f"Security Violation: Function '{node_name}' is blocked by security policy."

            if isinstance(node, exp.Anonymous) and str(node.this).lower() in DISALLOWED_FUNCTIONS:
                return False, clean_sql, f"Security Violation: Function '{node.this}' is blocked by security policy."

        # 5. Table Allowlist Check
        # Track CTE (Common Table Expression) alias names so they are recognized
        cte_aliases: Set[str] = {cte.alias.lower() for cte in ast.ctes if cte.alias}

        # Inspect all Table references in AST
        tables_in_query: Set[str] = set()
        for table_node in ast.find_all(exp.Table):
            table_name = table_node.name.lower()
            if not table_name:
                # If table node has no name, it could be a function table like read_csv or subquery
                if not isinstance(table_node.this, (exp.Identifier, exp.Var)):
                    return False, clean_sql, f"Security Violation: Non-standard table expression '{table_node.sql()}' is prohibited."
            elif table_name not in cte_aliases:
                tables_in_query.add(table_name)

        # Check against allowlist
        disallowed_tables = tables_in_query - self.allowed_tables
        if disallowed_tables:
            return False, clean_sql, f"Access Denied: Query attempts to access unauthorized table(s): {', '.join(sorted(disallowed_tables))}. Allowed tables: {', '.join(sorted(self.allowed_tables))}."

        # 6. Row Limit Enforcement (AST Rewriting)
        sanitized_ast = self._enforce_limit(ast)
        sanitized_sql = sanitized_ast.sql(dialect="duckdb")

        return True, sanitized_sql, None

    def _enforce_limit(self, ast: exp.Expression) -> exp.Expression:
        """
        Inspects the AST for a LIMIT clause.
        If absent, appends default_limit.
        If present but exceeds max_limit, caps it at max_limit.
        """
        cloned_ast = ast.copy()

        if isinstance(cloned_ast, (exp.Select, exp.Union)):
            limit_exp = cloned_ast.args.get("limit")
            if limit_exp is None:
                cloned_ast = cloned_ast.limit(self.default_limit)
            else:
                try:
                    limit_val = int(limit_exp.expression.this)
                    if limit_val > self.max_limit:
                        cloned_ast.set("limit", exp.Limit(expression=exp.Literal.number(self.max_limit)))
                    elif limit_val <= 0:
                        cloned_ast.set("limit", exp.Limit(expression=exp.Literal.number(self.default_limit)))
                except (ValueError, AttributeError):
                    cloned_ast.set("limit", exp.Limit(expression=exp.Literal.number(self.default_limit)))

        return cloned_ast

# Singleton instance
validator = SQLValidator()
