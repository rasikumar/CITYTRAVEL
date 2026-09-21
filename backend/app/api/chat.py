import re
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import Bus, Route, Stop, RouteStop, Trip, DelayReport
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.eta import ETAEngine
from app.services.distance import haversine_distance

router = APIRouter(prefix="/api/chat", tags=["AI Transit Assistant"])

# ================= TRANSIT FUNCTIONS =================

def find_bus(query_str: str, db: Session) -> List[Dict[str, Any]]:
    like_q = f"%{query_str.strip()}%"
    buses = db.query(Bus).filter(
        or_(Bus.bus_id.ilike(like_q), Bus.bus_name.ilike(like_q))
    ).all()
    results = []
    for b in buses:
        results.append({
            "bus_id": b.bus_id,
            "bus_name": b.bus_name,
            "status": b.status,
            "speed_kmh": b.current_speed or 0.0,
            "route": b.route.route_name if b.route else "No Route Assigned",
            "current_location": f"({b.current_latitude:.4f}, {b.current_longitude:.4f})" if b.current_latitude else "Unknown"
        })
    return results

def find_route(query_str: str, db: Session) -> List[Dict[str, Any]]:
    like_q = f"%{query_str.strip()}%"
    routes = db.query(Route).filter(
        or_(Route.route_id.ilike(like_q), Route.route_name.ilike(like_q))
    ).all()
    results = []
    for r in routes:
        stops = [rs.stop.stop_name for rs in r.route_stops if rs.stop]
        results.append({
            "route_id": r.route_id,
            "route_name": r.route_name,
            "direction": r.direction,
            "stops": stops
        })
    return results

def find_stop(query_str: str, db: Session) -> List[Dict[str, Any]]:
    like_q = f"%{query_str.strip()}%"
    stops = db.query(Stop).filter(Stop.stop_name.ilike(like_q)).all()
    results = []
    for s in stops:
        routes_served = []
        for rs in s.route_stops:
            if rs.route:
                routes_served.append(f"Route {rs.route.route_id}")
        results.append({
            "stop_id": s.stop_id,
            "stop_name": s.stop_name,
            "coordinates": (s.latitude, s.longitude),
            "routes_served": list(set(routes_served))
        })
    return results

def get_bus_status(bus_id: str, db: Session) -> Dict[str, Any]:
    bus = db.query(Bus).filter(Bus.bus_id.ilike(bus_id.strip())).first()
    if not bus:
        return {"error": f"Bus '{bus_id}' not found in the TransitNow fleet."}

    return {
        "bus_id": bus.bus_id,
        "bus_name": bus.bus_name,
        "status": bus.status,
        "speed": f"{bus.current_speed or 0.0} km/h",
        "route": bus.route.route_name if bus.route else "Unassigned",
        "has_active_driver": bus.driver is not None,
        "latitude": bus.current_latitude,
        "longitude": bus.current_longitude,
    }

def get_next_stop(bus_id: str, db: Session) -> Dict[str, Any]:
    bus = db.query(Bus).filter(Bus.bus_id.ilike(bus_id.strip())).first()
    if not bus:
        return {"error": f"Bus '{bus_id}' not found."}

    if not bus.route or not bus.current_latitude or not bus.current_longitude:
        return {"bus_id": bus.bus_id, "next_stop": "Bus is at depot / not on active route."}

    ordered_stops = [
        {
            "stop_id": rs.stop.stop_id,
            "stop_name": rs.stop.stop_name,
            "latitude": rs.stop.latitude,
            "longitude": rs.stop.longitude,
            "sequence": rs.sequence,
            "dwell_time_minutes": rs.dwell_time_minutes or 2
        }
        for rs in bus.route.route_stops if rs.stop
    ]

    eta_info = ETAEngine.find_next_stop_and_etas(
        bus_lat=bus.current_latitude,
        bus_lon=bus.current_longitude,
        bus_speed_kmh=bus.current_speed or 25.0,
        ordered_stops=ordered_stops
    )
    return {
        "bus_id": bus.bus_id,
        "next_stop": eta_info["next_stop"],
        "eta": eta_info["eta_text"],
        "distance_km": round(eta_info["next_stop_distance_km"], 2)
    }

