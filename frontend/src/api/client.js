const API_BASE = '/api';

export async function sendChatMessage(message) {
  const response = await fetch(`${API_BASE}/chat/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
  if (!response.ok) {
    throw new Error(`Chat API error: ${response.statusText}`);
  }
  return await response.json();
}

export async function executeDirectSQL(sql) {
  const response = await fetch(`${API_BASE}/query/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sql, executed_by: 'ui_console' }),
  });
  if (!response.ok) {
    throw new Error(`Query API error: ${response.statusText}`);
  }
  return await response.json();
}

export async function fetchStations() {
  const response = await fetch(`${API_BASE}/sensors/stations`);
  if (!response.ok) throw new Error('Failed to fetch stations');
  return await response.json();
}

export async function fetchCitySummary() {
  const response = await fetch(`${API_BASE}/sensors/summary`);
  if (!response.ok) throw new Error('Failed to fetch city summary');
  return await response.json();
}

export async function fetchAnomalies(pollutant = 'pm25') {
  const response = await fetch(`${API_BASE}/anomalies/?pollutant=${pollutant}`);
  if (!response.ok) throw new Error('Failed to fetch anomalies');
  return await response.json();
}

export async function fetchAuditLogs(limit = 30) {
  const response = await fetch(`${API_BASE}/query/audit?limit=${limit}`);
  if (!response.ok) throw new Error('Failed to fetch audit logs');
  return await response.json();
}
