"""Seed the database with sample flights and a demo passenger."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from database import engine, SessionLocal, Base
from models import Passenger, Flight, Booking
import bcrypt
import random, string

Base.metadata.create_all(bind=engine)

def _hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

db = SessionLocal()

# Demo flights
flights_data = [
    ("TSK101", "TrustedSky Airlines", "JFK", "LAX", 2, 5.5, "A12", "1", "Boeing 737"),
    ("TSK202", "TrustedSky Airlines", "LAX", "ORD", 4, 4.0, "B7",  "2", "Airbus A320"),
    ("TSK303", "TrustedSky Airlines", "ORD", "MIA", 6, 2.5, "C3",  "1", "Boeing 757"),
    ("TSK404", "TrustedSky Airlines", "MIA", "JFK", 8, 3.0, "D22", "3", "Airbus A321"),
    ("TSK505", "TrustedSky Airlines", "SFO", "SEA", 1, 2.0, "E5",  "1", "Embraer E175"),
]

now = datetime.utcnow()
flight_objs = []
for fn, airline, orig, dest, dep_offset_h, dur_h, gate, terminal, ac in flights_data:
    if db.query(Flight).filter(Flight.flight_number == fn).first():
        continue
    dep = now + timedelta(hours=dep_offset_h)
    arr = dep + timedelta(hours=dur_h)
    f = Flight(
        flight_number=fn, airline=airline, origin=orig, destination=dest,
        departure_time=dep, arrival_time=arr,
        status="Scheduled" if dep_offset_h > 1 else "Boarding",
        gate=gate, terminal=terminal, aircraft_type=ac,
    )
    db.add(f)
    flight_objs.append(f)

db.commit()

# Demo passenger
if not db.query(Passenger).filter(Passenger.email == "demo@trustedsky.com").first():
    p = Passenger(
        email="demo@trustedsky.com",
        password_hash=_hash("demo1234"),
        first_name="Alex",
        last_name="Morgan",
        passport_number="P12345678",
        frequent_flyer_number="TSK0000001",
        tier="Gold",
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    f = db.query(Flight).filter(Flight.flight_number == "TSK101").first()
    if f:
        import uuid
        b = Booking(
            passenger_id=p.id,
            flight_id=f.id,
            seat_number="12A",
            seat_class="Business",
            status="Confirmed",
            boarding_pass_code=str(uuid.uuid4()).replace("-", "").upper()[:10],
        )
        db.add(b)
        db.commit()

    print("Demo passenger created — email: demo@trustedsky.com  password: demo1234")
else:
    print("Demo passenger already exists")

print("Seed complete.")
db.close()
