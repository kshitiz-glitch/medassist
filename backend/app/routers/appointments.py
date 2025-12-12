"""
Appointments Router
CRUD operations for appointment management.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    Appointment, AppointmentStatus, Doctor, Patient, 
    User, UserRole
)
from app.schemas import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    AppointmentWithDetails
)
from app.routers.auth import get_current_active_user, require_role
from app.services.calendar import GoogleCalendarService
from app.services.email import EmailService


router = APIRouter(prefix="/appointments", tags=["Appointments"])

calendar_service = GoogleCalendarService()
email_service = EmailService()


@router.post("/", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new appointment.
    Patients can only book for themselves.
    """
    # Verify doctor exists
    result = await db.execute(
        select(Doctor).where(Doctor.id == appointment_data.doctor_id)
    )
    doctor = result.scalar_one_or_none()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Get patient ID
    if current_user.role == UserRole.PATIENT:
        result = await db.execute(
            select(Patient).where(Patient.user_id == current_user.id)
        )
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient profile not found")
        
        patient_id = patient.id
    else:
        # Doctors/admins can specify patient_id
        if not appointment_data.patient_id:
            raise HTTPException(status_code=400, detail="Patient ID required")
        patient_id = appointment_data.patient_id
        
        result = await db.execute(
            select(Patient).where(Patient.id == patient_id)
        )
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
    
    # Check if slot is available
    existing = await db.execute(
        select(Appointment).where(
            and_(
                Appointment.doctor_id == doctor.id,
                Appointment.scheduled_time == appointment_data.scheduled_time,
                Appointment.status.in_([
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.RESCHEDULED
                ])
            )
        )
    )
    
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail="This time slot is already booked"
        )
    
    # Create appointment
    appointment = Appointment(
        doctor_id=doctor.id,
        patient_id=patient_id,
        scheduled_time=appointment_data.scheduled_time,
        duration_minutes=appointment_data.duration_minutes,
        symptoms=appointment_data.symptoms,
        status=AppointmentStatus.SCHEDULED
    )
    
    db.add(appointment)
    await db.flush()
    
    # Create calendar event
    try:
        user = await db.get(User, patient.user_id)
        event_id = await calendar_service.create_event(
            summary=f"Appointment: {patient.name} with Dr. {doctor.name}",
            start_time=appointment.scheduled_time,
            duration_minutes=doctor.consultation_duration,
            description=f"Symptoms: {appointment.symptoms}" if appointment.symptoms else "",
            attendees=[user.email] if user else []
        )
        appointment.google_calendar_event_id = event_id
    except Exception as e:
        print(f"Calendar error: {e}")
    
    # Send confirmation email
    try:
        user = await db.get(User, patient.user_id)
        if user:
            await email_service.send_appointment_confirmation(
                to_email=user.email,
                patient_name=patient.name,
                doctor_name=doctor.name,
                appointment_time=appointment.scheduled_time,
                symptoms=appointment.symptoms or ""
            )
            appointment.confirmation_sent = True
    except Exception as e:
        print(f"Email error: {e}")
    
    await db.commit()
    await db.refresh(appointment)
    
    return AppointmentResponse.model_validate(appointment)


