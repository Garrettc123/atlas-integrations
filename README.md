# ATLAS Integrations 🔌

> **Twilio · Stripe · Google Calendar · SendGrid**  
> Garcar Enterprise — ATLAS Platform

[![CI](https://github.com/Garrettc123/atlas-integrations/actions/workflows/ci.yml/badge.svg)](https://github.com/Garrettc123/atlas-integrations/actions/workflows/ci.yml)

## Integrations

| Service | Purpose | Compliance |
|---------|---------|------------|
| Twilio | SMS outreach + inbound handling | TCPA time windows + opt-out |
| Stripe | Payment links + deposit collection | PCI-DSS via Stripe |
| Google Calendar | Appointment booking | None required |
| SendGrid | Email delivery + tracking | CAN-SPAM footer auto-append |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```
