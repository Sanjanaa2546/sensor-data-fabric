import React, { useState } from 'react';
import { Table as TableIcon, Download, Search } from 'lucide-react';

export default function DataTable({ rows, columns }) {
  const [searchTerm, setSearchTerm] = useState('');

  if (!rows || rows.length === 0) {
    return (
      <div className="p-8 text-center text-slate-500 bg-slate-900/50 rounded-xl border border-slate-800">
        <TableIcon className="w-8 h-8 mx-auto mb-2 opacity-40" />
        <p className="text-sm">No tabular records available</p>
      </div>
    );
  }

  const cols = columns && columns.length > 0 ? columns : Object.keys(rows[0] || {});

  const filteredRows = rows.filter(r => {
    if (!searchTerm) return true;
    return Object.values(r).some(val => 
      String(val).toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  const exportCSV = () => {
    const header = cols.join(',');
    const csvRows = filteredRows.map(row => 
      cols.map(c => JSON.stringify(row[c] ?? '')).join(',')
    );
    const blob = new Blob([[header, ...csvRows].join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sensor_data_export_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-slate-900/90 rounded-xl border border-slate-800 overflow-hidden shadow-lg">
      {/* Table Toolbar */}
      <div className="p-3.5 border-b border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-950/40">
        <div className="flex items-center gap-2">
          <TableIcon className="w-4 h-4 text-sky-400" />
          <h3 className="text-sm font-bold text-slate-200">Query Result Table</h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
            {filteredRows.length} {filteredRows.length === 1 ? 'row' : 'rows'}
          </span>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-48">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
            <input 
              type="text" 
              placeholder="Search table..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-8 pr-2.5 py-1 text-xs rounded-md bg-slate-800/80 border border-slate-700 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
          </div>

          <button
            onClick={exportCSV}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            title="Export CSV"
          >
            <Download className="w-3.5 h-3.5 text-sky-400" />
            <span>CSV</span>
          </button>
        </div>
      </div>

      {/* Table Data */}
      <div className="overflow-x-auto max-h-80">
        <table className="w-full text-left text-xs font-sans">
          <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] tracking-wider sticky top-0 border-b border-slate-800">
            <tr>
              {cols.map(c => (
                <th key={c} className="py-2.5 px-3 font-semibold">
                  {c.replace(/_/g, ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
            {filteredRows.slice(0, 100).map((row, idx) => (
              <tr key={idx} className="hover:bg-slate-800/40 transition">
                {cols.map(c => {
                  const val = row[c];
                  const isAqi = c === 'aqi_category';
                  return (
                    <td key={c} className="py-2 px-3 whitespace-nowrap">
                      {isAqi ? (
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          val === 'Hazardous' || val === 'Very Unhealthy' ? 'bg-rose-950 text-rose-400 border border-rose-800' :
                          val === 'Unhealthy' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                          val === 'Moderate' ? 'bg-yellow-950 text-yellow-400 border border-yellow-800' :
                          'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        }`}>
                          {val}
                        </span>
                      ) : (
                        typeof val === 'number' ? val.toLocaleString() : (val ?? '—')
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {filteredRows.length > 100 && (
        <div className="p-2 text-center text-[11px] text-slate-500 bg-slate-950/50 border-t border-slate-800">
          Showing first 100 rows. Export CSV to view complete dataset.
        </div>
      )}
    </div>
  );
}
