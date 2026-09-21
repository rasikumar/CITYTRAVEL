import { driverApiRequest } from './driver-api.js';
import { driverAuth } from './driver-auth.js';
import { DriverGPSTracker } from './driver-gps.js';
import { RoutePlaybackSimulator } from './playback.js';

export class DriverTripController {
  constructor() {
    this.profile = null;
    this.activeTrip = null;
    this.gpsTracker = null;
    this.playbackSim = null;
    this.isUsingPlayback = false;
  }

  async initDashboard() {
    if (!driverAuth.isAuthenticated()) {
      window.location.href = '/driver-app/login';
      return;
    }

    try {
      this.profile = await driverAuth.fetchProfile();
      this.renderDashboard(this.profile);
    } catch (err) {
      console.error('Failed to load driver dashboard:', err);
      alert('Could not load assigned vehicle data. Please re-login.');
      driverAuth.logout();
    }
  }

  renderDashboard(data) {
    const { driver, assigned_bus, assigned_route, active_trip } = data;

    // Driver details
    const nameEl = document.getElementById('driverName');
    const idEl = document.getElementById('driverId');
    const phoneEl = document.getElementById('driverPhone');
    const shiftEl = document.getElementById('driverShift');
    const lunchEl = document.getElementById('driverLunch');

    if (nameEl) nameEl.textContent = driver.driver_name;
    if (idEl) idEl.textContent = driver.driver_id;
    if (phoneEl) phoneEl.textContent = driver.phone;
    if (shiftEl) shiftEl.textContent = `${driver.shift_start} - ${driver.shift_end}`;
    if (lunchEl) lunchEl.textContent = `${driver.lunch_start} - ${driver.lunch_end}`;

    // Assigned Bus (ONLY assigned bus)
    const busEl = document.getElementById('assignedBus');
    const regEl = document.getElementById('assignedBusReg');
    if (assigned_bus) {
      if (busEl) busEl.textContent = `${assigned_bus.bus_id} (${assigned_bus.bus_name})`;
      if (regEl) regEl.textContent = assigned_bus.registration_number;
    } else {
      if (busEl) busEl.textContent = 'No bus assigned';
    }

    // Assigned Route (ONLY assigned route)
    const routeEl = document.getElementById('assignedRoute');
    if (assigned_route) {
      if (routeEl) routeEl.textContent = `${assigned_route.route_id} - ${assigned_route.route_name}`;
    } else {
      if (routeEl) routeEl.textContent = 'No route assigned';
    }

    // Start Trip button handler
    const startBtn = document.getElementById('startTripBtn');
    if (startBtn) {
      startBtn.addEventListener('click', () => this.startTripAction());
    }

    // If trip is already active, direct to trip cockpit
    if (active_trip) {
      localStorage.setItem('transitnow_active_trip', JSON.stringify(active_trip));
    }
  }

  async startTripAction() {
    if (!this.profile.assigned_bus) {
      alert('Cannot start trip: No bus assigned to your driver ID.');
      return;
    }
    if (!this.profile.assigned_route) {
      alert('Cannot start trip: No route assigned to your bus.');
      return;
    }

    const startBtn = document.getElementById('startTripBtn');
    if (startBtn) {
      startBtn.disabled = true;
      startBtn.textContent = 'Validating and starting trip...';
    }

    try {
      const res = await driverApiRequest('/api/driver/trips/start', {
        method: 'POST',
        body: JSON.stringify({
          driver_id: this.profile.driver.driver_id,
          bus_id: this.profile.assigned_bus.bus_id,
          route_id: this.profile.assigned_route.route_id
        })
      });

      localStorage.setItem('transitnow_active_trip', JSON.stringify(res));
      window.location.href = '/driver-app/trip';
    } catch (err) {
      alert(err.message || 'Failed to start trip.');
      if (startBtn) {
        startBtn.disabled = false;
        startBtn.textContent = 'START TRIP';
      }
    }
  }

  async initTripCockpit() {
    if (!driverAuth.isAuthenticated()) {
      window.location.href = '/driver-app/login';
      return;
    }

    try {
      this.profile = await driverAuth.fetchProfile();
      const storedTrip = localStorage.getItem('transitnow_active_trip');
      this.activeTrip = storedTrip ? JSON.parse(storedTrip) : this.profile.active_trip;

      if (!this.activeTrip) {
        alert('No active trip found. Redirecting to dashboard...');
        window.location.href = '/driver-app';
        return;
      }

      this.setupTripCockpitUI();
      this.startTelemetryTransmission();
    } catch (err) {
      console.error('Trip init error:', err);
      alert('Error initializing trip cockpit.');
    }
  }

