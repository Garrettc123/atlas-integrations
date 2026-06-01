"""
ATLAS Integration Tests (all mocked — no real API calls)
"""

import pytest
from unittest.mock import MagicMock, patch
from integrations.twilio_client import TwilioClient, OPT_OUT_KEYWORDS


class TestTwilioClient:
    """Test SMS compliance layer."""

    def test_opt_out_keywords_complete(self):
        required = {'STOP', 'QUIT', 'CANCEL', 'UNSUBSCRIBE'}
        assert required.issubset(OPT_OUT_KEYWORDS)

    def test_blocks_message_outside_window(self):
        with patch('integrations.twilio_client.datetime') as mock_dt:
            from unittest.mock import MagicMock
            mock_now = MagicMock()
            mock_now.hour = 7  # 7 AM — before 9 AM
            mock_dt.now.return_value = mock_now

            with patch('integrations.twilio_client.Client'):
                client = TwilioClient()
                result = client.send_sms('+12145550000', 'Test message')
                assert result['sent'] is False
                assert result['blocked_reason'] == 'outside_send_window'

    def test_opt_out_triggers_suppression(self):
        mock_db = MagicMock()
        with patch('integrations.twilio_client.Client'):
            client = TwilioClient()
            result = client.process_inbound('+12145550000', 'STOP', db=mock_db)
            mock_db.suppress_phone.assert_called_once_with('+12145550000')
            assert result['action'] == 'opted_out'

    def test_normal_reply_continues_conversation(self):
        with patch('integrations.twilio_client.Client'):
            client = TwilioClient()
            result = client.process_inbound('+12145550000', 'Yes, call me at 2pm')
            assert result['action'] == 'conversation'


class TestStripeClient:
    """Test payment link creation."""

    def test_payment_link_creation(self):
        with patch('integrations.stripe_client.stripe') as mock_stripe:
            mock_price = MagicMock(id='price_xxx')
            mock_link = MagicMock(url='https://buy.stripe.com/test', id='plink_xxx')
            mock_stripe.Price.create.return_value = mock_price
            mock_stripe.PaymentLink.create.return_value = mock_link

            from integrations.stripe_client import StripeClient
            client = StripeClient()
            result = client.create_payment_link(50000, 'Roof inspection deposit')

            assert result['url'] == 'https://buy.stripe.com/test'
            assert result['amount'] == 500.0
            assert result['status'] == 'active'
