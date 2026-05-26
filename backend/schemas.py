from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


# ── Auth ─────────────────────────────────────────────────────────────────────

class PassengerRegister(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    passport_number: str

class PassengerLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    passenger_id: int
    frequent_flyer_number: str
    tier: str


# ── Passenger ────────────────────────────────────────────────────────────────

class PassengerOut(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    passport_number: str
    frequent_flyer_number: Optional[str]
    tier: str
    face_enrolled: bool
    face_enrolled_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Biometrics ───────────────────────────────────────────────────────────────

class FaceEnrollRequest(BaseModel):
    descriptor: List[float]   # 128-d face descriptor from face-api.js

class FaceVerifyRequest(BaseModel):
    descriptor: List[float]

class FaceVerifyResponse(BaseModel):
    matched: bool
    passenger_id: Optional[int]
    frequent_flyer_number: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    tier: Optional[str]
    confidence: float          # 1.0 = perfect match, 0.0 = no match
    distance: float


# ── Flights ───────────────────────────────────────────────────────────────────

class FlightOut(BaseModel):
    id: int
    flight_number: str
    airline: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    status: str
    gate: Optional[str]
    terminal: Optional[str]
    aircraft_type: Optional[str]

    class Config:
        from_attributes = True


# ── Bookings ──────────────────────────────────────────────────────────────────

class BookingOut(BaseModel):
    id: int
    passenger_id: int
    seat_number: str
    seat_class: str
    status: str
    boarding_pass_code: str
    checkin_time: Optional[datetime]
    boarding_time: Optional[datetime]
    flight: FlightOut

    class Config:
        from_attributes = True


# ── Access ────────────────────────────────────────────────────────────────────

class GateAccessRequest(BaseModel):
    descriptor: List[float]
    location: str             # e.g. "Gate B12"
    event_type: str           # CHECKIN / GATE_ACCESS / BOARDING

class GateAccessResponse(BaseModel):
    granted: bool
    event_type: str
    location: str
    passenger_id: Optional[int]
    first_name: Optional[str]
    last_name: Optional[str]
    frequent_flyer_number: Optional[str]
    tier: Optional[str]
    booking: Optional[BookingOut]
    confidence: float
    message: str
    timestamp: datetime

class AccessLogOut(BaseModel):
    id: int
    passenger_id: Optional[int]
    event_type: str
    location: Optional[str]
    status: str
    confidence: Optional[float]
    detail: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True
