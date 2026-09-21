"""
Training Script for TransitNow ETA Prediction Model
Generates historical and synthetic transit route data, trains a RandomForestRegressor,
and exports eta_model.joblib for production inference.
"""
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

def generate_synthetic_transit_data(n_samples: int = 5000) -> pd.DataFrame:
    np.random.seed(42)

    # 1. Feature: Distance remaining along route (0.5 km to 25 km)
    distance_km = np.random.uniform(0.5, 25.0, n_samples)

    # 2. Feature: Current observed bus speed (10 km/h to 60 km/h)
    speed_kmh = np.random.uniform(10.0, 50.0, n_samples)

    # 3. Feature: Remaining intermediate stops (1 to 15 stops)
    stops_remaining = np.random.randint(1, 15, n_samples)

    # 4. Feature: Hour of the day (6 to 22)
    hour_of_day = np.random.randint(6, 23, n_samples)

    # 5. Feature: Day of the week (0=Mon, 6=Sun)
    day_of_week = np.random.randint(0, 7, n_samples)

    # 6. Feature: Reported delay offset (0 to 25 mins)
    delay_offset = np.random.choice([0, 0, 0, 5, 10, 15, 20], size=n_samples)

    # Target variable: True travel time in minutes
    # Physics base: (distance / speed) * 60
    base_travel_mins = (distance_km / speed_kmh) * 60.0

    # Traffic multiplier during morning (8-10) and evening (17-20) peak hours
    traffic_factor = np.where(
        ((hour_of_day >= 8) & (hour_of_day <= 10)) | ((hour_of_day >= 17) & (hour_of_day <= 20)),
        1.35,
        1.05
    )

    # Dwell time per stop: ~2.5 mins with variance
    dwell_mins = stops_remaining * np.random.uniform(1.8, 3.0, n_samples)

    # Gaussian noise
    noise = np.random.normal(0, 1.5, n_samples)

    actual_eta_mins = (base_travel_mins * traffic_factor) + dwell_mins + delay_offset + noise
    actual_eta_mins = np.clip(actual_eta_mins, 1.0, 180.0)

    df = pd.DataFrame({
        "distance_km": distance_km,
        "speed_kmh": speed_kmh,
        "stops_remaining": stops_remaining,
        "hour_of_day": hour_of_day,
        "day_of_week": day_of_week,
        "delay_offset": delay_offset,
        "actual_eta_mins": actual_eta_mins
    })
    return df

def train_and_save():
    print("Generating transit training dataset...")
    df = generate_synthetic_transit_data(8000)

    feature_cols = [
        "distance_km",
        "speed_kmh",
        "stops_remaining",
        "hour_of_day",
        "day_of_week",
        "delay_offset"
    ]
    X = df[feature_cols]
    y = df["actual_eta_mins"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Fitting RandomForestRegressor ETA model...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    print(f"Model Training Results -> MAE: {mae:.2f} mins | R^2: {r2:.3f}")

    output_path = os.path.join(os.path.dirname(__file__), "eta_model.joblib")
    joblib.dump(model, output_path)
    print(f"Exported model to: {output_path}")

if __name__ == "__main__":
    train_and_save()