@router.get("/", response_model=List[AppointmentResponse])
async def list_appointments(
    status: Optional[str] = None,
    date: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List appointments.
    Patients see their own appointments.
    Doctors see appointments at their practice.
    """
    query = select(Appointment)
    
    if current_user.role == UserRole.PATIENT:
        # Get patient's appointments
        result = await db.execute(
            select(Patient).where(Patient.user_id == current_user.id)
        )
        patient = result.scalar_one_or_none()
        
        if patient:
            query = query.where(Appointment.patient_id == patient.id)
    
    elif current_user.role == UserRole.DOCTOR:
        # Get doctor's appointments
        result = await db.execute(
            select(Doctor).where(Doctor.user_id == current_user.id)
        )
        doctor = result.scalar_one_or_none()
        
        if doctor:
            query = query.where(Appointment.doctor_id == doctor.id)
    
    if status:
        query = query.where(Appointment.status == AppointmentStatus(status))
    
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            day_start = datetime.combine(target_date, datetime.min.time())
            day_end = datetime.combine(target_date, datetime.max.time())
            query = query.where(
                and_(
                    Appointment.scheduled_time >= day_start,
                    Appointment.scheduled_time <= day_end
                )
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    
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


@router.get("/{appointment_id}", response_model=AppointmentWithDetails)
async def get_appointment(
    appointment_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific appointment with full details."""
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Verify access
    if current_user.role == UserRole.PATIENT:
        patient_result = await db.execute(
            select(Patient).where(Patient.user_id == current_user.id)
        )
        patient = patient_result.scalar_one_or_none()
        
        if not patient or appointment.patient_id != patient.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    elif current_user.role == UserRole.DOCTOR:
        doctor_result = await db.execute(
            select(Doctor).where(Doctor.user_id == current_user.id)
        )
        doctor = doctor_result.scalar_one_or_none()
        
        if not doctor or appointment.doctor_id != doctor.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get related data
    from app.schemas import DoctorResponse, PatientResponse
    
    doctor = await db.get(Doctor, appointment.doctor_id)
    patient = await db.get(Patient, appointment.patient_id)
    
    response = AppointmentWithDetails.model_validate(appointment)
    if doctor:
        response.doctor = DoctorResponse.model_validate(doctor)
    if patient:
        response.patient = PatientResponse.model_validate(patient)
    
    return response


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: uuid.UUID,
    update_data: AppointmentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an appointment."""
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Handle rescheduling
    if "scheduled_time" in update_dict and update_dict["scheduled_time"] != appointment.scheduled_time:
        old_time = appointment.scheduled_time
        new_time = update_dict["scheduled_time"]
        
        # Update calendar event
        if appointment.google_calendar_event_id:
            try:
                await calendar_service.update_event(
                    appointment.google_calendar_event_id,
                    new_time
                )
            except Exception as e:
                print(f"Calendar update error: {e}")
        
        # Notify patient
        patient = await db.get(Patient, appointment.patient_id)
        if patient:
            user = await db.get(User, patient.user_id)
            if user:
                await email_service.send_reschedule_notification(
                    to_email=user.email,
                    patient_name=patient.name,
                    old_time=old_time,
                    new_time=new_time
                )
        
        update_dict["status"] = AppointmentStatus.RESCHEDULED
    
    for key, value in update_dict.items():
        setattr(appointment, key, value)
    
    await db.commit()
    await db.refresh(appointment)
    
    return AppointmentResponse.model_validate(appointment)


@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: uuid.UUID,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel an appointment."""
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Verify access
    if current_user.role == UserRole.PATIENT:
        patient_result = await db.execute(
            select(Patient).where(Patient.user_id == current_user.id)
        )
        patient = patient_result.scalar_one_or_none()
        
        if not patient or appointment.patient_id != patient.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    appointment.status = AppointmentStatus.CANCELLED
    if reason:
        appointment.notes = f"Cancelled: {reason}"
    
    # Delete calendar event
    if appointment.google_calendar_event_id:
        try:
            await calendar_service.delete_event(appointment.google_calendar_event_id)
        except Exception as e:
            print(f"Calendar deletion error: {e}")
    
    # Notify patient
    patient = await db.get(Patient, appointment.patient_id)
    if patient:
        user = await db.get(User, patient.user_id)
        if user:
            await email_service.send_cancellation_notification(
                to_email=user.email,
                patient_name=patient.name,
                appointment_time=appointment.scheduled_time,
                reason=reason or ""
            )
    
    await db.commit()
    
    return {"message": "Appointment cancelled successfully"}


@router.post("/{appointment_id}/complete")
async def complete_appointment(
    appointment_id: uuid.UUID,
    diagnosis: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db)
):
    """Mark an appointment as completed (doctors only)."""
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Verify doctor owns this appointment
    doctor_result = await db.execute(
        select(Doctor).where(Doctor.user_id == current_user.id)
    )
    doctor = doctor_result.scalar_one_or_none()
    
    if not doctor or appointment.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    appointment.status = AppointmentStatus.COMPLETED
    if diagnosis:
        appointment.diagnosis = diagnosis
    if notes:
        appointment.notes = notes
    
    await db.commit()
    
    return {"message": "Appointment marked as completed"}
