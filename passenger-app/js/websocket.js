// Real-time WebSocket Client for Passenger Tracking

export class TransitWebSocket {
  constructor(mapManager, onTelemetryCallback, onDelayCallback) {
    this.map = mapManager;
    this.onTelemetry = onTelemetryCallback;
    this.onDelay = onDelayCallback;
    this.socket = null;
    this.reconnectTimer = null;
    this.selectedStop = null;
    this.selectedBusId = null;
  }

  setSelectedAlertTarget(busId, stop) {
    this.selectedBusId = busId;
    this.selectedStop = stop;
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/transit`;

    console.log(`[WebSocket] Connecting to ${wsUrl}...`);
    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log('[WebSocket] Connected to TransitNow real-time feed');
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (err) {
        console.error('[WebSocket] Malformed message:', err);
      }
    };

    this.socket.onerror = (err) => {
      console.warn('[WebSocket] Connection error:', err);
    };

    this.socket.onclose = () => {
      console.log('[WebSocket] Connection closed. Retrying in 3s...');
      this.reconnectTimer = setTimeout(() => this.connect(), 3000);
    };
  }

  handleMessage(msg) {
    if (msg.type === 'telemetry') {
      // 1. Update map bus marker smoothly
      this.map.updateBusMarker(msg);

      // 2. Trigger UI callback for card updates
      if (this.onTelemetry) {
        this.onTelemetry(msg);
      }

      // 3. Check selected stop proximity for arrival notifications
      if (this.selectedBusId && msg.bus_id === this.selectedBusId && this.selectedStop) {
        this.checkStopProximity(msg);
      }
    } else if (msg.type === 'delay') {
      if (this.onDelay) {
        this.onDelay(msg);
      }
    } else if (msg.type === 'trip_ended') {
      console.log(`[WebSocket] Trip ended for bus ${msg.bus_id}`);
      this.map.removeBusMarker(msg.bus_id);
      if (this.onTelemetry) {
        this.onTelemetry({ bus_id: msg.bus_id, status: 'ENDED', trip_status: 'ENDED' });
      }
    }
  }

  checkStopProximity(busTelemetry) {
    if (!this.selectedStop) return;
    const d = this.map.haversine(
      busTelemetry.latitude,
      busTelemetry.longitude,
      this.selectedStop.latitude,
      this.selectedStop.longitude
    );

    const banner = document.getElementById('arrivalBanner');
    if (!banner) return;

    if (d <= 0.05) {
      // Reached
      banner.className = 'arrival-banner reached';
      banner.style.display = 'block';
      banner.innerHTML = `🎉 <strong>Your bus has reached your stop (${this.selectedStop.stop_name})!</strong>`;
    } else if (d <= 0.5) {
      // Approaching
      banner.className = 'arrival-banner';
      banner.style.display = 'block';
      banner.innerHTML = `🔔 <strong>Your bus is approaching your stop (${this.selectedStop.stop_name})</strong> — ${Math.round(d * 1000)} meters away.`;
    }
  }
}
