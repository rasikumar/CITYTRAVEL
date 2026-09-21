import os
import joblib
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional

MODEL_PATH = os.path.join(os.path.dirname(__file__), "eta_model.joblib")

class ETAPredictor:
    """
    ML-based Estimated Time of Arrival (ETA) predictor using trained Scikit-learn model.
    Includes physics-informed regression fallback if model artifact is loading or missing.
    """
    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"[ETAPredictor] Warning: Could not load {MODEL_PATH}: {e}")
                self.model = None

    def predict_eta_minutes(
        self,
        distance_km: float,
        speed_kmh: float,
        stops_remaining: int = 1,
        hour_of_day: Optional[int] = None,
        day_of_week: Optional[int] = None,
        delay_offset_minutes: int = 0
    ) -> float:
        now = datetime.now()
        hr = hour_of_day if hour_of_day is not None else now.hour
        dow = day_of_week if day_of_week is not None else now.weekday()
        effective_speed = max(10.0, speed_kmh)

        # Use Scikit-Learn Model if loaded
        if self.model is not None:
            try:
                # Features: [distance_km, speed_kmh, stops_remaining, hour_of_day, day_of_week, delay_offset]
                X = np.array([[distance_km, effective_speed, stops_remaining, hr, dow, delay_offset_minutes]])
                predicted = float(self.model.predict(X)[0])
                return max(1.0, round(predicted, 1))
            except Exception as err:
                print(f"[ETAPredictor] Prediction fallback due to error: {err}")

        # Physics-informed fallback: Travel Time = Dist / Speed + Dwell * stops + delay
        travel_time_hours = distance_km / effective_speed
        travel_time_mins = travel_time_hours * 60.0
        dwell_penalty_mins = stops_remaining * 2.0
        total_mins = max(1.0, travel_time_mins + dwell_penalty_mins + delay_offset_minutes)
        return round(total_mins, 1)

predictor = ETAPredictor()