def get_eta(bus_id: str, stop_name: str, db: Session) -> Dict[str, Any]:
    bus = db.query(Bus).filter(Bus.bus_id.ilike(bus_id.strip())).first()
    if not bus or not bus.route or not bus.current_latitude:
        return {"error": f"Bus '{bus_id}' is currently offline or not on an active line."}

    target_stop = db.query(Stop).filter(Stop.stop_name.ilike(f"%{stop_name.strip()}%")).first()
    if not target_stop:
        return {"error": f"Stop '{stop_name}' not found."}

    ordered_stops = [
        {
            "stop_id": rs.stop.stop_id,
            "stop_name": rs.stop.stop_name,
            "latitude": rs.stop.latitude,
            "longitude": rs.stop.longitude,
            "sequence": rs.sequence,
            "dwell_time_minutes": rs.dwell_time_minutes or 2
        }
        for rs in bus.route.route_stops if rs.stop
    ]

    eta_info = ETAEngine.find_next_stop_and_etas(
        bus_lat=bus.current_latitude,
        bus_lon=bus.current_longitude,
        bus_speed_kmh=bus.current_speed or 25.0,
        ordered_stops=ordered_stops
    )

    for se in eta_info["stop_etas"]:
        if target_stop.stop_name.lower() in se["stop_name"].lower():
            return {
                "bus_id": bus.bus_id,
                "stop_name": se["stop_name"],
                "eta": se["eta_text"],
                "status": se["status"]
            }

    return {
        "bus_id": bus.bus_id,
        "stop_name": target_stop.stop_name,
        "message": f"{target_stop.stop_name} is not on the route of {bus.bus_id} ({bus.route.route_name})."
    }

def get_delay(bus_id: str, db: Session) -> Dict[str, Any]:
    bus = db.query(Bus).filter(Bus.bus_id.ilike(bus_id.strip())).first()
    if not bus:
        return {"error": f"Bus '{bus_id}' not found."}

    active_trip = db.query(Trip).filter(Trip.bus_id == bus.id, Trip.status == "ACTIVE").order_by(Trip.id.desc()).first()
    if not active_trip:
        return {"bus_id": bus.bus_id, "has_delay": False, "message": "Bus has no active trip running right now."}

    delay = db.query(DelayReport).filter(DelayReport.trip_id == active_trip.id).order_by(DelayReport.id.desc()).first()
    if delay:
        return {
            "bus_id": bus.bus_id,
            "has_delay": True,
            "reason": delay.reason,
            "note": delay.note or "No additional note provided.",
            "reported_at": delay.reported_at.strftime("%H:%M")
        }
    return {
        "bus_id": bus.bus_id,
        "has_delay": False,
        "message": f"{bus.bus_id} is operating on schedule with no delays reported."
    }

# ================= CHAT ENDPOINT =================

