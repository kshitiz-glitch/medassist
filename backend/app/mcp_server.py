"""
MCP (Model Context Protocol) Server Implementation
Exposes tools, resources, and prompts for AI agent orchestration.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Any
import json

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Doctor, Patient, Appointment, AppointmentStatus
from app.database import async_session_maker
from app.services.calendar import GoogleCalendarService
from app.services.email import EmailService
from app.services.notification import NotificationService


class MCPTools:
    """
    MCP Tools implementation for the Doctor Appointment System.
    These tools can be called by the AI agent to perform actions.
    """
    
    def __init__(self):
        self.calendar_service = GoogleCalendarService()
        self.email_service = EmailService()
        self.notification_service = NotificationService()
    
    @staticmethod
    def get_tool_definitions() -> List[dict]:
        """Return OpenAI-compatible tool definitions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "check_doctor_availability",
                    "description": "Check available time slots for a doctor on a specific date. Use this when a patient wants to know when a doctor is available.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doctor_name": {
                                "type": "string",
                                "description": "The name of the doctor (partial match supported)"
                            },
                            "date": {
                                "type": "string",
                                "description": "The date to check availability for (e.g., '2024-01-15', 'tomorrow', 'next monday')"
                            }
                        },
                        "required": ["doctor_name", "date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "schedule_appointment",
                    "description": "Book an appointment with a doctor. Use this after confirming the patient wants a specific time slot.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doctor_name": {
                                "type": "string",
                                "description": "The name of the doctor"
                            },
                            "patient_email": {
                                "type": "string",
                                "description": "The patient's email address"
                            },
                            "appointment_datetime": {
                                "type": "string",
                                "description": "The date and time for the appointment in ISO format"
                            },
                            "symptoms": {
                                "type": "string",
                                "description": "Description of symptoms or reason for visit"
                            }
                        },
                        "required": ["doctor_name", "patient_email", "appointment_datetime"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_patient_statistics",
                    "description": "Get patient visit statistics for a doctor. Use this when a doctor asks about patient counts, visits, or appointments.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doctor_id": {
                                "type": "string",
                                "description": "The doctor's UUID"
                            },
                            "query_type": {
                                "type": "string",
                                "enum": ["yesterday", "today", "tomorrow", "this_week", "by_symptom"],
                                "description": "Type of statistics to retrieve"
                            },
                            "symptom": {
                                "type": "string",
                                "description": "Specific symptom to filter by (only for by_symptom query)"
                            }
                        },
                        "required": ["doctor_id", "query_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_doctor_report",
                    "description": "Send a summary report to the doctor via their preferred notification channel.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doctor_id": {
                                "type": "string",
                                "description": "The doctor's UUID"
                            },
                            "report_content": {
                                "type": "string",
                                "description": "The formatted report content to send"
                            },
                            "channel": {
                                "type": "string",
                                "enum": ["slack", "whatsapp", "in_app"],
                                "description": "Notification channel to use"
                            }
                        },
                        "required": ["doctor_id", "report_content", "channel"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "reschedule_appointment",
                    "description": "Reschedule an existing appointment to a new time. Use when a doctor is unavailable and auto-rescheduling is needed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "appointment_id": {
                                "type": "string",
                                "description": "The appointment UUID to reschedule"
                            },
                            "new_datetime": {
                                "type": "string",
                                "description": "The new date and time in ISO format"
                            },
                            "notify_patient": {
                                "type": "boolean",
                                "description": "Whether to send notification to patient"
                            }
                        },
                        "required": ["appointment_id", "new_datetime"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_all_doctors",
                    "description": "Get a list of all available doctors. Use when the patient doesn't specify a doctor name.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_appointment_details",
                    "description": "Get details of a specific appointment or list of appointments.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "appointment_id": {
                                "type": "string",
                                "description": "Specific appointment UUID"
                            },
                            "patient_email": {
                                "type": "string",
                                "description": "Get all appointments for this patient email"
                            },
                            "doctor_id": {
                                "type": "string",
                                "description": "Get all appointments for this doctor"
                            },
                            "date_range": {
                                "type": "string",
                                "enum": ["today", "tomorrow", "this_week", "next_week"],
                                "description": "Filter by date range"
                            }
                        }
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "cancel_appointment",
                    "description": "Cancel an existing appointment.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "appointment_id": {
                                "type": "string",
                                "description": "The appointment UUID to cancel"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for cancellation"
                            },
                            "notify_patient": {
                                "type": "boolean",
                                "description": "Whether to notify the patient"
                            }
                        },
                        "required": ["appointment_id"]
                    }
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, arguments: dict) -> dict:
        """Execute a tool by name with given arguments."""
        tool_map = {
            "check_doctor_availability": self._check_availability,
            "schedule_appointment": self._schedule_appointment,
            "get_patient_statistics": self._get_patient_stats,
            "send_doctor_report": self._send_report,
            "reschedule_appointment": self._reschedule_appointment,
            "get_all_doctors": self._get_all_doctors,
            "get_appointment_details": self._get_appointment_details,
            "cancel_appointment": self._cancel_appointment,
        }
        
        if tool_name not in tool_map:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            result = await tool_map[tool_name](**arguments)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def _check_availability(self, doctor_name: str, date: str) -> dict:
        """Check doctor availability for a given date."""
        async with async_session_maker() as session:
            # Parse the date
            target_date = self._parse_date(date)
            
            # Find doctor by name (partial match)
            result = await session.execute(
                select(Doctor).where(Doctor.name.ilike(f"%{doctor_name}%"))
            )
            doctor = result.scalar_one_or_none()
            
            if not doctor:
                return {
                    "success": False,
                    "message": f"No doctor found matching '{doctor_name}'",
                    "available_slots": []
                }
            
            # Get day of week
            day_name = target_date.strftime("%A").lower()
            
            # Get doctor's availability pattern for that day
            day_slots = doctor.available_slots.get(day_name, [])
            
            if not day_slots:
                return {
                    "success": True,
                    "doctor_name": doctor.name,
                    "date": target_date.strftime("%Y-%m-%d"),
                    "message": f"Dr. {doctor.name} is not available on {day_name}s",
                    "available_slots": []
                }
            
            # Get existing appointments for that day
            day_start = datetime.combine(target_date, datetime.min.time())
            day_end = datetime.combine(target_date, datetime.max.time())
            
            existing_appts = await session.execute(
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
            
            # Generate available time slots
            available_slots = []
            for slot in day_slots:
                start_time = datetime.strptime(slot["start"], "%H:%M").time()
                end_time = datetime.strptime(slot["end"], "%H:%M").time()
                
                current_time = datetime.combine(target_date, start_time)
                slot_end = datetime.combine(target_date, end_time)
                
                while current_time + timedelta(minutes=doctor.consultation_duration) <= slot_end:
                    if current_time not in booked_times:
                        available_slots.append(current_time.strftime("%I:%M %p"))
                    current_time += timedelta(minutes=doctor.consultation_duration)
            
            return {
                "success": True,
                "doctor_name": doctor.name,
                "doctor_id": str(doctor.id),
                "specialty": doctor.specialty,
                "date": target_date.strftime("%Y-%m-%d"),
                "day": day_name.capitalize(),
                "available_slots": available_slots,
                "consultation_duration": doctor.consultation_duration,
                "message": f"Dr. {doctor.name} has {len(available_slots)} available slots on {target_date.strftime('%B %d, %Y')}"
            }
    
    async def _schedule_appointment(
        self, 
        doctor_name: str, 
        patient_email: str, 
        appointment_datetime: str,
        symptoms: str = ""
    ) -> dict:
        """Schedule a new appointment."""
        async with async_session_maker() as session:
            # Find doctor
            result = await session.execute(
                select(Doctor).where(Doctor.name.ilike(f"%{doctor_name}%"))
            )
            doctor = result.scalar_one_or_none()
            
            if not doctor:
                return {
                    "success": False,
                    "message": f"No doctor found matching '{doctor_name}'"
                }
            
            # Find patient by email
            from app.models import User, UserRole
            
            user_result = await session.execute(
                select(User).where(
                    and_(
                        User.email == patient_email,
                        User.role == UserRole.PATIENT
                    )
                )
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return {
                    "success": False,
                    "message": f"No patient found with email '{patient_email}'. Please register first."
                }
            
            patient_result = await session.execute(
                select(Patient).where(Patient.user_id == user.id)
            )
            patient = patient_result.scalar_one_or_none()
            
            if not patient:
                return {
                    "success": False,
                    "message": "Patient profile not found. Please complete your profile."
                }
            
            # Parse appointment time
            try:
                appt_time = datetime.fromisoformat(appointment_datetime.replace("Z", "+00:00"))
            except ValueError:
                # Try parsing natural language time
                appt_time = self._parse_datetime(appointment_datetime)
            
            # Check if slot is still available
            existing = await session.execute(
                select(Appointment).where(
                    and_(
                        Appointment.doctor_id == doctor.id,
                        Appointment.scheduled_time == appt_time,
                        Appointment.status == AppointmentStatus.SCHEDULED
                    )
                )
            )
            
            if existing.scalar_one_or_none():
                return {
                    "success": False,
                    "message": f"Sorry, the {appt_time.strftime('%I:%M %p')} slot is no longer available. Please choose another time."
                }
            
            # Create appointment
            appointment = Appointment(
                doctor_id=doctor.id,
                patient_id=patient.id,
                scheduled_time=appt_time,
                duration_minutes=doctor.consultation_duration,
                symptoms=symptoms,
                status=AppointmentStatus.SCHEDULED
            )
            
            session.add(appointment)
            await session.commit()
            await session.refresh(appointment)
            
            # Create Google Calendar event
            calendar_event_id = None
            try:
                calendar_event_id = await self.calendar_service.create_event(
                    summary=f"Appointment: {patient.name} with Dr. {doctor.name}",
                    start_time=appt_time,
                    duration_minutes=doctor.consultation_duration,
                    description=f"Symptoms: {symptoms}" if symptoms else "Regular checkup",
                    attendees=[patient_email]
                )
                appointment.google_calendar_event_id = calendar_event_id
                await session.commit()
            except Exception as e:
                print(f"Calendar integration error: {e}")
            
            # Send confirmation email
            try:
                await self.email_service.send_appointment_confirmation(
                    to_email=patient_email,
                    patient_name=patient.name,
                    doctor_name=doctor.name,
                    appointment_time=appt_time,
                    symptoms=symptoms
                )
                appointment.confirmation_sent = True
                await session.commit()
            except Exception as e:
                print(f"Email error: {e}")
            
            return {
                "success": True,
                "appointment_id": str(appointment.id),
                "message": f"✅ Appointment successfully booked with Dr. {doctor.name} on {appt_time.strftime('%B %d, %Y at %I:%M %p')}",
                "details": {
                    "doctor": doctor.name,
                    "specialty": doctor.specialty,
                    "patient": patient.name,
                    "time": appt_time.isoformat(),
                    "duration": f"{doctor.consultation_duration} minutes",
                    "calendar_event": calendar_event_id is not None,
                    "email_sent": appointment.confirmation_sent
                }
            }
    
    async def _get_patient_stats(
        self, 
        doctor_id: str, 
        query_type: str,
        symptom: Optional[str] = None
    ) -> dict:
        """Get patient statistics for a doctor."""
        async with async_session_maker() as session:
            doctor_uuid = uuid.UUID(doctor_id)
            
            # Get doctor info
            doctor_result = await session.execute(
                select(Doctor).where(Doctor.id == doctor_uuid)
            )
            doctor = doctor_result.scalar_one_or_none()
            
            if not doctor:
                return {"error": "Doctor not found"}
            
            now = datetime.now()
            today_start = datetime.combine(now.date(), datetime.min.time())
            today_end = datetime.combine(now.date(), datetime.max.time())
            
            if query_type == "yesterday":
                yesterday = now.date() - timedelta(days=1)
                start = datetime.combine(yesterday, datetime.min.time())
                end = datetime.combine(yesterday, datetime.max.time())
                
                result = await session.execute(
                    select(func.count(Appointment.id)).where(
                        and_(
                            Appointment.doctor_id == doctor_uuid,
                            Appointment.scheduled_time >= start,
                            Appointment.scheduled_time <= end,
                            Appointment.status == AppointmentStatus.COMPLETED
                        )
                    )
                )
                count = result.scalar()
                
                return {
                    "success": True,
                    "query": "yesterday's visits",
                    "count": count,
                    "message": f"You had {count} patient{'s' if count != 1 else ''} visit yesterday."
                }
            
            elif query_type == "today":
                result = await session.execute(
                    select(func.count(Appointment.id)).where(
                        and_(
                            Appointment.doctor_id == doctor_uuid,
                            Appointment.scheduled_time >= today_start,
                            Appointment.scheduled_time <= today_end,
                            Appointment.status.in_([
                                AppointmentStatus.SCHEDULED,
                                AppointmentStatus.COMPLETED
                            ])
                        )
                    )
                )
                count = result.scalar()
                
                return {
                    "success": True,
                    "query": "today's appointments",
                    "count": count,
                    "message": f"You have {count} appointment{'s' if count != 1 else ''} scheduled for today."
                }
            
            elif query_type == "tomorrow":
                tomorrow = now.date() + timedelta(days=1)
                start = datetime.combine(tomorrow, datetime.min.time())
                end = datetime.combine(tomorrow, datetime.max.time())
                
                result = await session.execute(
                    select(func.count(Appointment.id)).where(
                        and_(
                            Appointment.doctor_id == doctor_uuid,
                            Appointment.scheduled_time >= start,
                            Appointment.scheduled_time <= end,
                            Appointment.status == AppointmentStatus.SCHEDULED
                        )
                    )
                )
                count = result.scalar()
                
                return {
                    "success": True,
                    "query": "tomorrow's appointments",
                    "count": count,
                    "message": f"You have {count} appointment{'s' if count != 1 else ''} scheduled for tomorrow."
                }
            
            elif query_type == "this_week":
                week_start = now - timedelta(days=now.weekday())
                week_end = week_start + timedelta(days=6)
                
                result = await session.execute(
                    select(func.count(Appointment.id)).where(
                        and_(
                            Appointment.doctor_id == doctor_uuid,
                            Appointment.scheduled_time >= week_start,
                            Appointment.scheduled_time <= week_end
                        )
                    )
                )
                count = result.scalar()
                
                return {
                    "success": True,
                    "query": "this week's appointments",
                    "count": count,
                    "message": f"You have {count} appointment{'s' if count != 1 else ''} this week."
                }
            
            elif query_type == "by_symptom" and symptom:
                result = await session.execute(
                    select(func.count(Appointment.id)).where(
                        and_(
                            Appointment.doctor_id == doctor_uuid,
                            Appointment.symptoms.ilike(f"%{symptom}%")
                        )
                    )
                )
                count = result.scalar()
                
                return {
                    "success": True,
                    "query": f"patients with {symptom}",
                    "count": count,
                    "message": f"You have seen {count} patient{'s' if count != 1 else ''} with {symptom}."
                }
            
            return {"error": "Invalid query type"}
    
    async def _send_report(
        self, 
        doctor_id: str, 
        report_content: str, 
        channel: str
    ) -> dict:
        """Send a report via the specified notification channel."""
        try:
            if channel == "slack":
                result = await self.notification_service.send_slack_message(report_content)
            elif channel == "whatsapp":
                result = await self.notification_service.send_whatsapp_message(
                    doctor_id, report_content
                )
            elif channel == "in_app":
                result = await self.notification_service.create_in_app_notification(
                    doctor_id, report_content
                )
            else:
                return {"success": False, "message": f"Unknown channel: {channel}"}
            
            return {
                "success": True,
                "channel": channel,
                "message": f"Report sent successfully via {channel}!"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send report: {str(e)}"
            }
    
    async def _reschedule_appointment(
        self, 
        appointment_id: str, 
        new_datetime: str,
        notify_patient: bool = True
    ) -> dict:
        """Reschedule an existing appointment (Bonus feature: auto-rescheduling)."""
        async with async_session_maker() as session:
            appt_uuid = uuid.UUID(appointment_id)
            
            result = await session.execute(
                select(Appointment).where(Appointment.id == appt_uuid)
            )
            appointment = result.scalar_one_or_none()
            
            if not appointment:
                return {"success": False, "message": "Appointment not found"}
            
            old_time = appointment.scheduled_time
            
            try:
                new_time = datetime.fromisoformat(new_datetime.replace("Z", "+00:00"))
            except ValueError:
                new_time = self._parse_datetime(new_datetime)
            
            appointment.scheduled_time = new_time
            appointment.status = AppointmentStatus.RESCHEDULED
            
            await session.commit()
            
            # Update Google Calendar if exists
            if appointment.google_calendar_event_id:
                try:
                    await self.calendar_service.update_event(
                        appointment.google_calendar_event_id,
                        new_time
                    )
                except Exception as e:
                    print(f"Calendar update error: {e}")
            
            # Notify patient
            if notify_patient:
                patient = await session.get(Patient, appointment.patient_id)
                if patient:
                    user = await session.get(User, patient.user_id)
                    if user:
                        await self.email_service.send_reschedule_notification(
                            to_email=user.email,
                            patient_name=patient.name,
                            old_time=old_time,
                            new_time=new_time
                        )
            
            return {
                "success": True,
                "message": f"Appointment rescheduled from {old_time.strftime('%B %d at %I:%M %p')} to {new_time.strftime('%B %d at %I:%M %p')}",
                "new_time": new_time.isoformat()
            }
    
    async def _get_all_doctors(self) -> dict:
        """Get list of all doctors."""
        async with async_session_maker() as session:
            result = await session.execute(select(Doctor))
            doctors = result.scalars().all()
            
            doctors_list = [
                {
                    "id": str(d.id),
                    "name": d.name,
                    "specialty": d.specialty,
                    "consultation_duration": d.consultation_duration
                }
                for d in doctors
            ]
            
            return {
                "success": True,
                "doctors": doctors_list,
                "count": len(doctors_list),
                "message": f"Found {len(doctors_list)} doctors available."
            }
    
    async def _get_appointment_details(
        self,
        appointment_id: Optional[str] = None,
        patient_email: Optional[str] = None,
        doctor_id: Optional[str] = None,
        date_range: Optional[str] = None
    ) -> dict:
        """Get appointment details."""
        async with async_session_maker() as session:
            query = select(Appointment)
            
            if appointment_id:
                query = query.where(Appointment.id == uuid.UUID(appointment_id))
            
            if doctor_id:
                query = query.where(Appointment.doctor_id == uuid.UUID(doctor_id))
            
            if date_range:
                now = datetime.now()
                if date_range == "today":
                    start = datetime.combine(now.date(), datetime.min.time())
                    end = datetime.combine(now.date(), datetime.max.time())
                elif date_range == "tomorrow":
                    tomorrow = now.date() + timedelta(days=1)
                    start = datetime.combine(tomorrow, datetime.min.time())
                    end = datetime.combine(tomorrow, datetime.max.time())
                elif date_range == "this_week":
                    start = now - timedelta(days=now.weekday())
                    end = start + timedelta(days=6)
                elif date_range == "next_week":
                    start = now + timedelta(days=7-now.weekday())
                    end = start + timedelta(days=6)
                
                query = query.where(
                    and_(
                        Appointment.scheduled_time >= start,
                        Appointment.scheduled_time <= end
                    )
                )
            
            result = await session.execute(query)
            appointments = result.scalars().all()
            
            appt_list = []
            for appt in appointments:
                doctor = await session.get(Doctor, appt.doctor_id)
                patient = await session.get(Patient, appt.patient_id)
                
                appt_list.append({
                    "id": str(appt.id),
                    "doctor": doctor.name if doctor else "Unknown",
                    "patient": patient.name if patient else "Unknown",
                    "time": appt.scheduled_time.isoformat(),
                    "status": appt.status.value,
                    "symptoms": appt.symptoms
                })
            
            return {
                "success": True,
                "appointments": appt_list,
                "count": len(appt_list)
            }
    
    async def _cancel_appointment(
        self,
        appointment_id: str,
        reason: str = "",
        notify_patient: bool = True
    ) -> dict:
        """Cancel an appointment."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Appointment).where(Appointment.id == uuid.UUID(appointment_id))
            )
            appointment = result.scalar_one_or_none()
            
            if not appointment:
                return {"success": False, "message": "Appointment not found"}
            
            appointment.status = AppointmentStatus.CANCELLED
            appointment.notes = f"Cancelled: {reason}" if reason else "Cancelled"
            
            await session.commit()
            
            # Cancel Google Calendar event
            if appointment.google_calendar_event_id:
                try:
                    await self.calendar_service.delete_event(
                        appointment.google_calendar_event_id
                    )
                except Exception as e:
                    print(f"Calendar deletion error: {e}")
            
            return {
                "success": True,
                "message": "Appointment cancelled successfully"
            }
    
    def _parse_date(self, date_str: str) -> datetime.date:
        """Parse natural language date to datetime.date."""
        from datetime import date
        import re
        
        date_str = date_str.lower().strip()
        today = datetime.now().date()
        
        if date_str in ["today", "now"]:
            return today
        elif date_str == "tomorrow":
            return today + timedelta(days=1)
        elif date_str == "yesterday":
            return today - timedelta(days=1)
        elif "next" in date_str:
            # next monday, next week, etc.
            days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for i, day in enumerate(days):
                if day in date_str:
                    days_ahead = i - today.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    return today + timedelta(days=days_ahead)
        
        # Try parsing ISO format
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
        
        # Try other formats
        formats = ["%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%B %d"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        # Default to today if parsing fails
        return today
    
    def _parse_datetime(self, dt_str: str) -> datetime:
        """Parse natural language datetime."""
        # Simple implementation - extend as needed
        date_part = self._parse_date(dt_str)
        
        # Try to extract time
        import re
        time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', dt_str, re.I)
        
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            period = time_match.group(3)
            
            if period and period.lower() == "pm" and hour < 12:
                hour += 12
            elif period and period.lower() == "am" and hour == 12:
                hour = 0
            
            return datetime.combine(date_part, datetime.min.time().replace(hour=hour, minute=minute))
        
        # Default to 9 AM
        return datetime.combine(date_part, datetime.min.time().replace(hour=9))


# Global MCP tools instance
mcp_tools = MCPTools()
