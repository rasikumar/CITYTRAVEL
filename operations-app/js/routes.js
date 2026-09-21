import { opsApiRequest } from './operations-api.js';
import { NominatimGeocode } from './nominatim.js';

export const routesOps = {
  // 1. List Routes
  async loadRoutes() {
    const tbody = document.getElementById('routesTableBody');
    if (!tbody) return;

    try {
      const routes = await opsApiRequest('/api/operations/routes');
      if (!routes || routes.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--ops-text-muted);">No transit routes created yet.</td></tr>`;
        return;
      }

      tbody.innerHTML = routes.map(r => `
        <tr>
          <td><strong style="color: var(--ops-primary);">${r.route_id}</strong></td>
          <td>${r.route_name}</td>
          <td>${r.direction}</td>
          <td>${r.stops_count} stops</td>
          <td>${r.buses_count} buses</td>
          <td>
            <a href="/operations/route-edit?id=${r.id}" class="btn-action-sm">Edit / Stops</a>
            <button class="btn-action-sm btn-action-del" data-del-route="${r.id}" data-del-code="${r.route_id}">Delete</button>
          </td>
        </tr>
      `).join('');

      tbody.querySelectorAll('[data-del-route]').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.dataset.delRoute;
          const code = btn.dataset.delCode;
          if (confirm(`Are you sure you want to delete Route ${code}?`)) {
            try {
              await opsApiRequest(`/api/operations/routes/${id}`, { method: 'DELETE' });
              await this.loadRoutes();
            } catch (err) {
              alert(err.message || 'Failed to delete route.');
            }
          }
        });
      });
    } catch (err) {
      console.error('Failed to load routes:', err);
    }
  },

  // 2. Setup Stop Nominatim Location Search
  bindNominatimInput(locationInput, resultsDropdown, latInput, lonInput) {
    let debounceTimer = null;

    locationInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      const query = locationInput.value.trim();
      if (query.length < 3) {
        resultsDropdown.style.display = 'none';
        return;
      }

      debounceTimer = setTimeout(async () => {
        resultsDropdown.innerHTML = `<div class="nominatim-item" style="color: var(--ops-text-muted);">Searching OpenStreetMap Nominatim...</div>`;
        resultsDropdown.style.display = 'block';

        const results = await NominatimGeocode.search(query);
        if (!results || results.length === 0) {
          resultsDropdown.innerHTML = `<div class="nominatim-item" style="color: var(--ops-text-muted);">No matching places found.</div>`;
          return;
        }

        resultsDropdown.innerHTML = results.map((item, idx) => `
          <div class="nominatim-item" data-idx="${idx}">
            📍 ${item.display_name}
          </div>
        `).join('');

        resultsDropdown.querySelectorAll('.nominatim-item[data-idx]').forEach(itemEl => {
          itemEl.addEventListener('click', () => {
            const idx = itemEl.dataset.idx;
            const chosen = results[idx];
            locationInput.value = chosen.display_name.split(',')[0];
            latInput.value = chosen.latitude.toFixed(6);
            lonInput.value = chosen.longitude.toFixed(6);
            resultsDropdown.style.display = 'none';
          });
        });
      }, 400);
    });

    document.addEventListener('click', (e) => {
      if (!locationInput.contains(e.target) && !resultsDropdown.contains(e.target)) {
        resultsDropdown.style.display = 'none';
      }
    });
  }
};
