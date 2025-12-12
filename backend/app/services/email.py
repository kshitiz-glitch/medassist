"""
Email Service
Handles email notifications for appointments using SendGrid.
"""

from datetime import datetime
from typing import Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from app.config import settings


class EmailService:
    """Service for sending email notifications."""
    
    def __init__(self):
        self.api_key = settings.sendgrid_api_key
        self.from_email = settings.from_email
        self.client = None
        
        if self.api_key:
            self.client = SendGridAPIClient(api_key=self.api_key)
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email using SendGrid."""
        try:
            if not self.client:
                # Demo mode
                print(f"[DEMO EMAIL] To: {to_email}")
                print(f"[DEMO EMAIL] Subject: {subject}")
                print(f"[DEMO EMAIL] Content: {html_content[:200]}...")
                return True
            
            message = Mail(
                from_email=Email(self.from_email, "Doctor Appointment Assistant"),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            if text_content:
                message.add_content(Content("text/plain", text_content))
            
            response = self.client.send(message)
            
            return response.status_code in [200, 201, 202]
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    async def send_appointment_confirmation(
        self,
        to_email: str,
        patient_name: str,
        doctor_name: str,
        appointment_time: datetime,
        symptoms: str = ""
    ) -> bool:
        """Send appointment confirmation email to patient."""
        
        subject = f"✅ Appointment Confirmed with Dr. {doctor_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f7fa; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .appointment-card {{ background: #f8f9fa; border-left: 4px solid #667eea; padding: 20px; margin: 20px 0; border-radius: 0 8px 8px 0; }}
                .detail {{ margin: 10px 0; }}
                .label {{ color: #666; font-size: 12px; text-transform: uppercase; }}
                .value {{ color: #333; font-size: 16px; font-weight: 600; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .btn {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏥 Appointment Confirmed!</h1>
                </div>
                <div class="content">
                    <p>Hello <strong>{patient_name}</strong>,</p>
                    <p>Your appointment has been successfully scheduled. Here are the details:</p>
                    
                    <div class="appointment-card">
                        <div class="detail">
                            <div class="label">Doctor</div>
                            <div class="value">Dr. {doctor_name}</div>
                        </div>
                        <div class="detail">
                            <div class="label">Date & Time</div>
                            <div class="value">{appointment_time.strftime('%B %d, %Y at %I:%M %p')}</div>
                        </div>
                        {f'<div class="detail"><div class="label">Reason for Visit</div><div class="value">{symptoms}</div></div>' if symptoms else ''}
                    </div>
                    
                    <p><strong>Important Reminders:</strong></p>
                    <ul>
                        <li>Please arrive 10 minutes before your scheduled time</li>
                        <li>Bring any relevant medical records or test reports</li>
                        <li>If you need to cancel, please do so at least 24 hours in advance</li>
                    </ul>
                    
                    <center>
                        <a href="#" class="btn">Add to Calendar</a>
                    </center>
                </div>
                <div class="footer">
                    <p>This email was sent by Doctor Appointment Assistant</p>
                    <p>If you have any questions, please reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)
    
    async def send_reschedule_notification(
        self,
        to_email: str,
        patient_name: str,
        old_time: datetime,
        new_time: datetime
    ) -> bool:
        """Send reschedule notification email."""
        
        subject = "📅 Your Appointment Has Been Rescheduled"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f7fa; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .time-box {{ display: inline-block; background: #f8f9fa; padding: 15px 25px; border-radius: 8px; margin: 10px; text-align: center; }}
                .old-time {{ text-decoration: line-through; color: #999; }}
                .new-time {{ color: #28a745; font-weight: bold; }}
                .arrow {{ font-size: 24px; color: #667eea; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📅 Appointment Rescheduled</h1>
                </div>
                <div class="content">
                    <p>Hello <strong>{patient_name}</strong>,</p>
                    <p>Your appointment has been rescheduled to a new time:</p>
                    
                    <center>
                        <div class="time-box old-time">
                            <div style="font-size: 12px; color: #999;">OLD TIME</div>
                            {old_time.strftime('%B %d, %Y')}
                            <br>{old_time.strftime('%I:%M %p')}
                        </div>
                        <span class="arrow">→</span>
                        <div class="time-box new-time">
                            <div style="font-size: 12px; color: #28a745;">NEW TIME</div>
                            {new_time.strftime('%B %d, %Y')}
                            <br>{new_time.strftime('%I:%M %p')}
                        </div>
                    </center>
                    
                    <p style="margin-top: 20px;">If this new time doesn't work for you, please contact us to reschedule.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)
    
    async def send_cancellation_notification(
        self,
        to_email: str,
        patient_name: str,
        appointment_time: datetime,
        reason: str = ""
    ) -> bool:
        """Send cancellation notification email."""
        
        subject = "❌ Appointment Cancelled"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7fa; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #dc3545; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: white; padding: 30px; border-radius: 0 0 10px 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>❌ Appointment Cancelled</h1>
                </div>
                <div class="content">
                    <p>Hello <strong>{patient_name}</strong>,</p>
                    <p>Your appointment scheduled for <strong>{appointment_time.strftime('%B %d, %Y at %I:%M %p')}</strong> has been cancelled.</p>
                    {f'<p><strong>Reason:</strong> {reason}</p>' if reason else ''}
                    <p>If you'd like to schedule a new appointment, please visit our website or contact us.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)
