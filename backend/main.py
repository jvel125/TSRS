from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from config import settings
from database import engine, Base
from routers import auth, passengers, flights, biometrics, access

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="Biometric-accelerated airport experience for frequent flyers",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,        prefix="/api/v1")
app.include_router(passengers.router,  prefix="/api/v1")
app.include_router(flights.router,     prefix="/api/v1")
app.include_router(biometrics.router,  prefix="/api/v1")
app.include_router(access.router,      prefix="/api/v1")

# Serve frontend from /frontend directory when running locally
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": settings.app_name}
