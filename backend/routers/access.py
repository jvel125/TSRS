import json
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import numpy as np

from database import get_db
from models import Passenger, Booking, AccessLog
from schemas import GateAccessRequest, GateAccessResponse, AccessLogOut, BookingOut
from config import settings
from routers.passengers import get_current_passenger

router = APIRouter(prefix="/access", tags=["access"])


def _euclidean(a: list, b: list) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    return float(np.linalg.norm(va - vb))


def _distance_to_confidence(distance: float, threshold: float) -> float:
    if distance >= threshold * 2:
        return 0.0
    return max(0.0, 1.0 - (distance / threshold))


def _identify_by_face(descriptor: list, db: Session):
    enrolled = db.query(Passenger).filter(Passenger.face_descriptor.isnot(None)).all()
    if not enrolled:
        return None, 999.0, 0.0

    best_p, best_d = None, float("inf")
    for p in enrolled:
        d = _euclidean(descriptor, json.loads(p.face_descriptor))
        if d < best_d:
            best_d = d
            best_p = p

    conf = _distance_to_confidence(best_d, settings.face_match_threshold)
    matched = best_d < settings.face_match_threshold
    return (best_p if matched else None), best_d, conf


@router.post("/gate", response_model=GateAccessResponse)
def gate_access(body: GateAccessRequest, request: Request, db: Session = Depends(get_db)):
    if len(body.descriptor) != 128:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Descriptor must be 128-dimensional")

    allowed_events = {"CHECKIN", "GATE_ACCESS", "BOARDING"}
    if body.event_type not in allowed_events:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"event_type must be one of {allowed_events}")

    passenger, distance, confidence = _identify_by_face(body.descriptor, db)
    now = datetime.utcnow()

    if passenger is None:
        db.add(AccessLog(
            passenger_id=None,
            event_type=body.event_type,
            location=body.location,
            status="FAILED",
            confidence=confidence,
            detail="Face not recognised",
            ip_address=request.client.host if request.client else None,
        ))
        db.commit()
        return GateAccessResponse(
            granted=False, event_type=body.event_type, location=body.location,
            passenger_id=None, first_name=None, last_name=None,
            frequent_flyer_number=None, tier=None, booking=None,
            confidence=confidence, message="Face not recognised", timestamp=now,
        )

    # Locate the relevant booking
    booking = (
        db.query(Booking)
        .filter(
            Booking.passenger_id == passenger.id,
            Booking.status.in_(["Confirmed", "CheckedIn"]),
        )
        .join(Booking.flight)
        .order_by(Booking.created_at.desc())
        .first()
    )

    granted = True
    message = "Access granted"

    if body.event_type == "CHECKIN":
        if booking and booking.status == "Confirmed":
            booking.status = "CheckedIn"
            booking.checkin_time = now
            message = f"Checked in — seat {booking.seat_number}"
        elif booking and booking.status == "CheckedIn":
            message = "Already checked in"
        else:
            granted = False
            message = "No eligible booking found for check-in"

    elif body.event_type == "GATE_ACCESS":
        if not booking or booking.status not in ("CheckedIn",):
            granted = False
            message = "Check-in required before gate access"

    elif body.event_type == "BOARDING":
        if booking and booking.status == "CheckedIn":
            booking.status = "Boarded"
            booking.boarding_time = now
            message = f"Welcome aboard — seat {booking.seat_number}"
        elif booking and booking.status == "Boarded":
            message = "Already boarded"
        else:
            granted = False
            message = "Valid check-in required before boarding"

    db.add(AccessLog(
        passenger_id=passenger.id,
        event_type=body.event_type,
        location=body.location,
        status="SUCCESS" if granted else "FAILED",
        confidence=confidence,
        detail=message,
        ip_address=request.client.host if request.client else None,
    ))
    db.commit()

    if booking:
        db.refresh(booking)

    return GateAccessResponse(
        granted=granted,
        event_type=body.event_type,
        location=body.location,
        passenger_id=passenger.id,
        first_name=passenger.first_name,
        last_name=passenger.last_name,
        frequent_flyer_number=passenger.frequent_flyer_number,
        tier=passenger.tier,
        booking=BookingOut.model_validate(booking) if booking else None,
        confidence=confidence,
        message=message,
        timestamp=now,
    )


@router.get("/logs", response_model=List[AccessLogOut])
def get_logs(
    limit: int = 50,
    passenger: Passenger = Depends(get_current_passenger),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(AccessLog)
        .filter(AccessLog.passenger_id == passenger.id)
        .order_by(AccessLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return logs


@router.get("/admin/logs", response_model=List[AccessLogOut])
def get_all_logs(limit: int = 100, db: Session = Depends(get_db)):
    """Admin endpoint — add auth middleware before deploying to production."""
    return db.query(AccessLog).order_by(AccessLog.timestamp.desc()).limit(limit).all()
