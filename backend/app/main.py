"""
Doctor Appointment Assistant - FastAPI Application
Main entry point for the backend server.
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.routers import auth, chat, doctors, patients, appointments


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 Starting Doctor Appointment Assistant...")
    await init_db()
    print("✅ Database initialized")
    
    # Seed demo data if database is empty
    await seed_demo_data()
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title="Doctor Appointment Assistant",
    description="""
    🏥 Smart Doctor Appointment and Reporting Assistant with MCP Integration
    
    ## Features
    - **Patient Appointment Scheduling**: Book appointments using natural language
    - **Doctor Reports**: Get summary reports via Slack, WhatsApp, or in-app
    - **Multi-turn Conversations**: Context-aware AI assistant
    - **Calendar Integration**: Google Calendar sync
    - **Email Notifications**: Appointment confirmations and updates
    
    ## Roles
    - **Patient**: Book, reschedule, cancel appointments
    - **Doctor**: View schedules, patient stats, receive reports
    
    ## MCP Tools
    The AI agent can use these tools:
    - `check_doctor_availability`: Check when a doctor is available
    - `schedule_appointment`: Book an appointment
    - `get_patient_statistics`: Get patient visit stats
    - `send_doctor_report`: Send reports via notification channels
    - `reschedule_appointment`: Auto-reschedule when needed
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(doctors.router, prefix="/api")
app.include_router(patients.router, prefix="/api")
app.include_router(appointments.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "🏥 Doctor Appointment Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "doctor-appointment-assistant"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc) if settings.debug else "Internal server error",
            "type": type(exc).__name__
        }
    )


async def seed_demo_data():
    """Seed demo data for testing."""
    from sqlalchemy import select
    from app.database import async_session_maker
    from app.models import User, Doctor, Patient, UserRole
    from app.routers.auth import get_password_hash
    
    async with async_session_maker() as session:
        # Check if we already have data
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            print("📊 Database already has data, skipping seed")
            return
        
        print("🌱 Seeding demo data...")
        
        # Create demo doctors
        demo_doctors = [
            {
                "email": "dr.ahuja@clinic.com",
                "password": "doctor123",
                "name": "Dr. Rahul Ahuja",
                "specialty": "General Medicine",
                "available_slots": {
                    "monday": [{"start": "09:00", "end": "12:00"}, {"start": "14:00", "end": "17:00"}],
                    "tuesday": [{"start": "09:00", "end": "12:00"}, {"start": "14:00", "end": "17:00"}],
                    "wednesday": [{"start": "09:00", "end": "12:00"}],
                    "thursday": [{"start": "09:00", "end": "12:00"}, {"start": "14:00", "end": "17:00"}],
                    "friday": [{"start": "09:00", "end": "12:00"}, {"start": "14:00", "end": "17:00"}]
                }
            },
            {
                "email": "dr.sharma@clinic.com",
                "password": "doctor123",
                "name": "Dr. Priya Sharma",
                "specialty": "Pediatrics",
                "available_slots": {
                    "monday": [{"start": "10:00", "end": "13:00"}, {"start": "15:00", "end": "18:00"}],
                    "tuesday": [{"start": "10:00", "end": "13:00"}],
                    "wednesday": [{"start": "10:00", "end": "13:00"}, {"start": "15:00", "end": "18:00"}],
                    "thursday": [{"start": "10:00", "end": "13:00"}, {"start": "15:00", "end": "18:00"}],
                    "friday": [{"start": "10:00", "end": "13:00"}]
                }
            },
            {
                "email": "dr.patel@clinic.com",
                "password": "doctor123",
                "name": "Dr. Amit Patel",
                "specialty": "Cardiology",
                "available_slots": {
                    "monday": [{"start": "08:00", "end": "11:00"}, {"start": "13:00", "end": "16:00"}],
                    "wednesday": [{"start": "08:00", "end": "11:00"}, {"start": "13:00", "end": "16:00"}],
                    "friday": [{"start": "08:00", "end": "11:00"}, {"start": "13:00", "end": "16:00"}]
                }
            }
        ]
        
        for doc in demo_doctors:
            user = User(
                email=doc["email"],
                hashed_password=get_password_hash(doc["password"]),
                role=UserRole.DOCTOR
            )
            session.add(user)
            await session.flush()
            
            doctor = Doctor(
                user_id=user.id,
                name=doc["name"],
                specialty=doc["specialty"],
                available_slots=doc["available_slots"],
                consultation_duration=30
            )
            session.add(doctor)
        
        # Create demo patient
        patient_user = User(
            email="patient@example.com",
            hashed_password=get_password_hash("patient123"),
            role=UserRole.PATIENT
        )
        session.add(patient_user)
        await session.flush()
        
        patient = Patient(
            user_id=patient_user.id,
            name="Demo Patient",
            phone="+91-9876543210"
        )
        session.add(patient)
        
        await session.commit()
        print("✅ Demo data seeded successfully!")
        print("   📧 Demo Patient: patient@example.com / patient123")
        print("   👨‍⚕️ Demo Doctors:")
        print("      - dr.ahuja@clinic.com / doctor123 (General Medicine)")
        print("      - dr.sharma@clinic.com / doctor123 (Pediatrics)")
        print("      - dr.patel@clinic.com / doctor123 (Cardiology)")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
