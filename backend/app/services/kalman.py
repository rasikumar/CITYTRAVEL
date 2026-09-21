import time
from typing import Tuple, Optional, Dict
from app.services.distance import haversine_distance

class KalmanFilter1D:
    """
    One-dimensional Kalman filter for smoothing sensor readings (e.g. speed).
    """
    def __init__(self, process_variance: float = 1e-4, measurement_variance: float = 1e-2):
        self.q = process_variance
        self.r = measurement_variance
        self.x = 0.0  # state estimate
        self.p = 1.0  # estimate error covariance
        self.initialized = False

    def update(self, measurement: float) -> float:
        if not self.initialized:
            self.x = measurement
            self.initialized = True
            return self.x

        # Prediction
        self.p = self.p + self.q

        # Measurement update (Correction)
        k = self.p / (self.p + self.r)
        self.x = self.x + k * (measurement - self.x)
        self.p = (1 - k) * self.p
        return self.x

class BusGPSKalmanFilter:
    """
    2D Position & Speed Kalman Filter for real-time bus tracking.
    Smoothes latitude, longitude, and speed, and rejects impossible jumps.
    """
    def __init__(self, max_realistic_speed_kmh: float = 120.0):
        self.max_realistic_speed_kmh = max_realistic_speed_kmh
        self.lat_filter = KalmanFilter1D(process_variance=1e-5, measurement_variance=5e-4)
        self.lon_filter = KalmanFilter1D(process_variance=1e-5, measurement_variance=5e-4)
        self.speed_filter = KalmanFilter1D(process_variance=0.5, measurement_variance=2.0)
        
        self.last_lat: Optional[float] = None
        self.last_lon: Optional[float] = None
        self.last_timestamp: Optional[float] = None

    def validate_and_filter(
        self,
        lat: float,
        lon: float,
        speed: float,
        timestamp: Optional[float] = None
    ) -> Tuple[float, float, float, bool]:
        """
        Validates the incoming coordinate against physical constraints and applies Kalman smoothing.
        Returns: (filtered_lat, filtered_lon, filtered_speed, is_valid)
        """
        current_time = timestamp or time.time()

        # Coordinate bounds check
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return lat, lon, speed, False

        # First reading initialization
        if self.last_lat is None or self.last_lon is None or self.last_timestamp is None:
            self.last_lat = lat
            self.last_lon = lon
            self.last_timestamp = current_time
            f_lat = self.lat_filter.update(lat)
            f_lon = self.lon_filter.update(lon)
            f_speed = self.speed_filter.update(max(0.0, speed))
            return f_lat, f_lon, f_speed, True

        # Check time difference
        dt = max(0.1, current_time - self.last_timestamp)
        distance_km = haversine_distance(self.last_lat, self.last_lon, lat, lon)
        calculated_speed_kmh = (distance_km / dt) * 3600.0

        # Impossible jump rejection (teleportation check)
        if calculated_speed_kmh > self.max_realistic_speed_kmh and distance_km > 0.5:
            # Reject jump - retain previous state with slight decay
            return self.last_lat, self.last_lon, self.speed_filter.x * 0.9, False

        # Apply Kalman filter smoothing
        filtered_lat = self.lat_filter.update(lat)
        filtered_lon = self.lon_filter.update(lon)
        
        effective_speed = speed if speed > 0 else calculated_speed_kmh
        filtered_speed = round(max(0.0, self.speed_filter.update(effective_speed)), 1)

        self.last_lat = filtered_lat
        self.last_lon = filtered_lon
        self.last_timestamp = current_time

        return round(filtered_lat, 6), round(filtered_lon, 6), filtered_speed, True

# In-memory registry of active bus Kalman filters
bus_filters: Dict[str, BusGPSKalmanFilter] = {}

def get_bus_kalman_filter(bus_id: str) -> BusGPSKalmanFilter:
    if bus_id not in bus_filters:
        bus_filters[bus_id] = BusGPSKalmanFilter()
    return bus_filters[bus_id]

def reset_bus_kalman_filter(bus_id: str):
    if bus_id in bus_filters:
        del bus_filters[bus_id]
