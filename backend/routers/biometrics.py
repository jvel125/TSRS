import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import numpy as np

from database import get_db
from models import Passenger, AccessLog
from schemas import FaceEnrollRequest, FaceVerifyRequest, FaceVerifyResponse
from routers.passengers import get_current_passenger
from config import settings

router = APIRouter(prefix="/biometrics", tags=["biometrics"])


def _euclidean(a: list, b: list) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    return float(np.linalg.norm(va - vb))


def _distance_to_confidence(distance: float, threshold: float) -> float:
    """Map Euclidean distance to a 0–1 confidence score."""
    if distance >= threshold * 2:
        return 0.0
    return max(0.0, 1.0 - (distance / threshold))


@router.post("/enroll", status_code=200)
def enroll_face(
    body: FaceEnrollRequest,
    request: Request,
    passenger: Passenger = Depends(get_current_passenger),
    db: Session = Depends(get_db),
):
    if len(body.descriptor) != 128:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Descriptor must be 128-dimensional")

    passenger.face_descriptor = json.dumps(body.descriptor)
    passenger.face_enrolled_at = datetime.utcnow()
    db.add(AccessLog(
        passenger_id=passenger.id,
        event_type="ENROLL",
        status="SUCCESS",
        ip_address=request.client.host if request.client else None,
    ))
    db.commit()
    return {"message": "Face enrolled successfully", "enrolled_at": passenger.face_enrolled_at}


@router.post("/verify", response_model=FaceVerifyResponse)
def verify_face(body: FaceVerifyRequest, request: Request, db: Session = Depends(get_db)):
    """Identify a passenger by face against all enrolled passengers."""
    if len(body.descriptor) != 128:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Descriptor must be 128-dimensional")

    enrolled = db.query(Passenger).filter(Passenger.face_descriptor.isnot(None)).all()
    if not enrolled:
        return FaceVerifyResponse(
            matched=False, passenger_id=None, frequent_flyer_number=None,
            first_name=None, last_name=None, tier=None, confidence=0.0, distance=999.0,
        )

    best_passenger = None
    best_distance = float("inf")

    for p in enrolled:
        stored = json.loads(p.face_descriptor)
        dist = _euclidean(body.descriptor, stored)
        if dist < best_distance:
            best_distance = dist
            best_passenger = p

    matched = best_distance < settings.face_match_threshold
    confidence = _distance_to_confidence(best_distance, settings.face_match_threshold)

    db.add(AccessLog(
        passenger_id=best_passenger.id if matched else None,
        event_type="FACE_VERIFY",
        status="SUCCESS" if matched else "FAILED",
        confidence=confidence,
        ip_address=request.client.host if request.client else None,
    ))
    db.commit()

    if not matched:
        return FaceVerifyResponse(
            matched=False, passenger_id=None, frequent_flyer_number=None,
            first_name=None, last_name=None, tier=None, confidence=confidence, distance=best_distance,
        )

    return FaceVerifyResponse(
        matched=True,
        passenger_id=best_passenger.id,
        frequent_flyer_number=best_passenger.frequent_flyer_number,
        first_name=best_passenger.first_name,
        last_name=best_passenger.last_name,
        tier=best_passenger.tier,
        confidence=confidence,
        distance=best_distance,
    )


@router.delete("/enroll", status_code=200)
def revoke_face(
    passenger: Passenger = Depends(get_current_passenger),
    db: Session = Depends(get_db),
):
    passenger.face_descriptor = None
    passenger.face_enrolled_at = None
    db.commit()
    return {"message": "Face data revoked"}
