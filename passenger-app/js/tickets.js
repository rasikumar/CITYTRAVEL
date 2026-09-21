import { apiRequest } from './api.js';

export const ticketsManager = {
  async loadBusesForTicket() {
    const busSelect = document.getElementById('ticketBusSelect');
    if (!busSelect) return;

    try {
      const buses = await apiRequest('/api/buses');
      busSelect.innerHTML = '<option value="">-- Choose a bus / line --</option>';
      buses.forEach(b => {
        const opt = document.createElement('option');
        opt.value = b.bus_id;
        opt.textContent = `${b.bus_id} - ${b.bus_name} (${b.route_name || 'Active Line'})`;
        busSelect.appendChild(opt);
      });
    } catch (err) {
      console.error('Failed to load buses for ticketing:', err);
    }
  },

  async purchaseTicket(formData) {
    return await apiRequest('/api/tickets', {
      method: 'POST',
      body: JSON.stringify(formData)
    });
  },

  async loadPassengerTickets() {
    const listContainer = document.getElementById('myTicketsList');
    if (!listContainer) return;

    try {
      const tickets = await apiRequest('/api/tickets');
      if (!tickets || tickets.length === 0) {
        listContainer.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">🎟️</div>
            <p>No active or past tickets found.</p>
          </div>
        `;
        return;
      }

      listContainer.innerHTML = tickets.map(t => `
        <div class="bus-card" style="border-left: 4px solid var(--primary);">
          <div class="bus-card-top">
            <span class="bus-id-badge">${t.ticket_number}</span>
            <span class="bus-status-badge status-active">${t.status}</span>
          </div>
          <div style="font-weight: 700; font-size: 1.05rem;">${t.bus_name}</div>
          <div style="font-size: 0.85rem; color: var(--text-muted);">${t.route_name}</div>
          <div class="bus-card-metrics">
            <div class="metric-item">
              <span class="metric-label">TYPE</span>
              <span class="metric-value">${t.ticket_type}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">FARE</span>
              <span class="metric-value">₹${t.fare.toFixed(2)}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">PAYMENT</span>
              <span class="metric-value">${t.payment_provider}</span>
            </div>
          </div>
          <div style="text-align: center; margin-top: 0.5rem; background: var(--bg-card-subtle); padding: 0.5rem; border-radius: 6px; font-family: monospace; font-size: 0.75rem;">
            VALID QR CODE PASS: ${t.ticket_number}
          </div>
        </div>
      `).join('');
    } catch (err) {
      console.error('Failed to load tickets:', err);
      listContainer.innerHTML = `<div class="empty-state">Could not load tickets.</div>`;
    }
  }
};
