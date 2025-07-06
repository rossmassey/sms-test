# SMS Outreach Backend

AI-powered SMS outreach system built with FastAPI, integrating Firebase Firestore, Twilio SMS, and OpenAI for intelligent customer communication.

## Features

- **Customer Management**: CRUD operations with tags, notes, and visit tracking
- **AI Message Generation**: OpenAI-powered personalized SMS composition with 7 message types
- **SMS Integration**: Twilio webhook handling for inbound/outbound messages
- **Intelligent Auto-Replies**: Automated responses with escalation logic
- **Message Types**: Welcome, follow-up, reminder, promotional, support, thank-you, appointment
- **Demo Mode**: Generate AI responses without sending SMS for testing
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

### Quick Test Options

```bash
# Run default development suite (fast, works everywhere)
python3 run_tests.py

# Run specific test categories
python3 run_tests.py --unit                    # Fast unit tests only
python3 run_tests.py --integration-graceful    # Integration tests (mocked external services)
python3 run_tests.py --integration-real        # Integration tests (real external services)
python3 run_tests.py --utils                   # Utility tests only
python3 run_tests.py --performance             # Performance tests only
```

### Test Categories Explained

**🚀 Unit Tests** - Fast, all dependencies mocked
- `tests/test_main.py` - Core API endpoints and authentication
- `tests/test_unit_mocked.py` - New SMS endpoints with heavy mocking
- Both complement each other, run together for full unit coverage

**🔗 Integration Tests** - **Choose one approach:**
- `tests/test_integration.py` - **Graceful/Mocked** (mocks database, AI, SMS calls)
- `tests/test_integration_real.py` - **Real Services** (actually hits database, AI, SMS)
- **For Development/CI**: Use `--integration-graceful` (fast, no API keys needed)
- **For Production Testing**: Use `--integration-real` (requires Firebase, OpenAI, Twilio)

**🛠️ Utility Tests** - Core functionality and validation
- `tests/test_utils.py` - Database, models, and utility functions

**⚡ Performance Tests** - Speed and load testing
- `tests/test_performance.py` - API response times and concurrent load

### Common Development Workflows

```bash
# 🏃 Default development suite (fast, works everywhere, ~25 seconds)
python3 run_tests.py

# ⚡ Quick unit tests only (super fast, ~1 second)
python3 run_tests.py --unit

# 🔍 Test with real services (production readiness, ~45 seconds)
python3 run_tests.py --unit --integration-real --utils

# 📈 Full production check with performance (requires API keys, ~1 minute)
python3 run_tests.py --unit --integration-real --utils --performance

# 🎯 Just test your new feature integration
python3 run_tests.py --integration-graceful
```

### Manual Test Commands

If you prefer running tests manually:

```bash
# Fast unit tests (recommended for development)
python3 -m pytest tests/test_main.py tests/test_unit_mocked.py -v

# Integration tests - graceful/mocked (works without external services)
python3 -m pytest tests/test_integration.py -v

# Integration tests - real services (requires API keys)
python3 -m pytest tests/test_integration_real.py -v

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
- `POST /messages/initial/sms` - Send initial SMS with AI generation
- `POST /messages/initial/demo` - Generate initial demo message (no SMS)
- `POST /messages/ongoing/sms` - Send ongoing SMS response
- `POST /messages/ongoing/demo` - Generate ongoing demo response (no SMS)

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
