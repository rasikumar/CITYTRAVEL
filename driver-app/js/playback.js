import { driverApiRequest } from './driver-api.js';

export class RoutePlaybackSimulator {
  constructor(context, stops, onPointSent, onStatusUpdate) {
    this.context = context; // { driver_id, bus_id, trip_id, route_id }
    this.stops = stops || [];
    this.onPointSent = onPointSent;
    this.onStatusUpdate = onStatusUpdate;
    this.isRunning = false;
    this.timer = null;
    this.currentStopIndex = 0;
    this.direction = 1; // 1 = forward (Stop 1 -> 4), -1 = reverse (Stop 4 -> 1)
    this.isWaitingAtTerminal = false;
    this.waitRemainingSeconds = 0;
  }

  start() {
    if (!this.stops || this.stops.length === 0) {
      if (this.onStatusUpdate) this.onStatusUpdate('No route stops available for playback.');
      return;
    }

    this.isRunning = true;
    this.currentStopIndex = 0;
    this.direction = 1;
    this.isWaitingAtTerminal = false;

    if (this.onStatusUpdate) {
      this.onStatusUpdate('ROUTE PLAYBACK ACTIVE');
    }

    this.step();
  }

  stop() {
    this.isRunning = false;
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    if (this.onStatusUpdate) {
      this.onStatusUpdate('ROUTE PLAYBACK STOPPED');
    }
  }

  async step() {
    if (!this.isRunning) return;

    // Check if we are in terminal wait state (10 minutes turnaround)
    if (this.isWaitingAtTerminal) {
      if (this.waitRemainingSeconds > 0) {
        if (this.onStatusUpdate) {
          const mins = Math.floor(this.waitRemainingSeconds / 60);
          const secs = this.waitRemainingSeconds % 60;
          this.onStatusUpdate(`ROUTE PLAYBACK (Waiting 10 min at terminal: ${mins}m ${secs}s)`);
        }
        this.waitRemainingSeconds -= 5;
        this.timer = setTimeout(() => this.step(), 5000);
        return;
      } else {
        // Wait finished, switch direction
        this.isWaitingAtTerminal = false;
        this.direction = -this.direction;
        this.currentStopIndex += this.direction;
      }
    }

    const currentStop = this.stops[this.currentStopIndex];
    if (!currentStop) return;

    // Send telemetry point for current stop
    const payload = {
      driver_id: this.context.driver_id,
      bus_id: this.context.bus_id,
      trip_id: this.context.trip_id,
      route_id: this.context.route_id,
      latitude: parseFloat(currentStop.latitude.toFixed(6)),
      longitude: parseFloat(currentStop.longitude.toFixed(6)),
      speed: 30.0,
      accuracy: 5.0,
      timestamp: new Date().toISOString(),
      source: 'route_playback'
    };

    try {
      const res = await driverApiRequest('/api/driver/telemetry', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      if (this.onPointSent) {
        this.onPointSent(payload, res);
      }
    } catch (err) {
      console.warn('[Playback] Telemetry transmission error:', err);
    }

    // Determine next stop
    const nextIndex = this.currentStopIndex + this.direction;

    if (nextIndex >= this.stops.length) {
      // Reached final stop (Stop 4), start 10 minutes wait before turnaround
      this.isWaitingAtTerminal = true;
      this.waitRemainingSeconds = 600; // 10 minutes (600s)
      if (this.onStatusUpdate) {
        this.onStatusUpdate('ROUTE PLAYBACK: Reached endpoint. Terminal wait (10 mins)...');
      }
      this.timer = setTimeout(() => this.step(), 4000);
    } else if (nextIndex < 0) {
      // Reached origin stop (Stop 1) in reverse, start 10 minutes wait before heading out again
      this.isWaitingAtTerminal = true;
      this.waitRemainingSeconds = 600; // 10 minutes
      if (this.onStatusUpdate) {
        this.onStatusUpdate('ROUTE PLAYBACK: Returned to origin. Terminal wait (10 mins)...');
      }
      this.timer = setTimeout(() => this.step(), 4000);
    } else {
      // Move to intermediate stop in 4 seconds
      this.currentStopIndex = nextIndex;
      this.timer = setTimeout(() => this.step(), 4000);
    }
  }
}
