# AeroFabric: Chat with Your Sensor Data 🌬️📊
### Enterprise IoT Sensor Data Fabric with SQL AST Guardrails & AI Tool Calling

> **Tailored for Data Fabric & AI Engineering Roles (UiPath, Snowflake, Databricks, AWS)**  
> *Ingest data • Govern access with AST parsing • Query with OLAP speed • Add agentic AI tool calling*

---

## 🌟 Executive Overview

**AeroFabric** is an enterprise-grade IoT Data Fabric that allows users to converse with live pollution sensor telemetry in plain English. 

The core architectural highlight that differentiates this project in senior technical interviews is **the AI Security & Validation Layer**:
* **The LLM never touches the database directly.**
* The model operates strictly through tool calling (`run_query`), proposing parameterized SQL queries against schema metadata.
* Before any SQL touches the analytical engine, a deterministic validation layer parses the Abstract Syntax Tree (AST) using `sqlglot`, verifying that it is strictly **SELECT-only**, accesses **only authorized tables**, enforces **row count limits**, prevents **semicolon chaining**, and logs every execution to a persistent **governance audit trail**.
* Flagged time-series deviations (e.g. industrial particulate inversions or sensor glitches) are surfaced by a **Z-Score & Rolling-Average Anomaly Engine** and synthesized in natural language.

---

## 🏗️ Architecture Diagram

```mermaid
flowchart TD
    User["User / Environmental Analyst"] -->|Natural Language Query| UI["React 19 Dashboard (Vite + Tailwind)"]
    
    subgraph Frontend ["Frontend Presentation Layer"]
        UI --> Chat["Interactive ChatBox"]
        UI --> Inspector["SQL Guardrail Inspector"]
        UI --> Charts["Dynamic Recharts (Time-Series & Bar)"]
        UI --> Table["Interactive CSV Data Table"]
        UI --> Sentinel["Time-Series Anomaly Feed"]
    end

    UI -->|REST API| API["FastAPI Backend Gateway (:8000)"]

    subgraph DataFabric ["AeroFabric Core Backend"]
        API --> Agent["LLM Tool Calling Agent"]
        Agent -->|1. Proposes SQL Query| Tool["run_query Tool Call"]
        
        subgraph GovernanceLayer ["Enterprise Guardrail & Governance (The Interview Star)"]
            Tool --> AST["AST Parser (sqlglot)"]
            AST --> ASTCheck{"Is Query Safe?"}
            ASTCheck -->|Violates Policy (DROP/INSERT/Unauthorized Table)| Block["Query Blocked & Audited"]
            ASTCheck -->|Passed| Sanitize["LIMIT Injection & Column Allowlist"]
            Block --> AuditLog[("query_audit_log")]
            Sanitize --> AuditLog
        end

        Sanitize -->|2. Executes Safe SQL| DuckDB[("DuckDB Columnar OLAP Engine")]
        DuckDB -->|3. Structured Records| Agent
        Agent -->|4. Synthesizes Answer + Metrics| API
        
        API --> AnomalyEngine["Statistical Anomaly Engine (Z-Score + 24h Rolling Mean)"]
        AnomalyEngine <--> DuckDB
    end
```

---

## 🛠️ The Tech Stack

| Layer | Technology | Key Capabilities & Rationale |
|---|---|---|
| **Storage & OLAP** | **DuckDB** | Columnar, vectorized in-process analytical database. Up to 100x faster than SQLite/PostgreSQL for time-series sensor aggregations. |
| **API Backend** | **Python 3.12 + FastAPI** | High-performance asynchronous REST API with Pydantic typing, auto OpenAPI docs, and clean router modularity. |
| **Security & Guardrails**| **sqlglot** | Full SQL AST parsing. Inspects query trees, enforces SELECT-only restrictions, blocks command injections, and rewrites limits. |
| **Time-Series Analytics**| **NumPy & Pandas** | Vectorized statistical $Z$-score calculations, 24-hour moving average baselines, and spike ratio anomaly detection. |
| **AI Tool Calling** | **Multi-Provider Agent** | Supports Gemini, OpenAI, Claude, plus an intelligent zero-key local synthesizer for out-of-the-box evaluations. |
| **Frontend UI** | **React 19 + Vite** | Modern reactive dashboard with Tailwind CSS, Lucide icons, Recharts visualizations, and live SQL inspector drawers. |
| **Deployment** | **Docker & AWS App Runner** | Multi-stage Docker container serving both compiled React frontend and FastAPI backend on port 8000. |

---

## 🛡️ The Guardrail Layer: Why Interviewers Care

