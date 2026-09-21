// Leaflet Map Manager for Passenger App

export class TransitMap {
  constructor(elementId = 'map') {
    this.elementId = elementId;
    this.map = null;
    this.tileLayers = {};
    this.currentLayer = null;
    this.busMarkers = new Map(); // bus_id -> L.marker
    this.passengerMarker = null;
    this.passengerCoords = null;
    this.defaultCenter = [9.9252, 78.1198]; // Madurai Center
    this.defaultZoom = 13;
    this.activeRoutePolyline = null;
  }

  init() {
    if (this.map) return;

    // 1. Initialize Map
    this.map = L.map(this.elementId, {
      center: this.defaultCenter,
      zoom: this.defaultZoom,
      zoomControl: true
    });

    // 2. Define Tile Layers
    this.tileLayers = {
      osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap'
      }),
      satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 18,
        attribution: '&copy; Esri'
      }),
      dark: L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        attribution: '&copy; CARTO'
      })
    };

    // Default layer
    this.setTileLayer('osm');
  }

  setTileLayer(layerName) {
    if (!this.tileLayers[layerName]) return;

    if (this.currentLayer) {
      this.map.removeLayer(this.currentLayer);
    }
    this.currentLayer = this.tileLayers[layerName];
    this.currentLayer.addTo(this.map);
  }

  recenter() {
    if (this.passengerCoords) {
      this.map.setView(this.passengerCoords, 14, { animate: true });
    } else {
      this.map.setView(this.defaultCenter, this.defaultZoom, { animate: true });
    }
  }

  setPassengerLocation(lat, lon) {
    this.passengerCoords = [lat, lon];

    if (!this.passengerMarker) {
      const icon = L.divIcon({
        className: 'custom-passenger-marker',
        html: `<div class="marker-passenger-icon" title="You are here">👤</div>`,
        iconSize: [34, 34],
        iconAnchor: [17, 17]
      });

      this.passengerMarker = L.marker([lat, lon], { icon }).addTo(this.map);
      this.passengerMarker.bindPopup('<strong>👤 You are here</strong>');
    } else {
      this.passengerMarker.setLatLng([lat, lon]);
    }

    // Recalculate distances for existing bus markers
    this.busMarkers.forEach((markerData) => {
      this.updateBusPopup(markerData.busId, markerData.lastData);
    });
  }

  haversine(lat1, lon1, lat2, lon2) {
    const R = 6371; // km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  formatDistance(distKm) {
    if (distKm < 1.0) {
      return `${Math.round(distKm * 1000)} m away`;
    }
    return `${distKm.toFixed(1)} km away`;
  }

  updateBusMarker(busData) {
    const { bus_id, latitude, longitude } = busData;
    if (!latitude || !longitude) return;

    let markerEntry = this.busMarkers.get(bus_id);

    if (markerEntry) {
      // Smoothly update existing marker position
      markerEntry.marker.setLatLng([latitude, longitude]);
      markerEntry.lastData = busData;
      this.updateBusPopup(bus_id, busData);
    } else {
      // Create new marker with custom bus icon and bus_id label
      const icon = L.divIcon({
        className: 'custom-bus-marker',
        html: `
          <div class="marker-bus-icon">🚌</div>
          <div class="marker-bus-label">${bus_id}</div>
        `,
        iconSize: [40, 50],
        iconAnchor: [20, 45]
      });

      const marker = L.marker([latitude, longitude], { icon }).addTo(this.map);
      markerEntry = { marker, busId: bus_id, lastData: busData };
      this.busMarkers.set(bus_id, markerEntry);
      this.updateBusPopup(bus_id, busData);
    }
  }

  updateBusPopup(busId, data) {
    const markerEntry = this.busMarkers.get(busId);
    if (!markerEntry) return;

    let distText = 'Location unknown';
    if (this.passengerCoords && data.latitude && data.longitude) {
      const d = this.haversine(
        this.passengerCoords[0],
        this.passengerCoords[1],
        data.latitude,
        data.longitude
      );
      distText = this.formatDistance(d);
    }

    const popupHtml = `
      <div style="font-size: 0.85rem; line-height: 1.4; min-width: 170px;">
        <div style="font-weight: bold; color: #0284c7; font-size: 1rem; margin-bottom: 4px;">
          🚌 ${data.bus_id || busId}
        </div>
        <div><strong>Route:</strong> ${data.route_name || data.route_id || 'City Line'}</div>
        <div><strong>Speed:</strong> ${data.speed || data.current_speed || 0} km/h</div>
        <div><strong>Distance:</strong> ${distText}</div>
        <div><strong>Next Stop:</strong> ${data.next_stop || 'In Transit'}</div>
        <div><strong>ETA:</strong> ${data.eta || 'N/A'}</div>
        <div><strong>Trip Status:</strong> <span style="color: green; font-weight: 600;">${data.trip_status || data.status || 'ACTIVE'}</span></div>
        ${data.delay_reason ? `<div style="color: #dc2626; margin-top: 4px; font-weight: 600;">⚠️ Delay: ${data.delay_reason}</div>` : ''}
      </div>
    `;

    markerEntry.marker.bindPopup(popupHtml);
  }

  removeBusMarker(busId) {
    const markerEntry = this.busMarkers.get(busId);
    if (markerEntry) {
      this.map.removeLayer(markerEntry.marker);
      this.busMarkers.delete(busId);
    }
  }

  displayRoute(stops) {
    if (this.activeRoutePolyline) {
      this.map.removeLayer(this.activeRoutePolyline);
      this.activeRoutePolyline = null;
    }

    if (!stops || stops.length === 0) return;

    const latlngs = stops.map(s => [s.latitude, s.longitude]);
    this.activeRoutePolyline = L.polyline(latlngs, {
      color: '#0284c7',
      weight: 4,
      opacity: 0.8,
      dashArray: '4, 8'
    }).addTo(this.map);

    this.map.fitBounds(this.activeRoutePolyline.getBounds(), { padding: [30, 30] });
  }
}
