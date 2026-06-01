"""
ATLAS Twilio Client
TCPA-compliant SMS sending with opt-out processing and time enforcement.
"""

from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from datetime import datetime
import pytz
import os
import logging

logger = logging.getLogger(__name__)

# Texas-safe hours (strictest: 9am-9pm)
SEND_WINDOW_START = 9
SEND_WINDOW_END = 21

OPT_OUT_KEYWORDS = {'STOP', 'QUIT', 'CANCEL', 'UNSUBSCRIBE', 'OPT OUT', 'REMOVE', 'END'}


class TwilioClient:
    """TCPA-compliant SMS client."""

    def __init__(self):
        self.client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')

    def send_sms(self, to: str, body: str, lead_timezone: str = 'America/Chicago') -> dict:
        """
        Send TCPA-compliant SMS.
        Auto-blocks if outside send window.
        Returns: {sent, sid, blocked_reason}
        """
        # Time enforcement
        if not self._in_send_window(lead_timezone):
            logger.warning(f"SMS blocked (time window): {to[-4:]}****")
            return {'sent': False, 'sid': None, 'blocked_reason': 'outside_send_window'}

        try:
            msg = self.client.messages.create(
                to=to,
                from_=self.from_number,
                body=body
            )
            logger.info(f"SMS sent: {msg.sid} to {to[-4:]}****")
            return {'sent': True, 'sid': msg.sid, 'blocked_reason': None}
        except TwilioException as e:
            logger.error(f"Twilio error: {e}")
            return {'sent': False, 'sid': None, 'blocked_reason': str(e)}

    def process_inbound(self, from_number: str, body: str, db=None) -> dict:
        """
        Handle inbound SMS. Immediately processes opt-outs (TCPA required).
        Returns TwiML-ready response.
        """
        clean = body.upper().strip()

        if any(kw in clean for kw in OPT_OUT_KEYWORDS):
            if db:
                db.suppress_phone(from_number)
            logger.info(f"Opt-out processed: {from_number[-4:]}****")
            return {
                'action': 'opted_out',
                'twiml_response': 'You have been unsubscribed. Reply START to rejoin.'
            }

        return {'action': 'conversation', 'twiml_response': None}

    def _in_send_window(self, timezone_str: str) -> bool:
        try:
            tz = pytz.timezone(timezone_str)
        except pytz.UnknownTimeZoneError:
            tz = pytz.timezone('America/Chicago')

        local = datetime.now(tz)
        return SEND_WINDOW_START <= local.hour < SEND_WINDOW_END

    def get_message_status(self, sid: str) -> str:
        msg = self.client.messages(sid).fetch()
        return msg.status
