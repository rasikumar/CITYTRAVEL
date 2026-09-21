import math
from typing import List, Tuple

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points in kilometers.
    """
    R = 6371.0  # Earth's radius in km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance = R * c
    return round(distance, 3)

def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points in meters.
    """
    return round(haversine_distance(lat1, lon1, lat2, lon2) * 1000.0, 1)

def format_distance(distance_km: float) -> str:
    """
    Format distance nicely for UI (e.g. '450 m' or '1.4 km').
    """
    if distance_km < 1.0:
        meters = int(distance_km * 1000)
        return f"{meters} m"
    return f"{distance_km:.1f} km"

def calculate_path_distance(coords: List[Tuple[float, float]]) -> float:
    """
    Calculate total cumulative distance along a list of (lat, lon) coordinates.
    """
    if len(coords) < 2:
        return 0.0
    total = 0.0
    for i in range(len(coords) - 1):
        total += haversine_distance(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1])
    return round(total, 3)
