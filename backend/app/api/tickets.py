import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models import Ticket, Payment, Bus, Route, Passenger
from app.schemas.ticket import TicketPurchase, TicketResponse
from app.api.passenger import get_current_passenger
from app.services.payment import payment_provider, MockPaymentProvider

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

@router.get("", response_model=List[dict])
def get_passenger_tickets(
    passenger: Passenger = Depends(get_current_passenger),
    db: Session = Depends(get_db)
):
    tickets = db.query(Ticket).filter(Ticket.passenger_id == passenger.id).order_by(Ticket.id.desc()).all()
    results = []
    for t in tickets:
        results.append({
            "id": t.id,
            "ticket_number": t.ticket_number,
            "passenger_id": t.passenger_id,
            "bus_id": t.bus_id,
            "bus_name": t.bus.bus_name if t.bus else "Any Transit Line",
            "route_name": t.bus.route.route_name if t.bus and t.bus.route else "All Routes Pass",
            "ticket_type": t.ticket_type,
            "fare": t.fare,
            "status": t.status,
            "qr_code_data": t.qr_code_data,
            "payment_provider": t.payment.provider if t.payment else "UPI",
            "payment_status": t.payment.status if t.payment else "SUCCESS",
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return results

@router.post("", response_model=dict)
def purchase_ticket(
    payload: TicketPurchase,
    passenger: Passenger = Depends(get_current_passenger),
    db: Session = Depends(get_db)
):
    # Lookup bus
    bus = db.query(Bus).filter(Bus.bus_id == payload.bus_id).first()
    bus_id_val = bus.id if bus else None
    route_id_val = bus.route_id if bus else None

    # Calculate fare based on ticket type
    fare = MockPaymentProvider.FARES.get(payload.ticket_type, 15.0)

    # Process simulated payment
    payment_result = payment_provider.process_payment(
        amount=fare,
        method=payload.payment_method,
        passenger_id=passenger.id,
        bus_id=payload.bus_id
    )

    ticket_number = f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    qr_payload = f"TRANSITNOW|{ticket_number}|{payload.ticket_type}|{fare}|{payload.bus_id}"

    new_ticket = Ticket(
        ticket_number=ticket_number,
        passenger_id=passenger.id,
        bus_id=bus_id_val,
        route_id=route_id_val,
        ticket_type=payload.ticket_type,
        fare=fare,
        status="ACTIVE",
        qr_code_data=qr_payload
    )
    db.add(new_ticket)
    db.flush()

    new_payment = Payment(
        payment_id=payment_result["transaction_id"],
        ticket_id=new_ticket.id,
        amount=fare,
        provider=payment_result["provider"],
        status=payment_result["status"]
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_ticket)

    return {
        "success": True,
        "message": "Ticket issued successfully! (Test Mode: No actual bank funds charged)",
        "ticket": {
            "id": new_ticket.id,
            "ticket_number": new_ticket.ticket_number,
            "bus_id": payload.bus_id,
            "bus_name": bus.bus_name if bus else "Transit Bus",
            "route_name": bus.route.route_name if bus and bus.route else "General Route",
            "ticket_type": new_ticket.ticket_type,
            "fare": new_ticket.fare,
            "status": new_ticket.status,
            "qr_code_data": new_ticket.qr_code_data,
            "payment_provider": new_payment.provider,
            "transaction_id": new_payment.payment_id,
            "created_at": new_ticket.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
    }
