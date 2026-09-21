import { opsApiRequest } from './operations-api.js';

export const tripsOps = {
  async loadDashboardOverview() {
    try {
      const [routes, buses, drivers, trips] = await Promise.all([
        opsApiRequest('/api/operations/routes').catch(() => []),
        opsApiRequest('/api/operations/buses').catch(() => []),
        opsApiRequest('/api/operations/drivers').catch(() => []),
        opsApiRequest('/api/operations/trips').catch(() => [])
      ]);

      const activeTrips = trips.filter(t => t.status === 'ACTIVE');
      const activeDelays = trips.filter(t => t.delays && t.delays.length > 0);

      const rCount = document.getElementById('kpiRoutes');
      const bCount = document.getElementById('kpiBuses');
      const dCount = document.getElementById('kpiDrivers');
      const tCount = document.getElementById('kpiActiveTrips');
      const delayCount = document.getElementById('kpiDelays');

      if (rCount) rCount.textContent = routes.length;
      if (bCount) bCount.textContent = buses.length;
      if (dCount) dCount.textContent = drivers.length;
      if (tCount) tCount.textContent = activeTrips.length;
      if (delayCount) delayCount.textContent = activeDelays.length;

      // Render Active Trips Compact Table
      const tripsBody = document.getElementById('dashboardTripsBody');
      if (tripsBody) {
        if (trips.length === 0) {
          tripsBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--ops-text-muted);">No transit trips recorded yet.</td></tr>`;
        } else {
          tripsBody.innerHTML = trips.slice(0, 10).map(t => `
            <tr>
              <td><strong style="color: var(--ops-primary);">${t.trip_id}</strong></td>
              <td>${t.bus_id} (${t.bus_name})</td>
              <td>${t.driver_name}</td>
              <td>${t.route_name}</td>
              <td><span style="color: ${t.status === 'ACTIVE' ? '#4ade80' : '#94a3b8'}; font-weight: 700;">${t.status}</span></td>
              <td>${t.delays.length > 0 ? `<span style="color: #f87171; font-weight: 600;">⚠️ ${t.delays.join(', ')}</span>` : '<span style="color: #4ade80;">On Schedule</span>'}</td>
            </tr>
          `).join('');
        }
      }
    } catch (err) {
      console.error('Failed to load dashboard overview:', err);
    }
  },

  async loadTripsMonitor() {
    const tripsBody = document.getElementById('tripsMonitorTableBody');
    const telemBody = document.getElementById('telemetryTableBody');

    try {
      const [trips, telemetry] = await Promise.all([
        opsApiRequest('/api/operations/trips'),
        opsApiRequest('/api/operations/telemetry')
      ]);

      if (tripsBody) {
        tripsBody.innerHTML = trips.map(t => `
          <tr>
            <td><strong>${t.trip_id}</strong></td>
            <td>${t.bus_id}</td>
            <td>${t.driver_name}</td>
            <td>${t.route_name}</td>
            <td>${t.start_time}</td>
            <td><span style="color: ${t.status === 'ACTIVE' ? '#4ade80' : '#94a3b8'}; font-weight: 700;">${t.status}</span></td>
            <td>${t.delays.join(', ') || 'None'}</td>
          </tr>
        `).join('');
      }

      if (telemBody) {
        telemBody.innerHTML = telemetry.map(tr => `
          <tr>
            <td>${tr.timestamp}</td>
            <td><strong>${tr.bus_id}</strong></td>
            <td>${tr.latitude.toFixed(5)}, ${tr.longitude.toFixed(5)}</td>
            <td>${tr.speed} km/h</td>
            <td>${tr.accuracy} m</td>
            <td><span style="font-size: 0.75rem; background: var(--ops-surface-card); padding: 2px 6px; border-radius: 4px;">${tr.source}</span></td>
          </tr>
        `).join('');
      }
    } catch (err) {
      console.error('Failed to load trips monitor:', err);
    }
  }
};
