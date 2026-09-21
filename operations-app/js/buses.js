import { opsApiRequest } from './operations-api.js';

export const busesOps = {
  async loadBuses() {
    const tbody = document.getElementById('busesTableBody');
    if (!tbody) return;

    try {
      const buses = await opsApiRequest('/api/operations/buses');
      if (!buses || buses.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--ops-text-muted);">No buses in fleet yet.</td></tr>`;
        return;
      }

      tbody.innerHTML = buses.map(b => `
        <tr>
          <td><strong style="color: var(--ops-primary);">${b.bus_id}</strong></td>
          <td>${b.bus_name}</td>
          <td><span style="font-family: monospace;">${b.registration_number}</span></td>
          <td>${b.capacity} seats</td>
          <td>${b.driver_name}</td>
          <td>${b.route_name}</td>
          <td>
            <button class="btn-action-sm" data-edit-bus="${b.id}" data-json='${JSON.stringify(b)}'>Edit</button>
            <button class="btn-action-sm btn-action-del" data-del-bus="${b.id}" data-code="${b.bus_id}">Delete</button>
          </td>
        </tr>
      `).join('');

      tbody.querySelectorAll('[data-del-bus]').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.dataset.delBus;
          const code = btn.dataset.code;
          if (confirm(`Are you sure you want to delete Bus ${code}? Any active trips will be safely terminated.`)) {
            try {
              await opsApiRequest(`/api/operations/buses/${id}`, { method: 'DELETE' });
              await this.loadBuses();
            } catch (err) {
              alert(err.message || 'Failed to delete bus.');
            }
          }
        });
      });

      tbody.querySelectorAll('[data-edit-bus]').forEach(btn => {
        btn.addEventListener('click', () => {
          const b = JSON.parse(btn.dataset.json);
          this.openEditModal(b);
        });
      });
    } catch (err) {
      console.error('Failed to load buses:', err);
    }
  },

  async populateSelectors(driverSelectId, routeSelectId) {
    const dSelect = document.getElementById(driverSelectId);
    const rSelect = document.getElementById(routeSelectId);

    if (dSelect) {
      try {
        const drivers = await opsApiRequest('/api/operations/drivers');
        dSelect.innerHTML = '<option value="">-- Select Driver --</option>';
        drivers.forEach(d => {
          dSelect.innerHTML += `<option value="${d.id}">${d.driver_id} - ${d.driver_name}</option>`;
        });
      } catch (err) {
        console.warn('Could not populate drivers dropdown:', err);
      }
    }

    if (rSelect) {
      try {
        const routes = await opsApiRequest('/api/operations/routes');
        rSelect.innerHTML = '<option value="">-- Select Route --</option>';
        routes.forEach(r => {
          rSelect.innerHTML += `<option value="${r.id}">${r.route_id} - ${r.route_name}</option>`;
        });
      } catch (err) {
        console.warn('Could not populate routes dropdown:', err);
      }
    }
  },

  openEditModal(b) {
    document.getElementById('editBusIdInput').value = b.id;
    document.getElementById('editBusCode').value = b.bus_id;
    document.getElementById('editBusName').value = b.bus_name;
    document.getElementById('editBusReg').value = b.registration_number;
    document.getElementById('editBusCapacity').value = b.capacity || 50;
    
    const dSelect = document.getElementById('editBusDriverSelect');
    const rSelect = document.getElementById('editBusRouteSelect');
    if (dSelect) dSelect.value = b.driver_id || '';
    if (rSelect) rSelect.value = b.route_id || '';

    document.getElementById('editBusModal').style.display = 'flex';
  },

  async handleCreateBus(formData) {
    return await opsApiRequest('/api/operations/buses', {
      method: 'POST',
      body: JSON.stringify(formData)
    });
  },

  async handleUpdateBus(id, formData) {
    return await opsApiRequest(`/api/operations/buses/${id}`, {
      method: 'PUT',
      body: JSON.stringify(formData)
    });
  }
};
