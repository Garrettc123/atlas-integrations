"""
ATLAS Stripe Client
Payment link generation and deposit collection.
"""

import stripe
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')


class StripeClient:
    """Creates payment links and tracks deposit collection."""

    def create_payment_link(self, amount_cents: int, description: str,
                             customer_email: Optional[str] = None,
                             metadata: Optional[dict] = None) -> dict:
        """
        Create a Stripe payment link for deposit collection.

        Args:
            amount_cents: Amount in cents (e.g., 50000 = $500)
            description: Job description shown on payment page
            customer_email: Pre-fill customer email
            metadata: Lead ID, client ID, etc.

        Returns: {url, link_id, amount, status}
        """
        try:
            price = stripe.Price.create(
                currency='usd',
                unit_amount=amount_cents,
                product_data={'name': description}
            )

            link_params = {
                'line_items': [{'price': price.id, 'quantity': 1}],
                'metadata': metadata or {}
            }

            if customer_email:
                link_params['customer_creation'] = 'always'

            payment_link = stripe.PaymentLink.create(**link_params)

            logger.info(f"Payment link created: ${amount_cents/100:.2f}")
            return {
                'url': payment_link.url,
                'link_id': payment_link.id,
                'amount': amount_cents / 100,
                'status': 'active'
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return {'url': None, 'link_id': None, 'amount': 0, 'status': 'error'}

    def create_invoice(self, customer_email: str, amount_cents: int,
                        description: str) -> dict:
        """Create and send a Stripe invoice."""
        try:
            customer = stripe.Customer.create(email=customer_email)

            stripe.InvoiceItem.create(
                customer=customer.id,
                amount=amount_cents,
                currency='usd',
                description=description
            )

            invoice = stripe.Invoice.create(
                customer=customer.id,
                auto_advance=True
            )
            finalized = stripe.Invoice.finalize_invoice(invoice.id)

            logger.info(f"Invoice sent to {customer_email}")
            return {
                'invoice_id': finalized.id,
                'hosted_url': finalized.hosted_invoice_url,
                'status': finalized.status
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe invoice error: {e}")
            return {}