  setupTripCockpitUI() {
    // Header labels
    document.getElementById('cockpitBusId').textContent = this.profile.assigned_bus.bus_id;
    document.getElementById('cockpitRoute').textContent = this.profile.assigned_route.route_name;
    document.getElementById('cockpitTripId').textContent = this.activeTrip.trip_id;

    // Buttons
    document.getElementById('endTripBtn').addEventListener('click', () => this.endTripAction());
    document.getElementById('reportDelayBtn').addEventListener('click', () => this.openDelayModal());
    document.getElementById('closeDelayModalBtn').addEventListener('click', () => this.closeDelayModal());
    document.getElementById('playbackFallbackBtn').addEventListener('click', () => this.toggleRoutePlayback());

    // Delay Option Clicks
    document.querySelectorAll('.delay-option-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const reason = btn.dataset.reason;
        this.submitDelay(reason);
      });
    });
  }

  startTelemetryTransmission() {
    const context = {
      driver_id: this.profile.driver.driver_id,
      bus_id: this.profile.assigned_bus.bus_id,
      trip_id: this.activeTrip.trip_id,
      route_id: this.profile.assigned_route.route_id
    };

    // Instantiate GPS Tracker
    this.gpsTracker = new DriverGPSTracker(
      context,
      (sent, backendRes) => this.updateCockpitTelemetry(sent, backendRes),
      (errMsg) => this.handleGPSError(errMsg)
    );

    this.gpsTracker.startTracking();
  }

  updateCockpitTelemetry(sent, backendRes) {
    const dot = document.getElementById('gpsStatusDot');
    const label = document.getElementById('gpsStatusLabel');
    if (dot) dot.className = 'gps-dot';
    if (label) label.textContent = this.isUsingPlayback ? 'ROUTE PLAYBACK' : 'Connected (Live GPS)';

    document.getElementById('cockpitSpeed').textContent = sent.speed || 0;
    document.getElementById('cockpitAccuracy').textContent = `${sent.accuracy || 8} m`;
    document.getElementById('cockpitLat').textContent = sent.latitude.toFixed(5);
    document.getElementById('cockpitLon').textContent = sent.longitude.toFixed(5);

    if (backendRes) {
      if (backendRes.next_stop) {
        document.getElementById('cockpitNextStop').textContent = backendRes.next_stop;
      }
      if (backendRes.eta) {
        document.getElementById('cockpitEta').textContent = backendRes.eta;
      }
    }
  }

  handleGPSError(errMsg) {
    console.warn('GPS Signal Issue:', errMsg);
    const dot = document.getElementById('gpsStatusDot');
    const label = document.getElementById('gpsStatusLabel');
    if (dot) dot.className = 'gps-dot offline';
    if (label) label.textContent = 'GPS unavailable';

    const banner = document.getElementById('playbackBanner');
    if (banner) banner.style.display = 'flex';
  }

  toggleRoutePlayback() {
    if (this.gpsTracker) {
      this.gpsTracker.stopTracking();
    }

    this.isUsingPlayback = true;
    const context = {
      driver_id: this.profile.driver.driver_id,
      bus_id: this.profile.assigned_bus.bus_id,
      trip_id: this.activeTrip.trip_id,
      route_id: this.profile.assigned_route.route_id
    };

    const stops = this.profile.assigned_route.stops || [];
    this.playbackSim = new RoutePlaybackSimulator(
      context,
      stops,
      (sent, backendRes) => this.updateCockpitTelemetry(sent, backendRes),
      (statusMsg) => {
        const playbackStatusEl = document.getElementById('playbackStatusText');
        if (playbackStatusEl) playbackStatusEl.textContent = statusMsg;
      }
    );

    this.playbackSim.start();
  }

  openDelayModal() {
    document.getElementById('delayModal').classList.add('show');
  }

  closeDelayModal() {
    document.getElementById('delayModal').classList.remove('show');
  }

  async submitDelay(reason) {
    try {
      await driverApiRequest('/api/driver/delay', {
        method: 'POST',
        body: JSON.stringify({
          trip_id: this.activeTrip.trip_id,
          bus_id: this.profile.assigned_bus.bus_id,
          driver_id: this.profile.driver.driver_id,
          reason: reason,
          note: `Reported by driver ${this.profile.driver.driver_name}`
        })
      });

      this.closeDelayModal();
      alert(`Delay reported: "${reason}". Broadcasted to passenger live map.`);
    } catch (err) {
      alert(err.message || 'Failed to submit delay report.');
    }
  }

  async endTripAction() {
    const confirmEnd = confirm('Are you sure you want to end this active trip?');
    if (!confirmEnd) return;

    if (this.gpsTracker) this.gpsTracker.stopTracking();
    if (this.playbackSim) this.playbackSim.stop();

    try {
      await driverApiRequest('/api/driver/trips/end', {
        method: 'POST',
        body: JSON.stringify({ trip_id: this.activeTrip.trip_id })
      });

      localStorage.removeItem('transitnow_active_trip');
      alert('Trip ended successfully. Passenger tracking updated.');
      window.location.href = '/driver-app';
    } catch (err) {
      alert(err.message || 'Error ending trip.');
    }
  }
}
