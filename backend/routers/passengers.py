from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import jwt_util
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database import get_db
from models import Passenger
from schemas import PassengerOut
from config import settings

router = APIRouter(prefix="/passengers", tags=["passengers"])
bearer = HTTPBearer()


def get_current_passenger(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> Passenger:
    try:
        payload = jwt_util.decode(credentials.credentials, settings.secret_key)
        passenger_id = int(payload["sub"])
    except (ValueError, KeyError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    passenger = db.query(Passenger).filter(Passenger.id == passenger_id).first()
    if not passenger:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Passenger not found")
    return passenger


@router.get("/me", response_model=PassengerOut)
def get_me(passenger: Passenger = Depends(get_current_passenger)):
    return _to_out(passenger)


@router.get("/{passenger_id}", response_model=PassengerOut)
def get_passenger(passenger_id: int, db: Session = Depends(get_db)):
    p = db.query(Passenger).filter(Passenger.id == passenger_id).first()
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Passenger not found")
    return _to_out(p)


def _to_out(p: Passenger) -> PassengerOut:
    return PassengerOut(
        id=p.id,
        email=p.email,
        first_name=p.first_name,
        last_name=p.last_name,
        passport_number=p.passport_number,
        frequent_flyer_number=p.frequent_flyer_number,
        tier=p.tier,
        face_enrolled=p.face_descriptor is not None,
        face_enrolled_at=p.face_enrolled_at,
        created_at=p.created_at,
    )