Most simple "Chat with SQL" tutorials give an LLM direct database credentials or run raw string queries. In enterprise data fabrics (such as UiPath's Data Fabric or Snowflake Horizon), this creates severe security and cost risks:
1. **Destructive Queries:** Accidental or prompt-injected `DROP TABLE`, `TRUNCATE`, or `DELETE`.
2. **Data Exfiltration:** Accessing internal tables (e.g. `user_credentials`, `system_settings`).
3. **Runaway Queries:** `SELECT * FROM telemetry` without limits consuming gigabytes of memory.
4. **Denial of Service:** Multi-statement chaining (`SELECT 1; DROP TABLE ...;`).

### How AeroFabric Solves This
Before any query executes:
1. **Syntax & AST Inspection:** `sqlglot.parse()` converts raw SQL into an AST. If multiple statements exist, it is rejected immediately.
2. **Statement Type Verification:** The root AST node must strictly be `exp.Select` or `exp.Union`. Any `Drop`, `Delete`, `Insert`, `Update`, `Create`, `Alter`, or `TruncateTable` triggers an instant policy block.
3. **Table Whitelist:** The AST traverses all `exp.Table` references. Only `sensor_stations`, `air_quality_readings`, and `query_audit_log` (or internal CTE aliases) are permitted.
4. **LIMIT Enforcement:** If the query lacks a `LIMIT`, the AST rewrites the query to append `LIMIT 100`. If an incoming limit exceeds `1000`, it is capped at `1000`.
5. **Execution Audit Trail:** Every query (successful or rejected) is logged into `query_audit_log` with execution latency, row count, reason, and timestamp.

---

## 📈 Time-Series Anomaly Detection Engine

AeroFabric includes a mathematical anomaly detection engine:
* **Z-Score Calculation:** Measures how many standard deviations an observation deviates from baseline:
  $$Z = \frac{x - \mu}{\sigma}$$
* **24-Hour Rolling Moving Average:** Smooths diurnal traffic and solar cycles to detect sharp localized spikes.
* **Severity Classification:** Readings exceeding $Z \ge 4.0$ or a spike ratio $\ge 3.0$ are classified as `CRITICAL`, while $Z \ge 3.0$ is `HIGH`.
* **Plain Language Explanation:** The engine generates natural language summaries detailing the exact pollutant spike, comparison to the 24h baseline, and official EPA/OpenAQ AQI category (Good, Moderate, Unhealthy, Hazardous).

---

## 🚀 Quickstart Guide

### Option 1: Run Locally (Fastest)

#### Prerequisites
* Python 3.10+
* Node.js v18+

#### 1. Start the Backend
```bash
# Navigate to backend directory
cd sensor-data-fabric/backend

# Install dependencies
pip install -r requirements.txt

# Run automated tests (19 guardrail & API tests)
python -m pytest tests -v

# Start FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* API Documentation: `http://127.0.0.1:8000/docs`
* Health Check: `http://127.0.0.1:8000/health`

#### 2. Start the Frontend
```bash
# In a new terminal, navigate to frontend
cd sensor-data-fabric/frontend

# Install dependencies (if not already done)
npm install

# Start Vite development server
npm run dev
```
* Open your browser at: `http://localhost:5173`

---

### Option 2: Run via Docker Compose (Single Container)

```bash
cd sensor-data-fabric
docker compose up --build
```
* Access the unified app at: `http://localhost:8000`

---

## 🧪 Automated Test Suite

AeroFabric includes 19 rigorous unit and integration tests proving that guardrails block attacks and that analytical queries execute correctly:

```bash
cd sensor-data-fabric/backend
$env:PYTHONPATH="."
python -m pytest tests -v
```

### Verified Test Cases
* `test_drop_table_is_blocked` — Proves `DROP TABLE` is blocked before reaching DuckDB.
* `test_delete_is_blocked` — Proves `DELETE FROM` statements are rejected.
* `test_insert_and_update_blocked` — Rejects mutative statements.
* `test_multiple_statement_chaining_blocked` — Blocks semicolon injection attacks (`SELECT 1; DROP...`).
* `test_unauthorized_tables_blocked` — Blocks access to unauthorized schemas and system tables.
* `test_dangerous_functions_blocked` — Blocks `read_csv`, `getenv`, and shell operations.
* `test_valid_select_allowed_and_limit_injected` — Verifies automatic `LIMIT 100` injection on bare SELECTs.
* `test_excessive_limit_capped` — Verifies that `LIMIT 999999` is safely capped at `1000`.
* `test_valid_ctes_allowed` — Supports advanced analytical CTEs (`WITH ... SELECT`).
* `test_anomaly_detection_identifies_injected_spikes` — Validates mathematical Z-score anomaly detection.
* `test_chat_endpoint_worst_pm25` — Validates tool calling query synthesis.

---

## 💼 Resume Bullets & Interview Talking Points

### Recommended Resume Line:
> **"Built an enterprise IoT Data Fabric with validated LLM tool-calling (FastAPI, DuckDB, sqlglot, React) featuring AST-level SQL guardrails, Z-score anomaly detection, and automated audit governance, deployed on AWS."**

### Key Interview Questions to Crush:

#### 1. "Why didn't you let the LLM execute SQL directly?"
> *"Allowing an LLM to execute raw SQL directly introduces prompt injection vulnerabilities, destructive query risks (`DROP`/`DELETE`), and uncontrolled memory consumption. In AeroFabric, I designed the AI as a proposing agent that calls a `run_query` tool. The backend passes the proposed SQL through `sqlglot` to parse the Abstract Syntax Tree. We verify it is strictly a SELECT statement, check every table against an allowlist, inject a mandatory LIMIT clause, and enforce execution timeouts before DuckDB executes it."*

#### 2. "Why DuckDB over SQLite or PostgreSQL for this use case?"
> *"IoT sensor readings are time-series analytical data (OLAP) characterized by heavy aggregations (`AVG(pm25)`, `MAX(no2)`, rolling windows across millions of rows) rather than row-by-row transactional updates (OLTP). DuckDB's vectorized columnar engine performs these scans orders of magnitude faster with zero server overhead and minimal memory footprint."*

#### 3. "How did you implement anomaly detection?"
> *"I implemented a dual-metric statistical filter using NumPy and Pandas: computing normalized Z-scores across historical station baselines alongside a 24-hour moving average window. This separates natural diurnal traffic fluctuations from genuine industrial pollution events or sensor hardware failures, which the LLM then translates into plain English advisories."*
