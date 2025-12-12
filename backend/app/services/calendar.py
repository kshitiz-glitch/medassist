"""
Google Calendar Service
Handles calendar integration for appointment scheduling.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.config import settings


# Scopes required for Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarService:
    """Service for Google Calendar integration."""
    
    def __init__(self):
        self.credentials = None
        self.service = None
    
    async def _get_service(self):
        """Get or create the Google Calendar service."""
        if self.service:
            return self.service
        
        creds = None
        
        # Load existing token
        if os.path.exists(settings.google_token_file):
            creds = Credentials.from_authorized_user_file(
                settings.google_token_file, SCOPES
            )
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # For production, you'd use a different OAuth flow
                # This is for local development
                if os.path.exists(settings.google_credentials_file):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        settings.google_credentials_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    
                    # Save credentials for future use
                    with open(settings.google_token_file, 'w') as token:
                        token.write(creds.to_json())
                else:
                    # Return a mock service for demo purposes
                    return None
        
        self.credentials = creds
        self.service = build('calendar', 'v3', credentials=creds)
        return self.service
    
    async def create_event(
        self,
        summary: str,
        start_time: datetime,
        duration_minutes: int = 30,
        description: str = "",
        attendees: List[str] = None,
        location: str = ""
    ) -> Optional[str]:
        """
        Create a calendar event for an appointment.
        Returns the event ID if successful.
        """
        try:
            service = await self._get_service()
            
            if not service:
                # Demo mode - return a fake event ID
                print(f"[DEMO] Would create calendar event: {summary} at {start_time}")
                return f"demo_event_{start_time.strftime('%Y%m%d%H%M')}"
            
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Asia/Kolkata',  # Adjust for your timezone
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Asia/Kolkata',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 30},       # 30 min before
                    ],
                },
            }
            
            if location:
                event['location'] = location
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
                event['sendUpdates'] = 'all'  # Send email invites
            
            result = service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return result.get('id')
            
        except Exception as e:
            print(f"Error creating calendar event: {e}")
            # Return demo ID for graceful degradation
            return f"demo_event_{start_time.strftime('%Y%m%d%H%M')}"
    
    async def update_event(
        self,
        event_id: str,
        new_start_time: datetime,
        duration_minutes: int = 30
    ) -> bool:
        """Update an existing calendar event."""
        try:
            if event_id.startswith("demo_"):
                print(f"[DEMO] Would update event {event_id} to {new_start_time}")
                return True
            
            service = await self._get_service()
            if not service:
                return True
            
            # Get existing event
            event = service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            end_time = new_start_time + timedelta(minutes=duration_minutes)
            
            event['start']['dateTime'] = new_start_time.isoformat()
            event['end']['dateTime'] = end_time.isoformat()
            
            service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error updating calendar event: {e}")
            return False
    
    async def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event."""
        try:
            if event_id.startswith("demo_"):
                print(f"[DEMO] Would delete event {event_id}")
                return True
            
            service = await self._get_service()
            if not service:
                return True
            
            service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error deleting calendar event: {e}")
            return False
    
    async def get_events(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[dict]:
        """Get calendar events within a time range."""
        try:
            service = await self._get_service()
            if not service:
                return []
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_time.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
            
        except Exception as e:
            print(f"Error getting calendar events: {e}")
            return []
