# SMS Outreach Backend

**AI-powered SMS conversation system for NextGen MedSpa** - Staff initiate conversations, AI maintains them automatically, and human staff intervene only when needed.

## 🎯 What This App Does

Your staff starts SMS conversations with customers, and AI continues the conversation automatically until the customer is satisfied or human intervention is needed.

**Key Features:**
- **Staff-Initiated Conversations**: Start personalized SMS conversations with customers
- **Automatic AI Responses**: AI handles customer replies without staff involvement  
- **Smart Escalation**: AI knows when to stop and alert staff for complex issues
- **Manual Override**: Staff can intervene and send manual messages at any time
- **NextGen MedSpa Integration**: Tailored for medical spa services and treatments

## 🎮 Live Demo

**Want to see how it works?** Check out the interactive demo UI:

```bash
python3 run_demo.py
```

The demo shows the complete workflow: adding customers, starting AI conversations, mocking customer responses, and manual staff intervention. No real SMS needed!

## 🚀 Quick Start

### 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# For demo UI:
cd jank_ui && npm install
```

### 2. Configure Environment

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

### 3. Run Development Server

```bash
python run_dev.py
```

API available at `http://localhost:8000` with interactive docs at `/docs`

## 📱 API Endpoints Overview

All endpoints require API key authentication via `X-API-Key` header.

### Core Conversation Flow

| Endpoint | Purpose |
|----------|---------|
| `POST /messages/initial/sms` | **Start conversation** with customer |
| `POST /messages/incoming` | **Handle customer replies** (Twilio webhook) |
| `POST /messages/manual` | **Staff sends manual message** |
| `GET /messages` | **View conversation history** |

### Demo & Testing

| Endpoint | Purpose |
|----------|---------|
| `POST /messages/initial/demo` | **Test AI messages** without SMS |
| `POST /messages/ongoing/demo` | **Test AI responses** with chat history |

### Customer Management

| Endpoint | Purpose |
|----------|---------|
| `POST /customers` | **Create customer** |
| `GET /customers` | **List customers** |
| `GET /customers/{id}` | **Get customer details** |
| `PUT /customers/{id}` | **Update customer** |

## 🤖 AI Message Types

The AI can generate 7 types of personalized messages:

- **`welcome`** - New customer greeting
- **`follow-up`** - Post-treatment check-in  
- **`reminder`** - Appointment reminders
- **`promotional`** - Special offers
- **`support`** - Help with questions
- **`thank-you`** - Gratitude messages
- **`appointment`** - Scheduling related

## 🚨 Auto-Escalation System

AI automatically stops responding and alerts staff when it detects:
- **Violence/Threats** - Any threatening language toward staff or property
- **Legal Issues** - Mentions of suing, lawyers, malpractice, or legal action
- **Medical Emergencies** - Severe pain, bleeding, allergic reactions, or complications
- **Extreme Anger** - Unacceptable service complaints or insulting language
- **Do Not Contact** - Complete silence for unsubscribe requests

**Escalation Features:**
- **Deterministic Pattern Detection** - Critical threats bypass AI for safety
- **Contextual Acknowledgments** - Professional responses before escalation
- **Complete Silence** - No response to "do not contact" requests
- **Comprehensive Testing** - 28 test cases covering all escalation scenarios

## 📊 Testing

```bash
python3 run_tests.py
```

**Test Categories:**
- `--unit` - Core API, SMS endpoints, and escalation detection (recommended for development)
- `--integration` - Full stack tests with Firebase, OpenAI, and Twilio
- `--utils` - Utility function validation tests
- `--performance` - Load and performance benchmarks

**Key Test Suites:**
- **Escalation Detection** - 28 test cases covering violence, legal threats, medical emergencies, and do-not-contact scenarios
- **SMS Endpoints** - All 4 new message endpoints with mocked services
- **Core API** - Authentication, customer management, and database operations

Use `-h` for additional test options and categories.

## 📁 Project Structure

```
sms_app/
├── app/
│   ├── main.py              # FastAPI app and middleware
│   ├── database.py          # Firebase initialization  
│   ├── models.py            # Data models and validation
│   ├── routes/
│   │   ├── customers.py     # Customer management endpoints
│   │   └── messages.py      # SMS and conversation endpoints
│   └── utils/
│       ├── twilio_client.py # SMS functionality
│       └── llm_client.py    # AI message generation
├── jank_ui/                 # React demo UI
├── tests/                   # Test suite
├── business_config.txt      # NextGen MedSpa configuration
├── requirements.txt         # Dependencies
└── .env                     # Environment variables
```

## 🔗 Frontend Integration

For detailed frontend integration examples, conversation flows, and demo UI architecture, see:

**[📖 Frontend Integration Guide](FRONTEND_GUIDE.md)**

## 🛠️ Dependencies

- **FastAPI** - Web framework
- **Firebase Admin SDK** - Database
- **Twilio** - SMS messaging
- **OpenAI** - AI message generation
- **React** - Demo UI framework
