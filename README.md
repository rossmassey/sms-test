# SMS Outreach Backend

AI-powered SMS outreach system built with FastAPI, integrating Firebase Firestore, Twilio SMS, and OpenAI for intelligent customer communication.

## Features

- **Customer Management**: CRUD operations with tags, notes, and visit tracking
- **AI Message Generation**: OpenAI-powered personalized SMS composition
- **SMS Integration**: Twilio webhook handling for inbound/outbound messages
- **Intelligent Auto-Replies**: Automated responses with escalation logic
- **RESTful API**: FastAPI with authentication and validation

## Architecture

- **Backend**: FastAPI with async support
- **Database**: Firebase Firestore
- **SMS**: Twilio Python SDK
- **AI**: OpenAI GPT integration
- **Auth**: API key authentication

## Prerequisites

You'll need accounts and API keys for:
- **Firebase** (Firestore database)
- **Twilio** (SMS functionality) 
- **OpenAI** (AI message generation)

## Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file with your service credentials:

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

### 4. Firebase Setup

1. Create a Firebase project and enable Firestore
2. Generate a service account key (JSON file)
3. Save as `firebase-service-account.json` in project root
4. Update `FIREBASE_PROJECT_ID` in `.env`

### 5. Run Development Server

```bash
python run_dev.py
```

API available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

## Testing

Run the complete test suite with these 4 commands:

```bash
# Integration tests (real Firebase)
python3 -m pytest tests/test_integration.py tests/test_integration_real.py -v

# Unit tests (mocked dependencies)  
python3 -m pytest tests/test_main.py tests/test_unit_mocked.py -v

# Utility and validation tests
python3 -m pytest tests/test_utils.py -v

# Performance tests
python3 -m pytest tests/test_performance.py -v
```

## API Endpoints

All endpoints require API key authentication via `X-API-Key` header.

### Customers
- `GET /customers` - List customers
- `POST /customers` - Create customer  
- `GET /customers/{id}` - Get customer
- `PUT /customers/{id}` - Update customer
- `DELETE /customers/{id}` - Delete customer

### Messages
- `GET /messages` - List messages
- `POST /messages/send` - Generate AI message and send SMS
- `POST /messages/manual` - Create manual message record
- `POST /messages/incoming` - Twilio webhook (no auth required)

## Project Structure

```
sms_app/
├── app/
│   ├── main.py              # FastAPI app and middleware
│   ├── database.py          # Firebase initialization  
│   ├── models.py            # Pydantic data models
│   ├── routes/
│   │   ├── customers.py     # Customer CRUD endpoints
│   │   └── messages.py      # Message and SMS endpoints
│   └── utils/
│       ├── twilio_client.py # SMS functionality
│       └── llm_client.py    # OpenAI integration
├── tests/                   # Comprehensive test suite
├── requirements.txt         # Python dependencies
└── .env                     # Environment variables
```

## Dependencies

- **FastAPI**: Web framework with automatic API documentation
- **Firebase Admin SDK**: Firestore database integration
- **Twilio SDK**: SMS sending and webhook handling  
- **OpenAI SDK**: AI-powered message generation
- **Pydantic**: Data validation and serialization
- **pytest**: Comprehensive testing framework

## License

This project is provided as-is for educational and commercial use.
