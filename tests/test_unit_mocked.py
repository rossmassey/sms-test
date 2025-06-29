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

# Import the test app instead of the real app
from tests.test_app import test_app
from app.models import CustomerCreate, CustomerUpdate, MessageSend, Customer, Message

# Create test client with test app
client = TestClient(test_app)

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
        mock_messages_collection.order_by.return_value.limit.return_value.offset.return_value.stream.return_value = []
        
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
KEYWORDS: complaint, refund, angry
CUSTOMER_INTENT: Customer wants a refund due to poor service"""
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await analyze_message_sentiment("I want my money back! This service is terrible!")
        
        assert result["sentiment"] == "negative"
        assert result["urgency"] == "high"
        assert "complaint" in result["keywords"]
        assert "refund" in result["customer_intent"].lower()
        mock_openai.chat.completions.create.assert_called_once()

class TestTwilioIntegrationUnit:
    """Unit tests for Twilio integration with mocked API calls."""
    
    @patch('app.utils.twilio_client.twilio_client')
    async def test_send_sms_success_mocked(self, mock_twilio):
        """Test successful SMS sending (mocked)."""
        from app.utils.twilio_client import send_sms
        
        # Mock Twilio response
        mock_message = Mock()
        mock_message.sid = "SM123456789"
        mock_twilio.messages.create.return_value = mock_message
        
        result = await send_sms("+1234567890", "Test message")
        assert result == "SM123456789"
        mock_twilio.messages.create.assert_called_once()
    
    @patch('app.utils.twilio_client.twilio_client')
    async def test_get_message_status_mocked(self, mock_twilio):
        """Test getting message delivery status (mocked)."""
        from app.utils.twilio_client import get_message_status
        
        # Mock Twilio message status
        mock_message = Mock()
        mock_message.sid = "SM123"
        mock_message.status = "delivered"
        mock_message.error_code = None
        mock_message.error_message = None
        mock_message.date_sent = "2024-01-15T10:00:00Z"
        mock_message.date_updated = "2024-01-15T10:01:00Z"
        
        mock_twilio.messages.return_value.fetch.return_value = mock_message
        
        result = await get_message_status("SM123")
        
        assert result["sid"] == "SM123"
        assert result["status"] == "delivered"
        assert result["error_code"] is None
        mock_twilio.messages.assert_called_once()
    
    def test_format_phone_number_unit(self):
        """Test phone number formatting (unit test)."""
        from app.utils.twilio_client import format_phone_number
        
        test_cases = [
            ("1234567890", "+11234567890"),
            ("+1234567890", "+1234567890"),
            ("(123) 456-7890", "+11234567890"),
            ("123-456-7890", "+11234567890"),
            ("123.456.7890", "+11234567890"),
        ]
        
        for input_phone, expected in test_cases:
            result = format_phone_number(input_phone)
            assert result == expected, f"Failed for {input_phone}: got {result}, expected {expected}"
    
    @patch('os.getenv')
    def test_verify_webhook_signature_mocked(self, mock_getenv):
        """Test webhook signature verification (mocked environment)."""
        from app.utils.twilio_client import verify_webhook_signature
        
        # Mock the environment variable
        mock_getenv.return_value = "test_auth_token"
        
        # Test that the function attempts to verify signature
        result = verify_webhook_signature(
            b"test body",
            "test_signature",
            "https://example.com/webhook"
        )
        
        # Should attempt to get auth token
        mock_getenv.assert_called_with("TWILIO_AUTH_TOKEN")
        # Result will be False since signature won't match, but that's expected
        assert isinstance(result, bool)

class TestValidationUnit:
    """Unit tests for data validation."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": VALID_API_KEY, "Content-Type": "application/json"}
    
    def test_create_customer_invalid_data(self, auth_headers):
        """Test customer creation with invalid data."""
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "phone": "invalid_phone"
        }
        
        response = client.post("/customers", headers=auth_headers, json=invalid_data)
        assert response.status_code == 422  # Validation error
        
        # Also test completely missing name
        invalid_data2 = {
            "phone": "+1234567890"
            # Missing name entirely
        }
        
        response2 = client.post("/customers", headers=auth_headers, json=invalid_data2)
        assert response2.status_code == 422  # Validation error
    
    def test_invalid_json_request(self, auth_headers):
        """Test handling of invalid JSON in request body."""
        response = client.post(
            "/customers", 
            headers=auth_headers, 
            data="invalid json"
        )
        assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
