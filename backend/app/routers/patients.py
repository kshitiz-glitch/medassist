"""
Patients Router
CRUD operations for patient management.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Patient, User, UserRole, Appointment
from app.schemas import PatientResponse, PatientUpdate, AppointmentResponse
from app.routers.auth import get_current_active_user, require_role


router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("/me", response_model=PatientResponse)
async def get_current_patient(
    current_user: User = Depends(require_role(UserRole.PATIENT)),
    db: AsyncSession = Depends(get_db)
):
    """Get current patient's profile."""
    result = await db.execute(
        select(Patient).where(Patient.user_id == current_user.id)
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    return PatientResponse.model_validate(patient)


@router.put("/me", response_model=PatientResponse)
async def update_current_patient(
    update_data: PatientUpdate,
    current_user: User = Depends(require_role(UserRole.PATIENT)),
    db: AsyncSession = Depends(get_db)
):
    """Update current patient's profile."""
    result = await db.execute(
        select(Patient).where(Patient.user_id == current_user.id)
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(patient, key, value)
    
    await db.commit()
    await db.refresh(patient)
    
    return PatientResponse.model_validate(patient)


@router.get("/me/appointments", response_model=List[AppointmentResponse])
async def get_patient_appointments(
    status: Optional[str] = None,
    upcoming_only: bool = False,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=100),
    current_user: User = Depends(require_role(UserRole.PATIENT)),
    db: AsyncSession = Depends(get_db)
):
    """Get current patient's appointments."""
    from datetime import datetime
    from app.models import AppointmentStatus, Doctor
    
    # Get patient
    result = await db.execute(
        select(Patient).where(Patient.user_id == current_user.id)
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    # Build query
    query = select(Appointment).where(Appointment.patient_id == patient.id)
    
    if status:
        query = query.where(Appointment.status == AppointmentStatus(status))
    
    if upcoming_only:
        query = query.where(Appointment.scheduled_time >= datetime.now())
    
    query = query.order_by(Appointment.scheduled_time.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    appointments = result.scalars().all()
    
    # Build response with doctor names
    responses = []
    for a in appointments:
        response = AppointmentResponse.model_validate(a)
        # Fetch doctor name
        doctor = await db.get(Doctor, a.doctor_id)
        if doctor:
            response.doctor_name = doctor.name
        responses.append(response)
    
    return responses


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific patient by ID (doctors only)."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return PatientResponse.model_validate(patient)


@router.get("/{patient_id}/history")
async def get_patient_history(
    patient_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db)
):
    """Get a patient's appointment history (doctors only)."""
    from app.models import Doctor
    
    # Get doctor
    result = await db.execute(
        select(Doctor).where(Doctor.user_id == current_user.id)
    )
    doctor = result.scalar_one_or_none()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    
    # Get patient
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get appointments between this doctor and patient
    result = await db.execute(
        select(Appointment).where(
            Appointment.patient_id == patient_id,
            Appointment.doctor_id == doctor.id
        ).order_by(Appointment.scheduled_time.desc())
    )
    appointments = result.scalars().all()
    
    return {
        "patient": PatientResponse.model_validate(patient),
        "appointments": [
            {
                "id": str(a.id),
                "scheduled_time": a.scheduled_time.isoformat(),
                "status": a.status.value,
                "symptoms": a.symptoms,
                "diagnosis": a.diagnosis,
                "notes": a.notes
            }
            for a in appointments
        ],
        "total_visits": len(appointments)
    }
