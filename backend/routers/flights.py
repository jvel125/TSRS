from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Flight, Booking
from schemas import FlightOut, BookingOut
from routers.passengers import get_current_passenger
from models import Passenger

router = APIRouter(prefix="/flights", tags=["flights"])


@router.get("", response_model=List[FlightOut])
def list_flights(db: Session = Depends(get_db)):
    return db.query(Flight).order_by(Flight.departure_time).all()


@router.get("/{flight_id}", response_model=FlightOut)
def get_flight(flight_id: int, db: Session = Depends(get_db)):
    f = db.query(Flight).filter(Flight.id == flight_id).first()
    if not f:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Flight not found")
    return f


@router.get("/number/{flight_number}", response_model=FlightOut)
def get_flight_by_number(flight_number: str, db: Session = Depends(get_db)):
    f = db.query(Flight).filter(Flight.flight_number == flight_number.upper()).first()
    if not f:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Flight not found")
    return f


@router.get("/me/bookings", response_model=List[BookingOut])
def my_bookings(
    passenger: Passenger = Depends(get_current_passenger),
    db: Session = Depends(get_db),
):
    bookings = (
        db.query(Booking)
        .filter(Booking.passenger_id == passenger.id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return bookings
