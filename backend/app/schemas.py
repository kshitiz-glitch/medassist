"""
Pydantic Schemas
Request/Response models for API validation.
"""

import uuid
from datetime import datetime, date
from typing import Optional, List, Any
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


# ============== Auth Schemas ==============

class UserRole(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=2)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============== Doctor Schemas ==============

class TimeSlot(BaseModel):
    start: str  # "09:00"
    end: str    # "12:00"


class DoctorBase(BaseModel):
    name: str
    specialty: str
    phone: Optional[str] = None
    bio: Optional[str] = None
    consultation_duration: int = 30


class DoctorCreate(DoctorBase):
    available_slots: dict = Field(
        default_factory=dict,
        description="Availability pattern by day of week"
    )


class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    specialty: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    available_slots: Optional[dict] = None
    consultation_duration: Optional[int] = None


class DoctorResponse(DoctorBase):
    id: uuid.UUID
    user_id: uuid.UUID
    available_slots: dict
    created_at: datetime
    
    class Config:
        from_attributes = True


class DoctorWithAvailability(DoctorResponse):
    available_times: List[datetime] = []


# ============== Patient Schemas ==============

class PatientBase(BaseModel):
    name: str
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


class PatientCreate(PatientBase):
    medical_history: dict = Field(default_factory=dict)


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    medical_history: Optional[dict] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


class PatientResponse(PatientBase):
    id: uuid.UUID
    user_id: uuid.UUID
    medical_history: dict
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============== Appointment Schemas ==============

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class AppointmentBase(BaseModel):
    scheduled_time: datetime
    duration_minutes: int = 30
    symptoms: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    doctor_id: uuid.UUID
    patient_id: Optional[uuid.UUID] = None  # Will be set from current user if patient


class AppointmentUpdate(BaseModel):
    scheduled_time: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    symptoms: Optional[str] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    id: uuid.UUID
    doctor_id: uuid.UUID
    patient_id: uuid.UUID
    status: AppointmentStatus
    diagnosis: Optional[str]
    notes: Optional[str]
    google_calendar_event_id: Optional[str]
    confirmation_sent: bool
    created_at: datetime
    doctor_name: Optional[str] = None  # Added for frontend display
    
    class Config:
        from_attributes = True


class AppointmentWithDetails(AppointmentResponse):
    doctor: Optional[DoctorResponse] = None
    patient: Optional[PatientResponse] = None


# ============== Chat Schemas ==============

class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    session_id: str
    tools_used: List[str] = []
    context: dict = {}


class ConversationResponse(BaseModel):
    id: uuid.UUID
    session_id: str
    messages: List[ChatMessage]
    context: dict
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============== Notification Schemas ==============

class NotificationChannel(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    WHATSAPP = "whatsapp"
    IN_APP = "in_app"


class NotificationRequest(BaseModel):
    channel: NotificationChannel
    recipient_id: Optional[uuid.UUID] = None
    report_type: str = "daily_summary"


class NotificationResponse(BaseModel):
    success: bool
    channel: NotificationChannel
    message: str


# ============== Report Schemas ==============

class PatientStats(BaseModel):
    total_visits: int
    yesterday_visits: int
    today_appointments: int
    tomorrow_appointments: int
    symptoms_breakdown: dict = {}


class DoctorReport(BaseModel):
    doctor_id: uuid.UUID
    doctor_name: str
    report_date: datetime
    stats: PatientStats
    summary: str


# ============== Prompt History Schemas ==============

class PromptHistoryResponse(BaseModel):
    id: uuid.UUID
    session_id: str
    prompt: str
    response: str
    tools_used: List[str]
    success: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============== Availability Check Schemas ==============

class AvailabilityRequest(BaseModel):
    doctor_name: str
    date: str  # "2024-01-15" or "tomorrow"


class AvailabilitySlot(BaseModel):
    time: datetime
    available: bool


class AvailabilityResponse(BaseModel):
    doctor_name: str
    date: str
    slots: List[AvailabilitySlot]
