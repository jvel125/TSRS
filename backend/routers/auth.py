from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt_util
import bcrypt
import random
import string

from database import get_db
from models import Passenger, AccessLog
from schemas import PassengerRegister, PassengerLogin, Token
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


def _hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_pw(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def _generate_ffn() -> str:
    prefix = "TSK"
    digits = "".join(random.choices(string.digits, k=7))
    return f"{prefix}{digits}"


def _create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload["exp"] = int(expire.timestamp())
    return jwt_util.encode(payload, settings.secret_key)


@router.post("/register", response_model=Token, status_code=201)
def register(body: PassengerRegister, request: Request, db: Session = Depends(get_db)):
    if db.query(Passenger).filter(Passenger.email == body.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    if db.query(Passenger).filter(Passenger.passport_number == body.passport_number).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Passport number already registered")

    ffn = _generate_ffn()
    while db.query(Passenger).filter(Passenger.frequent_flyer_number == ffn).first():
        ffn = _generate_ffn()

    passenger = Passenger(
        email=body.email,
        password_hash=_hash_pw(body.password),
        first_name=body.first_name,
        last_name=body.last_name,
        passport_number=body.passport_number,
        frequent_flyer_number=ffn,
        tier="Bronze",
    )
    db.add(passenger)
    db.commit()
    db.refresh(passenger)

    db.add(AccessLog(
        passenger_id=passenger.id,
        event_type="REGISTER",
        status="SUCCESS",
        ip_address=request.client.host if request.client else None,
    ))
    db.commit()

    token = _create_access_token({"sub": str(passenger.id), "ffn": ffn})
    return Token(
        access_token=token,
        token_type="bearer",
        passenger_id=passenger.id,
        frequent_flyer_number=ffn,
        tier=passenger.tier,
    )


@router.post("/login", response_model=Token)
def login(body: PassengerLogin, request: Request, db: Session = Depends(get_db)):
    passenger = db.query(Passenger).filter(Passenger.email == body.email).first()
    if not passenger or not _verify_pw(body.password, passenger.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    db.add(AccessLog(
        passenger_id=passenger.id,
        event_type="LOGIN",
        status="SUCCESS",
        ip_address=request.client.host if request.client else None,
    ))
    db.commit()

    token = _create_access_token({"sub": str(passenger.id), "ffn": passenger.frequent_flyer_number})
    return Token(
        access_token=token,
        token_type="bearer",
        passenger_id=passenger.id,
        frequent_flyer_number=passenger.frequent_flyer_number,
        tier=passenger.tier,
    )
