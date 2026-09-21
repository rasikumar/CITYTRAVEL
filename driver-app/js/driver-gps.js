import { driverApiRequest } from './driver-api.js';

export class DriverGPSTracker {
  constructor(context, onTelemetrySent, onError) {
    this.context = context; // { driver_id, bus_id, trip_id, route_id }
    this.onTelemetrySent = onTelemetrySent;
    this.onError = onError;
    this.watchId = null;
    this.isTracking = false;
    this.hasSentFirstCoordinate = false;
    this.lastSentTimestamp = 0;
  }

  async startTracking() {
    if (!navigator.geolocation) {
      if (this.onError) this.onError('Browser does not support geolocation.');
      return false;
    }

    this.isTracking = true;
    this.hasSentFirstCoordinate = false;

    // 1. Immediately request first position
    navigator.geolocation.getCurrentPosition(
      (pos) => this.handlePosition(pos, true),
      (err) => {
        console.warn('Initial GPS position failed, falling back to watchPosition:', err);
        if (this.onError) this.onError(err.message || 'GPS Signal Acquiring...');
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
    );

    // 2. Start continuous watchPosition
    this.watchId = navigator.geolocation.watchPosition(
      (pos) => this.handlePosition(pos, false),
      (err) => {
        console.warn('watchPosition error:', err);
        if (this.onError) this.onError(err.message || 'Poor GPS reception');
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 1000 }
    );

    return true;
  }

  stopTracking() {
    this.isTracking = false;
    if (this.watchId !== null) {
      navigator.geolocation.clearWatch(this.watchId);
      this.watchId = null;
    }
  }

  async handlePosition(position, isFirst = false) {
    if (!this.isTracking) return;

    const now = Date.now();
    // Throttle to maximum 1 update every 2 seconds unless it's the very first coordinate
    if (!isFirst && now - this.lastSentTimestamp < 2000) {
      return;
    }

    const { latitude, longitude, speed, accuracy } = position.coords;
    const speedKmh = speed !== null && speed >= 0 ? Math.round(speed * 3.6) : 0;

    const payload = {
      driver_id: this.context.driver_id,
      bus_id: this.context.bus_id,
      trip_id: this.context.trip_id,
      route_id: this.context.route_id,
      latitude: parseFloat(latitude.toFixed(6)),
      longitude: parseFloat(longitude.toFixed(6)),
      speed: speedKmh,
      accuracy: Math.round(accuracy || 10),
      timestamp: new Date().toISOString(),
      source: 'phone_gps'
    };

    try {
      this.lastSentTimestamp = now;
      this.hasSentFirstCoordinate = true;
      const res = await driverApiRequest('/api/driver/telemetry', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      if (this.onTelemetrySent) {
        this.onTelemetrySent(payload, res);
      }
    } catch (err) {
      console.error('Failed to transmit GPS telemetry:', err);
      if (this.onError) {
        this.onError('Network transmission error');
      }
    }
  }
}
