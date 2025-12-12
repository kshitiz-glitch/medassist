"""
Doctors Router
CRUD operations for doctor management.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Doctor, User, UserRole
from app.schemas import DoctorResponse, DoctorUpdate, DoctorWithAvailability
from app.routers.auth import get_current_active_user, require_role


router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("/", response_model=List[DoctorResponse])
async def list_doctors(
    specialty: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List all doctors.
    Optionally filter by specialty.
    """
    query = select(Doctor)
    
    if specialty:
        query = query.where(Doctor.specialty.ilike(f"%{specialty}%"))
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    doctors = result.scalars().all()
    
    return [DoctorResponse.model_validate(d) for d in doctors]


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(
    doctor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific doctor by ID."""
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    return DoctorResponse.model_validate(doctor)


@router.get("/search/{name}")
async def search_doctors(
    name: str,
    db: AsyncSession = Depends(get_db)
):
    """Search doctors by name (partial match)."""
    result = await db.execute(
        select(Doctor).where(Doctor.name.ilike(f"%{name}%"))
    )
    doctors = result.scalars().all()
    
    return [
        {
            "id": str(d.id),
            "name": d.name,
            "specialty": d.specialty,
            "consultation_duration": d.consultation_duration
        }
        for d in doctors
    ]


@router.get("/{doctor_id}/availability")
async def get_doctor_availability(
    doctor_id: uuid.UUID,
    date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a doctor's availability.
    If date is provided, returns available slots for that date.
    Otherwise, returns the general availability pattern.
    """
    from datetime import datetime, timedelta
    from app.models import Appointment, AppointmentStatus
    from sqlalchemy import and_
    
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    if not date:
        # Return general availability pattern
        return {
            "doctor_id": str(doctor.id),
            "doctor_name": doctor.name,
            "available_slots": doctor.available_slots,
            "consultation_duration": doctor.consultation_duration
        }
    
    # Parse the date
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    day_name = target_date.strftime("%A").lower()
    day_slots = doctor.available_slots.get(day_name, [])
    
    if not day_slots:
        return {
            "doctor_id": str(doctor.id),
            "doctor_name": doctor.name,
            "date": date,
            "day": day_name.capitalize(),
            "available_slots": [],
            "message": f"Dr. {doctor.name} is not available on {day_name}s"
        }
    
    # Get existing appointments
    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = datetime.combine(target_date, datetime.max.time())
    
    existing_appts = await db.execute(
        select(Appointment).where(
            and_(
                Appointment.doctor_id == doctor.id,
                Appointment.scheduled_time >= day_start,
                Appointment.scheduled_time <= day_end,
                Appointment.status.in_([
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.RESCHEDULED
                ])
            )
        )
    )
    booked_times = [a.scheduled_time for a in existing_appts.scalars().all()]
    
    # Generate available slots
    available_slots = []
    for slot in day_slots:
        start_time = datetime.strptime(slot["start"], "%H:%M").time()
        end_time = datetime.strptime(slot["end"], "%H:%M").time()
        
        current_time = datetime.combine(target_date, start_time)
        slot_end = datetime.combine(target_date, end_time)
        
        while current_time + timedelta(minutes=doctor.consultation_duration) <= slot_end:
            is_booked = current_time in booked_times
            available_slots.append({
                "time": current_time.strftime("%I:%M %p"),
                "datetime": current_time.isoformat(),
                "available": not is_booked
            })
            current_time += timedelta(minutes=doctor.consultation_duration)
    
    return {
        "doctor_id": str(doctor.id),
        "doctor_name": doctor.name,
        "specialty": doctor.specialty,
        "date": date,
        "day": day_name.capitalize(),
        "available_slots": available_slots,
        "consultation_duration": doctor.consultation_duration
    }


@router.put("/{doctor_id}", response_model=DoctorResponse)
async def update_doctor(
    doctor_id: uuid.UUID,
    update_data: DoctorUpdate,
    current_user: User = Depends(require_role(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db)
):
    """Update doctor information (only the doctor can update their own profile)."""
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Verify ownership
    if doctor.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(doctor, key, value)
    
    await db.commit()
    await db.refresh(doctor)
    
    return DoctorResponse.model_validate(doctor)


@router.get("/{doctor_id}/stats")
async def get_doctor_stats(
    doctor_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics for a doctor (only accessible by the doctor)."""
    from datetime import datetime, timedelta
    from sqlalchemy import func, and_
    from app.models import Appointment, AppointmentStatus
    
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Verify ownership
    if doctor.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view these stats")
    
    now = datetime.now()
    today_start = datetime.combine(now.date(), datetime.min.time())
    today_end = datetime.combine(now.date(), datetime.max.time())
    yesterday = now.date() - timedelta(days=1)
    tomorrow = now.date() + timedelta(days=1)
    
    # Today's appointments
    result = await db.execute(
        select(func.count(Appointment.id)).where(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.scheduled_time >= today_start,
                Appointment.scheduled_time <= today_end
            )
        )
    )
    today_count = result.scalar()
    
    # Yesterday's completed
    result = await db.execute(
        select(func.count(Appointment.id)).where(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.scheduled_time >= datetime.combine(yesterday, datetime.min.time()),
                Appointment.scheduled_time <= datetime.combine(yesterday, datetime.max.time()),
                Appointment.status == AppointmentStatus.COMPLETED
            )
        )
    )
    yesterday_count = result.scalar()
    
    # Tomorrow's appointments
    result = await db.execute(
        select(func.count(Appointment.id)).where(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.scheduled_time >= datetime.combine(tomorrow, datetime.min.time()),
                Appointment.scheduled_time <= datetime.combine(tomorrow, datetime.max.time()),
                Appointment.status == AppointmentStatus.SCHEDULED
            )
        )
    )
    tomorrow_count = result.scalar()
    
    # Total patients
    result = await db.execute(
        select(func.count(func.distinct(Appointment.patient_id))).where(
            Appointment.doctor_id == doctor_id
        )
    )
    total_patients = result.scalar()
    
    return {
        "doctor_id": str(doctor_id),
        "doctor_name": doctor.name,
        "today_appointments": today_count,
        "yesterday_visits": yesterday_count,
        "tomorrow_appointments": tomorrow_count,
        "total_patients": total_patients
    }
