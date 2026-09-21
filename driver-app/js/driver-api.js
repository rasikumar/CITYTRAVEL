// Driver Application Dedicated API Client
export async function driverApiRequest(endpoint, options = {}) {
  const token = localStorage.getItem('transitnow_driver_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(options.headers || {})
  };

  const config = {
    ...options,
    headers
  };

  try {
    const res = await fetch(endpoint, config);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || data.message || `Request failed (${res.status})`);
    }
    return data;
  } catch (err) {
    console.error(`Driver API Error [${endpoint}]:`, err);
    throw err;
  }
}
