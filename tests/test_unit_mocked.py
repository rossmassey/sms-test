"""
Unit tests for the SMS Outreach Backend - All external services mocked.
These tests should run fast and not depend on any external services.
Run with: python -m pytest tests/test_unit_mocked.py -v
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

# Import the mock app instead of the real app
from tests.test_app import mock_app
from app.models import CustomerCreate, CustomerUpdate, MessageSend, Customer, Message

# Create test client with mock app
client = TestClient(mock_app)

# Test data
VALID_API_KEY = "sms_backend_2025_secure_key_xyz789"
INVALID_API_KEY = "invalid_key"

class TestCustomerEndpointsUnit:
    """Unit tests for customer endpoints with mocked Firebase."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": VALID_API_KEY, "Content-Type": "application/json"}
    
    def test_list_customers_empty_mocked(self, auth_headers):
        """Test listing customers when collection is empty (mocked)."""
        # Use the mock from test_app
        from tests.test_app import mock_customers_collection
        mock_customers_collection.limit.return_value.offset.return_value.stream.return_value = []
        
        response = client.get("/customers", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []
    
    def test_create_customer_success_mocked(self, auth_headers):
        """Test successful customer creation (mocked)."""
        # Use the mock from test_app
        from tests.test_app import mock_customers_collection
        
        # Mock Firestore response
        mock_doc_ref = Mock()
        mock_doc_ref.id = "test_customer_id"
        mock_customers_collection.add.return_value = (None, mock_doc_ref)
        
        customer_data = {
            "name": "John Doe",
            "phone": "+1234567890",
            "notes": "Test customer",
            "tags": ["test", "unit-test"]
        }
        
        response = client.post("/customers", headers=auth_headers, json=customer_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_customer_id"
        assert data["name"] == "John Doe"
        assert data["phone"] == "+1234567890"
    
    def test_get_customer_success_mocked(self, auth_headers):
        """Test retrieving a specific customer (mocked)."""
        # Use the mock from test_app
        from tests.test_app import mock_customers_collection
        
        # Mock Firestore response
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.id = "test_customer_id"
        mock_doc.to_dict.return_value = {
            "name": "Jane Doe",
            "phone": "+1987654321",
            "notes": "VIP customer",
            "tags": ["vip"]
        }
        mock_customers_collection.document.return_value.get.return_value = mock_doc
        
        response = client.get("/customers/test_customer_id", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_customer_id"
        assert data["name"] == "Jane Doe"
    
    def test_get_customer_not_found_mocked(self, auth_headers):
        """Test retrieving a non-existent customer (mocked)."""
        # Use the mock from test_app
        from tests.test_app import mock_customers_collection
        
        # Mock Firestore response
        mock_doc = Mock()
        mock_doc.exists = False
        mock_customers_collection.document.return_value.get.return_value = mock_doc
        
        response = client.get("/customers/nonexistent", headers=auth_headers)
        assert response.status_code == 404
        assert "Customer not found" in response.text

class TestMessageEndpointsUnit:
    """Unit tests for message endpoints with mocked Firebase."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": VALID_API_KEY, "Content-Type": "application/json"}
    
    def test_list_messages_empty_mocked(self, auth_headers):
        """Test listing messages when collection is empty (mocked)."""
        from tests.test_app import mock_messages_collection
        mock_messages_collection.stream.return_value = []
        
        response = client.get("/messages", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []
    
    def test_create_manual_message_success_mocked(self, auth_headers):
        """Test creating a manual message record (mocked)."""
        from tests.test_app import mock_customers_collection, mock_messages_collection
        
        # Mock customer exists
        mock_customer_doc = Mock()
        mock_customer_doc.exists = True
        mock_customers_collection.document.return_value.get.return_value = mock_customer_doc
        
        # Mock message creation
        mock_doc_ref = Mock()
        mock_doc_ref.id = "test_message_id"
        mock_messages_collection.add.return_value = (None, mock_doc_ref)
        
        message_data = {
            "customer_id": "test_customer_id",
            "content": "Test manual message",
            "direction": "outbound",
            "source": "manual"
        }
        
        response = client.post("/messages/manual", headers=auth_headers, json=message_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_message_id"
        assert data["content"] == "Test manual message"

class TestNewMessageEndpointsUnit:
    """Unit tests for the new message endpoints with mocked dependencies."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": VALID_API_KEY, "Content-Type": "application/json"}
    
    @patch('app.routes.messages.generate_initial_message')
    @patch('app.routes.messages.send_sms')
    def test_send_initial_sms_success_mocked(self, mock_send_sms, mock_generate_message, auth_headers):
        """Test initial SMS message sending with mocked dependencies."""
        from tests.test_app import mock_customers_collection, mock_messages_collection
        
        # Mock AI message generation
        mock_generate_message.return_value = "Hi John! Welcome to our service. We're excited to have you!"
        
        # Mock SMS sending
        mock_send_sms.return_value = "test_twilio_sid"
        
        # Mock customer creation (customer not found initially)
        mock_customers_collection.where.return_value.stream.return_value = []
        mock_doc_ref = Mock()
        mock_doc_ref.id = "new_customer_id"
        mock_customers_collection.add.return_value = (None, mock_doc_ref)
        
        # Mock message saving
        mock_message_ref = Mock()
        mock_message_ref.id = "new_message_id"
        mock_messages_collection.add.return_value = (None, mock_message_ref)
        
        request_data = {
            "name": "John Doe",
            "phone": "+1234567890",
            "message_type": "welcome",
            "context": "New customer onboarding"
        }
        
        response = client.post("/messages/initial/sms", headers=auth_headers, json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message_id"] == "new_message_id"
        assert data["customer_id"] == "new_customer_id"
        assert data["twilio_sid"] == "test_twilio_sid"
    
    @patch('app.routes.messages.generate_initial_message')
    def test_send_initial_demo_success_mocked(self, mock_generate_message, auth_headers):
        """Test initial demo message generation with mocked dependencies."""
        # Mock AI message generation
        mock_generate_message.return_value = "Hello Jane! Thank you for your recent visit. How was your experience?"
        
        request_data = {
            "name": "Jane Doe",
            "message_type": "follow-up",
            "context": "Post-visit follow-up"
        }
        
        response = client.post("/messages/initial/demo", headers=auth_headers, json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["response_content"] == "Hello Jane! Thank you for your recent visit. How was your experience?"
        assert data["message_id"] is None  # Demo mode shouldn't save messages
    
    @patch('app.routes.messages.generate_ongoing_response')
    @patch('app.routes.messages.send_sms')
    def test_send_ongoing_sms_success_mocked(self, mock_send_sms, mock_generate_reply, auth_headers):
        """Test ongoing SMS conversation with mocked dependencies."""
        from tests.test_app import mock_customers_collection, mock_messages_collection
        
        # Mock customer lookup
        mock_customer_doc = Mock()
        mock_customer_doc.exists = True
        mock_customer_doc.id = "existing_customer_id"
        mock_customer_doc.to_dict.return_value = {
            "name": "John Doe",
            "phone": "+1234567890",
            "notes": "Regular customer"
        }
        mock_customers_collection.where.return_value.stream.return_value = [mock_customer_doc]
        
        # Mock message history retrieval
        mock_messages_collection.where.return_value.stream.return_value = []
        
        # Mock AI reply generation
        mock_generate_reply.return_value = "Thank you for your message! We'll get back to you soon."
        
        # Mock SMS sending
        mock_send_sms.return_value = "reply_twilio_sid"
        
        # Mock message saving
        mock_message_ref = Mock()
        mock_message_ref.id = "new_message_id"
        mock_messages_collection.add.return_value = (None, mock_message_ref)
        
        request_data = {
            "phone": "+1234567890",
            "message_content": "Hi, I have a question about my recent order",
            "context": "Customer inquiry"
        }
        
        response = client.post("/messages/ongoing/sms", headers=auth_headers, json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message_id"] == "new_message_id"
        assert data["customer_id"] == "existing_customer_id"
        assert data["twilio_sid"] == "reply_twilio_sid"
    
    @patch('app.routes.messages.generate_demo_response')
    def test_send_ongoing_demo_success_mocked(self, mock_generate_reply, auth_headers):
        """Test ongoing demo conversation with mocked dependencies."""
        # Mock AI reply generation
        mock_generate_reply.return_value = "I understand your concern. Let me help you with that right away."
        
        request_data = {
            "name": "Jane Doe",
            "message_history": [
                {"role": "user", "content": "Hi, I need help with my account"},
                {"role": "assistant", "content": "I'd be happy to help you with your account. What do you need assistance with?"}
            ],
            "message_content": "I can't access my payment history",
            "context": "Account support"
        }
        
        response = client.post("/messages/ongoing/demo", headers=auth_headers, json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["response_content"] == "I understand your concern. Let me help you with that right away."
        assert data["message_id"] is None  # Demo mode shouldn't save messages
    
    def test_initial_sms_invalid_data(self, auth_headers):
        """Test initial SMS endpoint with invalid data."""
        invalid_data = {
            "name": "",  # Empty name
            "phone": "+1234567890",
            "message_type": "welcome"
        }
        
        response = client.post("/messages/initial/sms", headers=auth_headers, json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_ongoing_sms_customer_not_found(self, auth_headers):
        """Test ongoing SMS when customer doesn't exist."""
        from tests.test_app import mock_customers_collection
        
        # Mock customer not found
        mock_customers_collection.where.return_value.stream.return_value = []
        
        request_data = {
            "phone": "+1999999999",
            "message_content": "Hello, I need help"
        }
        
        response = client.post("/messages/ongoing/sms", headers=auth_headers, json=request_data)
        assert response.status_code == 404
        assert "Customer not found" in response.text

class TestOpenAIIntegrationUnit:
    """Unit tests for OpenAI integration with mocked API calls."""
    
    @patch('app.utils.llm_client.openai_client')
    async def test_generate_outbound_message_mocked(self, mock_openai):
        """Test AI message generation (mocked)."""
        from app.utils.llm_client import generate_outbound_message
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hi John! Just checking in on your recent visit."
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        
        customer_data = {
            "name": "John Doe",
            "phone": "+1234567890",
            "tags": ["regular"],
            "last_visit": "2024-01-15"
        }
        
        result = await generate_outbound_message(customer_data, "Follow-up message")
        assert "John" in result
        assert len(result) > 0
        mock_openai.chat.completions.create.assert_called_once()
    
    @patch('app.utils.llm_client.openai_client')
    async def test_generate_auto_reply_mocked(self, mock_openai):
        """Test AI auto-reply generation (mocked)."""
        from app.utils.llm_client import generate_auto_reply
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """AUTO_REPLY: Thanks for your message! We'll get back to you soon.
ESCALATE: false
REASON: Simple greeting, can be handled automatically"""
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        
        customer_data = {"name": "John Doe", "phone": "+1234567890"}
        reply, escalate = await generate_auto_reply("Hello!", customer_data, [])
        
        assert reply is not None
        assert "Thanks for your message" in reply
        assert escalate is False
        mock_openai.chat.completions.create.assert_called_once()
    
    @patch('app.utils.llm_client.openai_client')
    async def test_analyze_message_sentiment_mocked(self, mock_openai):
        """Test message sentiment analysis (mocked)."""
        from app.utils.llm_client import analyze_message_sentiment
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """SENTIMENT: negative
URGENCY: high
KEYWORDS: billing, refund, angry
ESCALATE: true
REASON: Customer is angry about billing issue"""
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await analyze_message_sentiment("I'm very upset about this billing error! I want my money back!")
        assert result["sentiment"] == "negative"
        assert result["urgency"] == "high"
        assert result["escalate"] is True
        mock_openai.chat.completions.create.assert_called_once()

class TestTwilioIntegrationUnit:
    """Unit tests for Twilio integration with mocked API calls."""
    
    @patch('app.utils.twilio_client.twilio_client')
    async def test_send_sms_success_mocked(self, mock_twilio):
        """Test SMS sending success (mocked)."""
        from app.utils.twilio_client import send_sms
        
        # Mock Twilio response
        mock_message = Mock()
        mock_message.sid = "test_message_sid"
        mock_twilio.messages.create.return_value = mock_message
        
        result = await send_sms("+1234567890", "Test message")
        assert result == "test_message_sid"
        mock_twilio.messages.create.assert_called_once()
    
    @patch('app.utils.twilio_client.twilio_client')
    async def test_get_message_status_mocked(self, mock_twilio):
        """Test getting message status (mocked)."""
        from app.utils.twilio_client import get_message_status
        
        # Mock Twilio response
        mock_message = Mock()
        mock_message.sid = "test_sid"
        mock_message.status = "delivered"
        mock_message.error_code = None
        mock_message.error_message = None
        mock_message.date_sent = datetime.now()
        mock_message.date_updated = datetime.now()
        
        mock_twilio.messages.return_value.fetch.return_value = mock_message
        
        result = await get_message_status("test_sid")
        assert result["status"] == "delivered"
        assert result["sid"] == "test_sid"
    
    def test_format_phone_number_unit(self):
        """Test phone number formatting utility."""
        from app.utils.twilio_client import format_phone_number
        
        # Test cases
        assert format_phone_number("1234567890") == "+11234567890"
        assert format_phone_number("(123) 456-7890") == "+11234567890"
        assert format_phone_number("+1234567890") == "+1234567890"
        assert format_phone_number("11234567890") == "+11234567890"
        assert format_phone_number("123-456-7890") == "+11234567890"
    
    @patch('os.getenv')
    def test_verify_webhook_signature_mocked(self, mock_getenv):
        """Test webhook signature verification (mocked)."""
        from app.utils.twilio_client import verify_webhook_signature
        
        # Mock environment
        mock_getenv.return_value = "test_auth_token"
        
        # Test data
        url = "https://example.com/webhook"
        body = b"test_body"
        
        # This will fail verification with our test data, but that's expected
        result = verify_webhook_signature(body, "invalid_signature", url)
        assert result is False
        
        # Test with no auth token
        mock_getenv.return_value = None
        result = verify_webhook_signature(body, "any_signature", url)
        assert result is False

class TestValidationUnit:
    """Unit tests for data validation."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": VALID_API_KEY, "Content-Type": "application/json"}
    
    def test_create_customer_invalid_data(self, auth_headers):
        """Test customer creation with invalid data."""
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "phone": "+1234567890"
        }
        
        response = client.post("/customers", headers=auth_headers, json=invalid_data)
        assert response.status_code == 422  # Validation error
        
        # Test missing phone
        invalid_data2 = {
            "name": "John Doe"
            # Missing phone
        }
        
        response2 = client.post("/customers", headers=auth_headers, json=invalid_data2)
        assert response2.status_code == 422
    
    def test_invalid_json_request(self, auth_headers):
        """Test handling of invalid JSON."""
        response = client.post("/customers", headers=auth_headers, content="invalid json")
        assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
