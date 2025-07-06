# SMS Outreach Backend

AI-powered SMS conversation system for NextGen MedSpa with automated responses and escalation management.

## Overview

This backend service enables staff to initiate SMS conversations with customers, with AI handling ongoing responses until human intervention is required. The system includes automatic escalation detection, manual override capabilities, and comprehensive conversation management.

## Features

- Staff-initiated SMS conversations
- Automated AI responses to customer messages
- Smart escalation detection for complex issues
- Manual message override capabilities
- Customer database management
- Comprehensive conversation history

## Quick Start

### Installation

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

Create a `.env` file with required service credentials:

```bash
# Firebase Configuration
FIREBASE_CRED_PATH=./firebase-service-account.json
FIREBASE_PROJECT_ID=your-firebase-project-id

# Twilio Configuration  
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Security
API_KEY=your_secure_api_key_here
```

### Running the Service

```bash
python run_dev.py
```

The API will be available at `http://localhost:8000` with interactive documentation at `/docs`.

## API Endpoints

All endpoints require API key authentication via `X-API-Key` header.

### Core Conversation Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/messages/initial/sms` | POST | Initiate SMS conversation with customer |
| `/messages/incoming` | POST | Handle customer replies (Twilio webhook) |
| `/messages/manual` | POST | Send manual staff message |
| `/messages` | GET | Retrieve conversation history |

### Customer Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/customers` | POST | Create new customer |
| `/customers` | GET | List all customers |
| `/customers/{id}` | GET | Get customer details |
| `/customers/{id}` | PUT | Update customer information |
| `/customers/{id}` | DELETE | Delete customer and all messages |

### Demo and Testing

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/messages/initial/demo` | POST | Test AI message generation |
| `/messages/ongoing/demo` | POST | Test AI responses with history |

## AI Message Types

The system supports seven message types for personalized communication:

- `welcome` - New customer greeting
- `follow-up` - Post-treatment check-in
- `reminder` - Appointment reminders
- `promotional` - Special offers
- `support` - Customer support
- `thank-you` - Gratitude messages
- `appointment` - Scheduling related

## Escalation System

The AI automatically escalates conversations based on detection of:

- Violence or threats toward staff/property
- Legal issues or mentions of litigation
- Medical emergencies or severe complications
- Extreme anger or unacceptable complaints
- Do-not-contact requests

When escalation occurs, the system sends appropriate acknowledgment messages and flags the conversation for staff attention.

## Demo UI

For testing and demonstration purposes, run the included React interface:

```bash
python3 run_demo.py
```

This provides a complete workflow demonstration including customer management, conversation initiation, and staff intervention capabilities.

## Testing

Run the test suite with:

```bash
python3 run_tests.py
```

Test categories:
- `--unit` - Core API and functionality tests
- `--integration` - Full stack tests with external services
- `--utils` - Utility function validation
- `--performance` - Load and performance testing

## Project Structure

```
sms_app/
├── app/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Firebase configuration
│   ├── models.py            # Data models
│   ├── routes/
│   │   ├── customers.py     # Customer endpoints
│   │   └── messages.py      # Message endpoints
│   └── utils/
│       ├── twilio_client.py # SMS functionality
│       └── llm_client.py    # AI integration
├── jank_ui/                 # Demo interface
├── tests/                   # Test suite
├── business_config.txt      # Business configuration
└── requirements.txt         # Dependencies
```

## Dependencies

- FastAPI - Web framework
- Firebase Admin SDK - Database
- Twilio - SMS messaging
- OpenAI - AI message generation
- React - Demo UI

## Business Configuration

The system includes configurable business data in `business_config.txt` for context-aware AI responses. This allows the AI to handle basic business inquiries (hours, location, services) without escalation while maintaining appropriate boundaries for complex issues.
