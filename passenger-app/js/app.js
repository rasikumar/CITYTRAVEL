import { apiRequest } from './api.js';
import { auth } from './auth.js';
import { TransitMap } from './map.js';
import { TransitWebSocket } from './websocket.js';
import { TransitAI } from './ai.js';

class PassengerApp {
  constructor() {
    this.map = new TransitMap('map');
    this.ws = null;
    this.ai = new TransitAI();
    this.allBuses = [];
    this.allRoutes = [];
    this.userCoords = null;
    this.activeRouteId = null;
  }

  async init() {
    // 1. Initialize Map
    this.map.init();

    // 2. Initialize AI Assistant
    this.ai.init();

    // 3. Setup WebSocket connection
    this.ws = new TransitWebSocket(
      this.map,
      (telemetry) => this.handleLiveTelemetry(telemetry),
      (delay) => this.handleLiveDelay(delay)
    );
    this.ws.connect();

    // 4. Setup Theme
    this.initTheme();

    // 5. Setup UI Event Listeners
    this.setupEventListeners();

    // 6. Load Initial Data
    await this.loadRoutes();
    await this.loadBuses();
    await this.loadTravelUpdates();
    this.updateUserSessionUI();
  }

  initTheme() {
    const savedTheme = localStorage.getItem('transitnow_theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    this.updateThemeButtonIcon(savedTheme);
  }

  toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('transitnow_theme', next);
    this.updateThemeButtonIcon(next);

    // If map is in dark mode or map mode, adjust tile layer if requested
    if (next === 'dark') {
      const activeBtn = document.querySelector('.map-btn.active');
      if (activeBtn && activeBtn.dataset.layer === 'dark') {
        this.map.setTileLayer('dark');
      }
    }
  }

  updateThemeButtonIcon(theme) {
    const btn = document.getElementById('themeToggleBtn');
    if (btn) {
      btn.textContent = theme === 'dark' ? '☀️' : '🌙';
      btn.title = theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme';
    }
  }

