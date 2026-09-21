import { opsApiRequest } from './operations-api.js';

export const driversOps = {
  async loadDrivers() {
    const tbody = document.getElementById('driversTableBody');
    if (!tbody) return;

    try {
      const drivers = await opsApiRequest('/api/operations/drivers');
      if (!drivers || drivers.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--ops-text-muted);">No drivers registered.</td></tr>`;
        return;
      }

      tbody.innerHTML = drivers.map(d => `
        <tr>
          <td><strong style="color: var(--ops-primary);">${d.driver_id}</strong></td>
          <td>${d.driver_name}</td>
          <td>${d.phone}</td>
          <td>${d.shift_start} - ${d.shift_end}</td>
          <td>${d.lunch_start} - ${d.lunch_end}</td>
          <td>
            <button class="btn-action-sm" data-edit-driver="${d.id}" data-json='${JSON.stringify(d)}'>Edit</button>
            <button class="btn-action-sm btn-action-del" data-del-driver="${d.id}" data-code="${d.driver_id}">Delete</button>
          </td>
        </tr>
      `).join('');

      tbody.querySelectorAll('[data-del-driver]').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.dataset.delDriver;
          const code = btn.dataset.code;
          if (confirm(`Are you sure you want to delete Driver ${code}? Any assigned bus will be safely unassigned.`)) {
            try {
              await opsApiRequest(`/api/operations/drivers/${id}`, { method: 'DELETE' });
              await this.loadDrivers();
            } catch (err) {
              alert(err.message || 'Failed to delete driver.');
            }
          }
        });
      });

      tbody.querySelectorAll('[data-edit-driver]').forEach(btn => {
        btn.addEventListener('click', () => {
          const d = JSON.parse(btn.dataset.json);
          this.openEditModal(d);
        });
      });
    } catch (err) {
      console.error('Failed to load drivers:', err);
    }
  },

  openEditModal(d) {
    document.getElementById('editDriverIdInput').value = d.id;
    document.getElementById('editDriverCode').value = d.driver_id;
    document.getElementById('editDriverName').value = d.driver_name;
    document.getElementById('editDriverPhone').value = d.phone;
    document.getElementById('editShiftStart').value = d.shift_start || '08:00';
    document.getElementById('editShiftEnd').value = d.shift_end || '16:00';
    document.getElementById('editLunchStart').value = d.lunch_start || '12:30';
    document.getElementById('editLunchEnd').value = d.lunch_end || '13:00';
    document.getElementById('editDriverModal').style.display = 'flex';
  },

  async handleCreateDriver(formData) {
    return await opsApiRequest('/api/operations/drivers', {
      method: 'POST',
      body: JSON.stringify(formData)
    });
  },

  async handleUpdateDriver(id, formData) {
    return await opsApiRequest(`/api/operations/drivers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(formData)
    });
  }
};
