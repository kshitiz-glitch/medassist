"""
Notification Service
Handles notifications via Slack, WhatsApp, and in-app notifications.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

import httpx
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from app.config import settings


class NotificationService:
    """Service for multi-channel notifications to doctors."""
    
    def __init__(self):
        self.slack_webhook_url = settings.slack_webhook_url
        self.slack_token = settings.slack_bot_token
        self.slack_client = None
        
        if self.slack_token:
            self.slack_client = WebClient(token=self.slack_token)
        
        # In-app notifications storage (in production, use Redis or DB)
        self._in_app_notifications = {}
    
    async def send_slack_message(
        self,
        message: str,
        channel: str = "#doctor-reports"
    ) -> dict:
        """Send a message to Slack."""
        try:
            if self.slack_webhook_url:
                # Use webhook for simple messages
                async with httpx.AsyncClient() as client:
                    payload = {
                        "text": message,
                        "blocks": self._format_slack_blocks(message)
                    }
                    response = await client.post(
                        self.slack_webhook_url,
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        return {"success": True, "message": "Sent to Slack"}
                    else:
                        return {"success": False, "message": f"Slack error: {response.text}"}
            
            elif self.slack_client:
                # Use Slack SDK for more control
                response = self.slack_client.chat_postMessage(
                    channel=channel,
                    text=message,
                    blocks=self._format_slack_blocks(message)
                )
                return {"success": True, "message": "Sent to Slack"}
            
            else:
                # Demo mode
                print(f"[DEMO SLACK] {message[:200]}...")
                return {"success": True, "message": "Sent to Slack (demo mode)"}
                
        except SlackApiError as e:
            return {"success": False, "message": f"Slack API error: {e.response['error']}"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def _format_slack_blocks(self, message: str) -> list:
        """Format message as Slack blocks for rich formatting."""
        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🏥 Doctor Report",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📅 Generated at {datetime.now().strftime('%B %d, %Y %I:%M %p')}"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
    
    async def send_whatsapp_message(
        self,
        doctor_id: str,
        message: str,
        phone_number: Optional[str] = None
    ) -> dict:
        """
        Send a WhatsApp message.
        Note: This requires WhatsApp Business API integration.
        For demo purposes, this simulates the message.
        """
        try:
            # In production, integrate with WhatsApp Business API
            # (Twilio, MessageBird, or direct Meta API)
            
            print(f"[DEMO WHATSAPP] To doctor {doctor_id}")
            print(f"[DEMO WHATSAPP] Message: {message[:200]}...")
            
            # Placeholder for actual WhatsApp API call
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         "https://api.whatsapp.com/send",
            #         json={
            #             "phone": phone_number,
            #             "message": message
            #         }
            #     )
            
            return {
                "success": True,
                "message": "WhatsApp message sent (demo mode)",
                "doctor_id": doctor_id
            }
            
        except Exception as e:
            return {"success": False, "message": f"WhatsApp error: {str(e)}"}
    
    async def create_in_app_notification(
        self,
        user_id: str,
        content: str,
        notification_type: str = "report"
    ) -> dict:
        """Create an in-app notification for a user."""
        try:
            notification_id = str(uuid.uuid4())
            
            notification = {
                "id": notification_id,
                "user_id": user_id,
                "content": content,
                "type": notification_type,
                "read": False,
                "created_at": datetime.now().isoformat()
            }
            
            # Store notification (in production, use database)
            if user_id not in self._in_app_notifications:
                self._in_app_notifications[user_id] = []
            
            self._in_app_notifications[user_id].append(notification)
            
            return {
                "success": True,
                "notification_id": notification_id,
                "message": "In-app notification created"
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False
    ) -> list:
        """Get all notifications for a user."""
        notifications = self._in_app_notifications.get(user_id, [])
        
        if unread_only:
            notifications = [n for n in notifications if not n["read"]]
        
        # Sort by created_at descending
        notifications.sort(key=lambda x: x["created_at"], reverse=True)
        
        return notifications
    
    async def mark_notification_read(
        self,
        user_id: str,
        notification_id: str
    ) -> bool:
        """Mark a notification as read."""
        notifications = self._in_app_notifications.get(user_id, [])
        
        for notification in notifications:
            if notification["id"] == notification_id:
                notification["read"] = True
                notification["read_at"] = datetime.now().isoformat()
                return True
        
        return False
    
    async def send_doctor_report(
        self,
        doctor_id: str,
        report: dict,
        channel: str = "slack"
    ) -> dict:
        """
        Send a formatted doctor report via the specified channel.
        Formats the report nicely for each channel.
        """
        
        # Format the report message
        message = self._format_report_message(report)
        
        if channel == "slack":
            return await self.send_slack_message(message)
        elif channel == "whatsapp":
            return await self.send_whatsapp_message(doctor_id, message)
        elif channel == "in_app":
            return await self.create_in_app_notification(doctor_id, message, "report")
        else:
            return {"success": False, "message": f"Unknown channel: {channel}"}
    
    def _format_report_message(self, report: dict) -> str:
        """Format a report dictionary into a readable message."""
        
        lines = [
            f"📊 *Daily Report for Dr. {report.get('doctor_name', 'Doctor')}*",
            f"📅 {datetime.now().strftime('%B %d, %Y')}",
            "",
            "━━━━━━━━━━━━━━━━━━━━━",
            ""
        ]
        
        stats = report.get("stats", {})
        
        if "yesterday_visits" in stats:
            lines.append(f"📌 *Yesterday's Visits:* {stats['yesterday_visits']}")
        
        if "today_appointments" in stats:
            lines.append(f"📌 *Today's Appointments:* {stats['today_appointments']}")
        
        if "tomorrow_appointments" in stats:
            lines.append(f"📌 *Tomorrow's Appointments:* {stats['tomorrow_appointments']}")
        
        if "total_visits" in stats:
            lines.append(f"📌 *Total Patients:* {stats['total_visits']}")
        
        symptoms = stats.get("symptoms_breakdown", {})
        if symptoms:
            lines.append("")
            lines.append("*Top Symptoms:*")
            for symptom, count in sorted(symptoms.items(), key=lambda x: -x[1])[:5]:
                lines.append(f"  • {symptom}: {count}")
        
        lines.extend([
            "",
            "━━━━━━━━━━━━━━━━━━━━━",
            "",
            report.get("summary", "Have a great day! 🏥")
        ])
        
        return "\n".join(lines)
