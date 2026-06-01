"""
ATLAS Calendar Client
Google Calendar appointment booking with availability detection.
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz
import os
import logging

logger = logging.getLogger(__name__)

SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', 'service_account.json')
SCOPES = ['https://www.googleapis.com/auth/calendar']


class CalendarClient:
    """Books appointments in contractor's Google Calendar."""

    def __init__(self):
        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )
            self.service = build('calendar', 'v3', credentials=creds)
        except Exception as e:
            logger.warning(f"Calendar not configured: {e}")
            self.service = None

    def find_next_slot(self, calendar_id: str, duration_minutes: int = 60,
                        timezone: str = 'America/Chicago') -> Optional[dict]:
        """
        Find next available slot in the next 3 business days.
        Returns: {start, end, timezone} or None
        """
        if not self.service:
            return None

        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        for day_offset in range(1, 7):  # Next 6 days
            check = now + timedelta(days=day_offset)

            if check.weekday() >= 5:  # Skip weekends
                continue

            # Check 9am - 5pm slots in 1-hour blocks
            for hour in range(9, 17):
                slot_start = check.replace(hour=hour, minute=0, second=0, microsecond=0)
                slot_end = slot_start + timedelta(minutes=duration_minutes)

                if self._is_slot_free(calendar_id, slot_start, slot_end):
                    return {
                        'start': slot_start.isoformat(),
                        'end': slot_end.isoformat(),
                        'timezone': timezone
                    }
        return None

    def book_appointment(self, calendar_id: str, lead_name: str, lead_email: str,
                          lead_phone: str, slot: dict, job_description: str) -> dict:
        """
        Creates a calendar event and sends invite to lead.
        Returns: {event_id, url, start, end}
        """
        if not self.service:
            return {'event_id': None, 'url': None}

        event = {
            'summary': f'Roofing Inspection — {lead_name}',
            'description': f'{job_description}\n\nLead: {lead_name}\nPhone: {lead_phone}',
            'start': {'dateTime': slot['start'], 'timeZone': slot['timezone']},
            'end': {'dateTime': slot['end'], 'timeZone': slot['timezone']},
            'attendees': [{'email': lead_email}],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 1440},   # 24h
                    {'method': 'sms', 'minutes': 60},        # 1h
                ]
            }
        }

        created = self.service.events().insert(
            calendarId=calendar_id, body=event, sendNotifications=True
        ).execute()

        logger.info(f"Appointment booked: {created.get('id')} for {lead_name}")
        return {
            'event_id': created.get('id'),
            'url': created.get('htmlLink'),
            'start': slot['start'],
            'end': slot['end']
        }

    def _is_slot_free(self, calendar_id, start, end) -> bool:
        try:
            body = {'timeMin': start.isoformat(), 'timeMax': end.isoformat(),
                    'items': [{'id': calendar_id}]}
            result = self.service.freebusy().query(body=body).execute()
            busy = result.get('calendars', {}).get(calendar_id, {}).get('busy', [])
            return len(busy) == 0
        except Exception:
            return True  # Default to available if check fails