@router.post("", response_model=ChatResponse)
def transit_ai_assistant(payload: ChatRequest, db: Session = Depends(get_db)):
    msg = payload.message.lower().strip()
    now_str = datetime.utcnow().strftime("%H:%M:%S")

    # 1. Extract potential bus IDs (e.g. BUS001, bus002, 21g, 10a)
    bus_match = re.search(r'\b(bus\d{3}|bus\d+)\b', msg)
    found_bus_id = bus_match.group(1).upper() if bus_match else None
    
    # 2. Check for route IDs
    route_match = re.search(r'\b(\d{1,2}[a-z]|\d{1,3})\b', msg)
    found_route_id = route_match.group(1).upper() if route_match else None

    # Intent routing:
    # A. "Where is my bus" / "Where is BUS001"
    if "where is" in msg or "location" in msg or "track" in msg:
        target_bus = found_bus_id or "BUS001"
        status_data = get_bus_status(target_bus, db)
        next_data = get_next_stop(target_bus, db)
        
        if "error" in status_data:
            reply = status_data["error"]
        else:
            reply = (
                f"🚌 **{status_data['bus_id']}** ({status_data['bus_name']}) is currently **{status_data['status']}** "
                f"at {status_data['speed']}. Operating on {status_data['route']}. "
                f"Next upcoming stop is **{next_data.get('next_stop', 'Unknown')}** (ETA: {next_data.get('eta', 'N/A')})."
            )
        return ChatResponse(reply=reply, intent="find_bus", data=status_data, timestamp=now_str)

    # B. "Why is my bus late" / "delay"
    if "late" in msg or "delay" in msg or "why" in msg:
        target_bus = found_bus_id or "BUS001"
        delay_info = get_delay(target_bus, db)
        if delay_info.get("has_delay"):
            reply = f"⚠️ **{target_bus} is delayed.** Reason reported: **{delay_info['reason']}** ({delay_info['note']}) at {delay_info['reported_at']}."
        else:
            reply = f"✅ **{target_bus} is currently running on schedule.** No delay reports have been filed by the driver."
        return ChatResponse(reply=reply, intent="get_delay", data=delay_info, timestamp=now_str)

    # C. "When will BUS001 arrive" / "ETA"
    if "when will" in msg or "eta" in msg or "arrive" in msg:
        target_bus = found_bus_id or "BUS001"
        
        # Check if a stop was mentioned
        stop_keywords = ["mattuthavani", "central", "mahal", "goripalayam", "simmakkal", "periyar", "othakadai"]
        matched_stop = None
        for sk in stop_keywords:
            if sk in msg:
                matched_stop = sk
                break
        
        if matched_stop:
            eta_res = get_eta(target_bus, matched_stop, db)
            if "error" in eta_res:
                reply = eta_res["error"]
            elif "message" in eta_res:
                reply = eta_res["message"]
            else:
                reply = f"⏱️ **{target_bus}** is estimated to reach **{eta_res['stop_name']}** in **{eta_res['eta']}**."
            return ChatResponse(reply=reply, intent="get_eta", data=eta_res, timestamp=now_str)
        else:
            next_data = get_next_stop(target_bus, db)
            reply = f"⏱️ **{target_bus}** is heading towards **{next_data.get('next_stop', 'Depot')}** with an ETA of **{next_data.get('eta', 'N/A')}**."
            return ChatResponse(reply=reply, intent="get_eta", data=next_data, timestamp=now_str)

    # D. "Next stop"
    if "next stop" in msg:
        target_bus = found_bus_id or "BUS001"
        next_data = get_next_stop(target_bus, db)
        reply = f"🚏 The next stop for **{target_bus}** is **{next_data.get('next_stop')}** ({next_data.get('distance_km')} km away, ETA: {next_data.get('eta')})."
        return ChatResponse(reply=reply, intent="get_next_stop", data=next_data, timestamp=now_str)

    # E. "Find bus to Mattuthavani" / destination search
    if "to " in msg or "find" in msg or "reach" in msg:
        # Check destination
        dest = msg.split("to ")[-1].strip("?. ") if "to " in msg else msg
        stops = find_stop(dest, db)
        if stops:
            s_name = stops[0]["stop_name"]
            routes = stops[0]["routes_served"]
            reply = f"📍 Found stop **{s_name}**. It is served by: {', '.join(routes) if routes else 'Local Transit Lines'}. Bus **BUS001 (Route 21G)** provides direct service."
        else:
            routes = find_route(dest, db)
            if routes:
                reply = f"🛣️ Found **{routes[0]['route_name']}** (Route {routes[0]['route_id']}) which travels via: {' ➔ '.join(routes[0]['stops'])}."
            else:
                reply = f"🔍 No direct buses or stops found matching '{dest}'. Try searching for 'Mattuthavani', 'Madurai Central', or 'Route 21G'."
        return ChatResponse(reply=reply, intent="find_route", data={"query": dest}, timestamp=now_str)

    # Default general guidance
    return ChatResponse(
        reply=(
            "👋 Hello! I am your TransitNow AI assistant. You can ask me:\n"
            "• *Where is BUS001?*\n"
            "• *When will BUS001 arrive at Mattuthavani?*\n"
            "• *Why is my bus late?*\n"
            "• *What is the next stop?*\n"
            "• *Find bus to Mattuthavani*"
        ),
        intent="general_help",
        data={},
        timestamp=now_str
    )
