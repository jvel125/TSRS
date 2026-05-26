from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Passenger(Base):
    __tablename__ = "passengers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    passport_number = Column(String, unique=True, nullable=False)
    frequent_flyer_number = Column(String, unique=True, index=True)
    tier = Column(String, default="Bronze")  # Bronze / Silver / Gold / Platinum
    face_descriptor = Column(Text, nullable=True)  # JSON array of 128 floats
    face_enrolled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    bookings = relationship("Booking", back_populates="passenger")
    access_logs = relationship("AccessLog", back_populates="passenger")


class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)
    flight_number = Column(String, unique=True, nullable=False, index=True)
    airline = Column(String, nullable=False)
    origin = Column(String(3), nullable=False)   # IATA code
    destination = Column(String(3), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    status = Column(String, default="Scheduled")  # Scheduled / Boarding / Departed / Arrived / Cancelled
    gate = Column(String, nullable=True)
    terminal = Column(String, nullable=True)
    aircraft_type = Column(String, nullable=True)

    bookings = relationship("Booking", back_populates="flight")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    passenger_id = Column(Integer, ForeignKey("passengers.id"), nullable=False)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False)
    seat_number = Column(String, nullable=False)
    seat_class = Column(String, default="Economy")  # Economy / Business / First
    status = Column(String, default="Confirmed")    # Confirmed / CheckedIn / Boarded / Cancelled
    boarding_pass_code = Column(String, unique=True, nullable=False, index=True)
    checkin_time = Column(DateTime, nullable=True)
    boarding_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    passenger = relationship("Passenger", back_populates="bookings")
    flight = relationship("Flight", back_populates="bookings")


class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    passenger_id = Column(Integer, ForeignKey("passengers.id"), nullable=True)
    event_type = Column(String, nullable=False)  # LOGIN / ENROLL / CHECKIN / GATE_ACCESS / BOARDING
    location = Column(String, nullable=True)      # Gate B12, Terminal 3, etc.
    status = Column(String, nullable=False)       # SUCCESS / FAILED / UNKNOWN
    confidence = Column(Float, nullable=True)     # 0.0 – 1.0
    detail = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, server_default=func.now())

    passenger = relationship("Passenger", back_populates="access_logs")
