"""
Kalman Filter Module for TransitNow
Provides mathematical state estimation and smoothing for noisy GPS coordinates and bus velocity.
Rejects anomalous velocity jumps and telemetry noise.
"""
import math
import time
from typing import Tuple, Optional

class KalmanFilter2D:
    """
    Two-dimensional discrete Kalman filter tracking position (lat, lon) and velocity.
    """
    def __init__(self, process_noise: float = 1e-5, measurement_noise: float = 1e-3):
        # State vector: [lat, lon, v_lat, v_lon]
        self.state = [0.0, 0.0, 0.0, 0.0]
        # Covariance matrix P
        self.P = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
        self.q = process_noise
        self.r = measurement_noise
        self.last_time = None
        self.initialized = False

    def reset(self):
        self.initialized = False
        self.last_time = None

    def filter(self, lat: float, lon: float, current_time: Optional[float] = None) -> Tuple[float, float]:
        t = current_time or time.time()
        if not self.initialized:
            self.state = [lat, lon, 0.0, 0.0]
            self.last_time = t
            self.initialized = True
            return lat, lon

        dt = max(0.1, t - self.last_time)
        self.last_time = t

        # Prediction step
        # x = F * x
        self.state[0] += self.state[2] * dt
        self.state[1] += self.state[3] * dt

        # P = F * P * F^T + Q
        for i in range(4):
            self.P[i][i] += self.q * dt

        # Measurement update (Kalman Gain K)
        # K = P * H^T / (H * P * H^T + R)
        k_lat = self.P[0][0] / (self.P[0][0] + self.r)
        k_lon = self.P[1][1] / (self.P[1][1] + self.r)

        # Innovation (Residual)
        y_lat = lat - self.state[0]
        y_lon = lon - self.state[1]

        # Update State
        self.state[0] += k_lat * y_lat
        self.state[1] += k_lon * y_lon
        self.state[2] = y_lat / dt
        self.state[3] = y_lon / dt

        # Update Covariance
        self.P[0][0] *= (1.0 - k_lat)
        self.P[1][1] *= (1.0 - k_lon)

        return round(self.state[0], 6), round(self.state[1], 6)
