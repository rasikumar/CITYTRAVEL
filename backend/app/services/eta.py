from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from app.services.distance import haversine_distance

class ETAEngine:
    """
    Computes real-time ETAs for bus stops along a route.
    Uses distance, current smoothed speed, scheduled dwell times, and delay offsets.
    """
    DEFAULT_URBAN_BUS_SPEED_KMH = 25.0  # Typical urban average speed when bus is stopped or crawling

    @classmethod
    def calculate_stop_eta(
        cls,
        bus_lat: float,
        bus_lon: float,
        bus_speed_kmh: float,
        stop_lat: float,
        stop_lon: float,
        dwell_time_minutes: int = 2,
        delay_offset_minutes: int = 0
    ) -> Tuple[int, str]:
        """
        Calculate estimated arrival time to a single stop in minutes and human-readable string.
        """
        dist_km = haversine_distance(bus_lat, bus_lon, stop_lat, stop_lon)

        # If bus is very close (< 50m)
        if dist_km <= 0.05:
            return 0, "Arrived"
        elif dist_km <= 0.3:
            return 1, "Approaching (1 min)"

        # Determine effective speed
        effective_speed = bus_speed_kmh if bus_speed_kmh >= 10.0 else cls.DEFAULT_URBAN_BUS_SPEED_KMH

        # Travel time in hours = distance / speed
        travel_time_hours = dist_km / effective_speed
        travel_time_minutes = travel_time_hours * 60.0

        total_minutes = max(1, round(travel_time_minutes + delay_offset_minutes))
        if total_minutes == 1:
            return 1, "1 min"
        return total_minutes, f"{total_minutes} mins"

    @classmethod
    def find_next_stop_and_etas(
        cls,
        bus_lat: float,
        bus_lon: float,
        bus_speed_kmh: float,
        ordered_stops: List[Dict[str, Any]],
        delay_offset_minutes: int = 0
    ) -> Dict[str, Any]:
        """
        Given the bus position and the list of ordered stops along the route,
        identifies the next upcoming stop and estimates ETAs for all remaining stops.
        """
        if not ordered_stops:
            return {
                "next_stop": None,
                "next_stop_id": None,
                "next_stop_distance_km": 0.0,
                "eta_text": "N/A",
                "eta_minutes": 0,
                "stop_etas": []
            }

        # Find closest stop to understand progression
        stop_distances = []
        for stop in ordered_stops:
            d = haversine_distance(bus_lat, bus_lon, stop["latitude"], stop["longitude"])
            stop_distances.append((d, stop))

        # Sort by distance to find closest
        closest_dist, closest_stop = min(stop_distances, key=lambda x: x[0])
        closest_seq = closest_stop.get("sequence", 1)

        # If bus is within 50m of closest stop, next stop might be the one after it
        target_seq = closest_seq
        if closest_dist < 0.08 and closest_seq < len(ordered_stops):
            target_seq = closest_seq + 1

        # Locate next stop item
        next_stop_item = None
        for s in ordered_stops:
            if s.get("sequence") == target_seq:
                next_stop_item = s
                break
        if not next_stop_item:
            next_stop_item = ordered_stops[-1]

        # Calculate ETA to next stop
        dist_to_next = haversine_distance(bus_lat, bus_lon, next_stop_item["latitude"], next_stop_item["longitude"])
        eta_mins, eta_str = cls.calculate_stop_eta(
            bus_lat=bus_lat,
            bus_lon=bus_lon,
            bus_speed_kmh=bus_speed_kmh,
            stop_lat=next_stop_item["latitude"],
            stop_lon=next_stop_item["longitude"],
            dwell_time_minutes=next_stop_item.get("dwell_time_minutes", 2),
            delay_offset_minutes=delay_offset_minutes
        )

        # Calculate ETAs for subsequent stops along sequence
        cumulative_minutes = eta_mins
        stop_etas = []
        prev_stop_lat = next_stop_item["latitude"]
        prev_stop_lon = next_stop_item["longitude"]

        for stop in ordered_stops:
            seq = stop.get("sequence", 1)
            if seq < target_seq:
                stop_etas.append({
                    "stop_id": stop.get("stop_id"),
                    "stop_name": stop.get("stop_name"),
                    "sequence": seq,
                    "eta_text": "Passed",
                    "eta_minutes": 0,
                    "is_next": False,
                    "status": "passed"
                })
            elif seq == target_seq:
                stop_etas.append({
                    "stop_id": stop.get("stop_id"),
                    "stop_name": stop.get("stop_name"),
                    "sequence": seq,
                    "eta_text": eta_str,
                    "eta_minutes": eta_mins,
                    "is_next": True,
                    "status": "approaching" if eta_mins <= 2 else "en_route"
                })
            else:
                inter_dist = haversine_distance(prev_stop_lat, prev_stop_lon, stop["latitude"], stop["longitude"])
                effective_speed = bus_speed_kmh if bus_speed_kmh >= 10.0 else cls.DEFAULT_URBAN_BUS_SPEED_KMH
                leg_mins = max(1, round((inter_dist / effective_speed) * 60.0 + stop.get("dwell_time_minutes", 2)))
                cumulative_minutes += leg_mins
                prev_stop_lat = stop["latitude"]
                prev_stop_lon = stop["longitude"]
                stop_etas.append({
                    "stop_id": stop.get("stop_id"),
                    "stop_name": stop.get("stop_name"),
                    "sequence": seq,
                    "eta_text": f"{cumulative_minutes} mins",
                    "eta_minutes": cumulative_minutes,
                    "is_next": False,
                    "status": "scheduled"
                })

        return {
            "next_stop": next_stop_item.get("stop_name"),
            "next_stop_id": next_stop_item.get("stop_id"),
            "next_stop_distance_km": dist_to_next,
            "eta_text": eta_str,
            "eta_minutes": eta_mins,
            "stop_etas": stop_etas
        }