  setupEventListeners() {
    // Theme toggle
    const themeBtn = document.getElementById('themeToggleBtn');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => this.toggleTheme());
    }

    // Profile menu toggle
    const profileBtn = document.getElementById('profileMenuBtn');
    const profileDropdown = document.getElementById('profileDropdown');
    if (profileBtn && profileDropdown) {
      profileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        profileDropdown.classList.toggle('show');
      });
      document.addEventListener('click', () => {
        profileDropdown.classList.remove('show');
      });
    }

    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        auth.logout();
      });
    }

    // Search input
    const searchInput = document.getElementById('transitSearchInput');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const query = e.target.value;
        if (clearSearchBtn) {
          clearSearchBtn.style.display = query ? 'block' : 'none';
        }
        this.performSearch(query);
      });
    }

    if (clearSearchBtn) {
      clearSearchBtn.addEventListener('click', () => {
        searchInput.value = '';
        clearSearchBtn.style.display = 'none';
        this.renderBuses(this.allBuses);
      });
    }

    // Map Layer Controls
    const mapButtons = document.querySelectorAll('.map-btn[data-layer]');
    mapButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        mapButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.map.setTileLayer(btn.dataset.layer);
      });
    });

    // Recenter Control
    const recenterBtn = document.getElementById('recenterMapBtn');
    if (recenterBtn) {
      recenterBtn.addEventListener('click', () => {
        this.map.recenter();
      });
    }

    // Use My Location
    const userLocBtn = document.getElementById('useMyLocationBtn');
    if (userLocBtn) {
      userLocBtn.addEventListener('click', () => this.requestUserLocation());
    }
  }

  requestUserLocation() {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }

    const btn = document.getElementById('useMyLocationBtn');
    if (btn) btn.innerHTML = '⏳ Locating...';

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        this.userCoords = { latitude, longitude };
        this.map.setPassengerLocation(latitude, longitude);
        this.map.recenter();
        if (btn) btn.innerHTML = '📍 You are here';
        this.renderBuses(this.allBuses); // Re-render with updated distances
      },
      (err) => {
        console.warn('Geolocation failed or denied:', err);
        // Fallback default coordinate in central Madurai
        const defaultLat = 9.9252;
        const defaultLon = 78.1198;
        this.userCoords = { latitude: defaultLat, longitude: defaultLon };
        this.map.setPassengerLocation(defaultLat, defaultLon);
        if (btn) btn.innerHTML = '📍 Madurai (Default)';
        this.renderBuses(this.allBuses);
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }

  async loadRoutes() {
    try {
      this.allRoutes = await apiRequest('/api/routes');
      this.renderRouteFilters(this.allRoutes);
    } catch (err) {
      console.error('Failed to load routes:', err);
    }
  }

  renderRouteFilters(routes) {
    const container = document.getElementById('routeFiltersContainer');
    if (!container) return;

    let html = `<button class="filter-badge active" data-route-id="ALL">All Routes</button>`;
    routes.forEach(r => {
      html += `<button class="filter-badge" data-route-id="${r.route_id}">${r.route_id} - ${r.route_name}</button>`;
    });
    container.innerHTML = html;

    container.querySelectorAll('.filter-badge').forEach(badge => {
      badge.addEventListener('click', () => {
        container.querySelectorAll('.filter-badge').forEach(b => b.classList.remove('active'));
        badge.classList.add('active');
        const routeId = badge.dataset.routeId;
        this.filterByRoute(routeId);
      });
    });
  }

  filterByRoute(routeId) {
    if (routeId === 'ALL') {
      this.activeRouteId = null;
      this.map.displayRoute(null);
      this.renderBuses(this.allBuses);
    } else {
      this.activeRouteId = routeId;
      const selectedRoute = this.allRoutes.find(r => r.route_id === routeId);
      if (selectedRoute) {
        this.map.displayRoute(selectedRoute.stops);
      }
      const filtered = this.allBuses.filter(b => b.route_code === routeId || b.route_id === routeId);
      this.renderBuses(filtered);
    }
  }

  async loadBuses() {
    try {
      this.allBuses = await apiRequest('/api/buses');
      this.renderBuses(this.allBuses);

      // Plot initial bus markers on the Leaflet map
      this.allBuses.forEach(b => {
        if (b.current_latitude && b.current_longitude) {
          this.map.updateBusMarker(b);
        }
      });
    } catch (err) {
      console.error('Failed to load buses:', err);
      this.renderEmptyState('Failed to load live buses.');
    }
  }

  async performSearch(query) {
    const q = query.trim();
    if (!q) {
      this.renderBuses(this.allBuses);
      return;
    }

    try {
      const results = await apiRequest(`/api/buses/search?q=${encodeURIComponent(q)}`);
      this.renderBuses(results);
    } catch (err) {
      console.error('Search error:', err);
    }
  }

  renderBuses(buses) {
    const container = document.getElementById('busesListContainer');
    const countBadge = document.getElementById('busesCountBadge');
    if (!container) return;

    if (countBadge) {
      countBadge.textContent = `${buses.length} buses`;
    }

    if (!buses || buses.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">🚌</div>
          <p><strong>No buses or routes found.</strong></p>
          <p style="font-size: 0.8rem; margin-top: 4px;">Try searching for BUS001, 21G, or Mattuthavani.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = buses.map(bus => {
      let distanceText = 'Enable location';
      if (this.userCoords && bus.current_latitude && bus.current_longitude) {
        const d = this.map.haversine(
          this.userCoords.latitude,
          this.userCoords.longitude,
          bus.current_latitude,
          bus.current_longitude
        );
        distanceText = `Bus is ${this.map.formatDistance(d)}`;
      }

      const isActive = bus.status === 'ACTIVE';
      const statusClass = isActive ? 'status-active' : 'status-idle';

      return `
        <div class="bus-card" data-bus-id="${bus.bus_id}">
          <div class="bus-card-top">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span class="bus-id-badge">🚌 ${bus.bus_id}</span>
              <span class="bus-route-name">${bus.route_name || 'City Line'}</span>
            </div>
            <span class="bus-status-badge ${statusClass}">${bus.status}</span>
          </div>

          <div class="bus-card-metrics">
            <div class="metric-item">
              <span class="metric-label">NEXT STOP</span>
              <span class="metric-value">${bus.next_stop || 'In Transit'}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">ETA</span>
              <span class="metric-value" style="color: var(--primary);">${bus.eta || 'N/A'}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">SPEED</span>
              <span class="metric-value">${bus.current_speed || 0} km/h</span>
            </div>
          </div>

          ${bus.delay_reason ? `
            <div class="delay-tag">
              ⚠️ Delayed: ${bus.delay_reason}
            </div>
          ` : ''}

          <div class="bus-card-footer">
            <span style="font-size: 0.8rem; color: var(--text-muted);">
              📍 ${distanceText}
            </span>
            <a href="/passenger/tickets?bus_id=${bus.bus_id}" class="btn-ticket">Buy Ticket</a>
          </div>
        </div>
      `;
    }).join('');

    // Attach click events on bus cards to center map
    container.querySelectorAll('.bus-card').forEach(card => {
      card.addEventListener('click', (e) => {
        if (e.target.closest('.btn-ticket')) return; // Allow ticket button click
        const busId = card.dataset.busId;
        const bus = buses.find(b => b.bus_id === busId);
        if (bus && bus.current_latitude && bus.current_longitude) {
          this.map.map.setView([bus.current_latitude, bus.current_longitude], 15, { animate: true });
          const marker = this.map.busMarkers.get(busId);
          if (marker) marker.marker.openPopup();
        }
      });
    });
  }

  renderEmptyState(msg) {
    const container = document.getElementById('busesListContainer');
    if (container) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">⚠️</div>
          <p>${msg}</p>
        </div>
      `;
    }
  }

  async loadTravelUpdates() {
    const container = document.getElementById('travelUpdatesContainer');
    if (!container) return;

    try {
      const updates = await apiRequest('/api/travel-updates');
      if (!updates || updates.length === 0) {
        container.innerHTML = `<div style="font-size: 0.85rem; color: var(--text-muted);">No transit advisories today.</div>`;
        return;
      }

      container.innerHTML = updates.map(u => `
        <div class="update-card">
          <div class="update-header">
            <span class="update-category">${u.category}</span>
            <span class="update-date">${u.published_at}</span>
          </div>
          <div class="update-title">${u.title}</div>
          <div class="update-summary">${u.summary}</div>
        </div>
      `).join('');
    } catch (err) {
      console.warn('Failed to load travel updates:', err);
    }
  }

  handleLiveTelemetry(telemetry) {
    // Update local bus data
    const idx = this.allBuses.findIndex(b => b.bus_id === telemetry.bus_id);
    if (idx !== -1) {
      this.allBuses[idx].current_latitude = telemetry.latitude;
      this.allBuses[idx].current_longitude = telemetry.longitude;
      this.allBuses[idx].current_speed = telemetry.speed;
      this.allBuses[idx].next_stop = telemetry.next_stop;
      this.allBuses[idx].eta = telemetry.eta;
      this.allBuses[idx].status = telemetry.trip_status;
      if (telemetry.delay_reason) {
        this.allBuses[idx].delay_reason = telemetry.delay_reason;
      }
    } else {
      // New bus discovered live
      this.allBuses.push({
        bus_id: telemetry.bus_id,
        route_name: `Route ${telemetry.route_id}`,
        route_code: telemetry.route_id,
        current_latitude: telemetry.latitude,
        current_longitude: telemetry.longitude,
        current_speed: telemetry.speed,
        next_stop: telemetry.next_stop,
        eta: telemetry.eta,
        status: telemetry.trip_status,
        delay_reason: telemetry.delay_reason
      });
    }

    // Refresh bus cards matching active filters
    if (this.activeRouteId) {
      const filtered = this.allBuses.filter(b => b.route_code === this.activeRouteId || b.route_id === this.activeRouteId);
      this.renderBuses(filtered);
    } else {
      this.renderBuses(this.allBuses);
    }
  }

  handleLiveDelay(delay) {
    const idx = this.allBuses.findIndex(b => b.bus_id === delay.bus_id);
    if (idx !== -1) {
      this.allBuses[idx].delay_reason = delay.reason;
      this.renderBuses(this.allBuses);
    }
  }

  updateUserSessionUI() {
    const user = auth.getUser();
    const profileName = document.getElementById('profileUserName');
    if (profileName && user) {
      profileName.textContent = user.full_name || 'Passenger';
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const app = new PassengerApp();
  app.init();
});
