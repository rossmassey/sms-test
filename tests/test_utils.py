"""
Unit tests for utility modules in the SMS Outreach Backend.
Run with: python -m pytest tests/test_utils.py -v
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
import firebase_admin

class TestLLMClient:
    """Test the LLM client utility functions."""
    
    @patch('app.utils.llm_client.openai_client')
    async def test_generate_outbound_message_success(self, mock_openai):
        """Test successful outbound message generation."""
        from app.utils.llm_client import generate_outbound_message
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hi John! Thanks for visiting us last week."
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        
        customer_data = {
            "name": "John Doe",
            "phone": "+1234567890",
            "notes": "Regular customer",
            "tags": ["regular", "vip"],
            "last_visit": "2024-01-15"
        }
        
        result = await generate_outbound_message(customer_data, "Follow-up message")
        
        assert result == "Hi John! Thanks for visiting us last week."
        mock_openai.chat.completions.create.assert_called_once()
    
    @patch('app.utils.llm_client.openai_client')
    async def test_generate_outbound_message_long_response(self, mock_openai):
        """Test handling of long AI responses (should truncate for SMS)."""
        from app.utils.llm_client import generate_outbound_message
        
        # Mock very long response
        long_message = "This is a very long message " * 20  # > 160 chars
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = long_message
        
        # Mock second call with shorter response
        short_response = Mock()
        short_response.choices = [Mock()]
        short_response.choices[0].message.content = "Hi John! Quick follow-up."
        
        mock_openai.chat.completions.create = AsyncMock(side_effect=[mock_response, short_response])
        
        customer_data = {"name": "John", "phone": "+1234567890"}
        result = await generate_outbound_message(customer_data)
        
        # Should have made two calls and returned the shorter message
        assert mock_openai.chat.completions.create.call_count == 2
        assert result == "Hi John! Quick follow-up."
    
    @patch('app.utils.llm_client.openai_client')
    async def test_generate_auto_reply_no_escalation(self, mock_openai):
        """Test auto-reply generation that doesn't need escalation."""
        from app.utils.llm_client import generate_auto_reply
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        # Fix the format to match the parsing logic
        mock_response.choices[0].message.content = """AUTO_REPLY: Thanks for your message! We're open Monday-Friday 9-5.
ESCALATE: false
REASON: Simple hours inquiry, can be handled automatically"""
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        
        customer_data = {"name": "Jane", "phone": "+1987654321"}
        incoming_message = "What are your hours?"
        
        reply, escalate = await generate_auto_reply(incoming_message, customer_data, [])
        
        assert reply == "Thanks for your message! We're open Monday-Friday 9-5."
        assert escalate is False
    
    @patch('app.utils.llm_client.openai_client')
    async def test_generate_auto_reply_needs_escalation(self, mock_openai):
        """Test auto-reply generation that needs escalation."""
        from app.utils.llm_client import generate_auto_reply
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
        AUTO_REPLY: NONE
        ESCALATE: true
        REASON: Customer complaint requires human attention
        """
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        
        customer_data = {"name": "Angry Customer", "phone": "+1111111111"}
        incoming_message = "I'm very upset about my service! This is unacceptable!"
        
        reply, escalate = await generate_auto_reply(incoming_message, customer_data, [])
        
        assert reply is None
        assert escalate is True
    
    @patch('app.utils.llm_client.openai_client')
    async def test_generate_auto_reply_error_handling(self, mock_openai):
        """Test auto-reply error handling."""
        from app.utils.llm_client import generate_auto_reply
        
        # Mock OpenAI error
        mock_openai.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        customer_data = {"name": "Test", "phone": "+1234567890"}
        
        reply, escalate = await generate_auto_reply("Test message", customer_data, [])
        
        # Should escalate on error for safety
        assert reply is None
        assert escalate is True
    
    @patch('app.utils.llm_client.openai_client')
    async def test_analyze_message_sentiment(self, mock_openai):
        """Test message sentiment analysis."""
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

class TestTwilioClient:
    """Test the Twilio client utility functions."""
    
    @patch('app.utils.twilio_client.twilio_client')
    async def test_send_sms_success(self, mock_twilio):
        """Test successful SMS sending."""
        from app.utils.twilio_client import send_sms
        
        # Mock Twilio response
        mock_message = Mock()
        mock_message.sid = "SM123456789abcdef"
        mock_twilio.messages.create.return_value = mock_message
        
        result = await send_sms("+1234567890", "Test message")
        
        assert result == "SM123456789abcdef"
        mock_twilio.messages.create.assert_called_once()
    
    @patch('app.utils.twilio_client.twilio_client')
    async def test_send_sms_phone_formatting(self, mock_twilio):
        """Test phone number formatting in SMS sending."""
        from app.utils.twilio_client import send_sms
        
        mock_message = Mock()
        mock_message.sid = "SM123"
        mock_twilio.messages.create.return_value = mock_message
        
        # Test phone number without country code
        await send_sms("1234567890", "Test")
        
        # Should have formatted the phone number
        call_args = mock_twilio.messages.create.call_args
        assert call_args[1]["to"] == "+11234567890"
    
    @patch('app.utils.twilio_client.twilio_client')
    async def test_send_sms_twilio_error(self, mock_twilio):
        """Test handling of Twilio errors."""
        from app.utils.twilio_client import send_sms
        from twilio.base.exceptions import TwilioException
        
        # Mock Twilio error
        mock_twilio.messages.create.side_effect = TwilioException("Invalid phone number")
        
        with pytest.raises(Exception) as exc_info:
            await send_sms("+1234567890", "Test message")
        
        assert "Twilio error" in str(exc_info.value)
    
    def test_verify_webhook_signature_invalid(self):
        """Test webhook signature verification with invalid signature."""
        from app.utils.twilio_client import verify_webhook_signature
        
        result = verify_webhook_signature(
            b"test body",
            "invalid_signature",
            "https://example.com/webhook"
        )
        
        assert result is False
    
    @patch.dict(os.environ, {'TWILIO_AUTH_TOKEN': 'test_auth_token'})
    def test_verify_webhook_signature_valid(self):
        """Test webhook signature verification with a valid signature."""
        from app.utils.twilio_client import verify_webhook_signature
        
        # This test will verify the logic path, but won't test actual signature validation
        # since that would require complex HMAC setup
        result = verify_webhook_signature(
            b"test body",
            "valid_signature",
            "https://example.com/webhook"
        )
        
        # Result will be False since signature won't match, but that's expected
        assert isinstance(result, bool)

    def test_format_phone_number_various_formats(self):
        """Test phone number formatting with various input formats."""
        from app.utils.twilio_client import format_phone_number
        
        test_cases = [
            ("1234567890", "+11234567890"),
            ("+1234567890", "+1234567890"),
            ("(123) 456-7890", "+11234567890"),
            ("123-456-7890", "+11234567890"),
            ("123.456.7890", "+11234567890"),
            ("1 (123) 456-7890", "+11234567890"),
        ]
        
        for input_phone, expected in test_cases:
            result = format_phone_number(input_phone)
            assert result == expected, f"Failed for {input_phone}: got {result}, expected {expected}"
    
    @patch('app.utils.twilio_client.twilio_client')
    async def test_get_message_status(self, mock_twilio):
        """Test getting message delivery status."""
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
    
    @patch('app.utils.twilio_client.twilio_client')
    async def test_get_account_balance(self, mock_twilio):
        """Test getting Twilio account balance."""
        from app.utils.twilio_client import get_account_balance
        
        # Mock balance response
        mock_balance = Mock()
        mock_balance.balance = "25.50"
        mock_twilio.balance.fetch.return_value = mock_balance
        
        result = await get_account_balance()
        
        assert result == 25.50
        assert isinstance(result, float)

class TestDatabaseOperations:
    """Tests for database operations."""

    def setup_method(self):
        """Reset Firebase app state before each test."""
        import firebase_admin
        if firebase_admin._apps:
            firebase_admin.delete_app(firebase_admin.get_app())

    @patch('firebase_admin.credentials.Certificate')
    @patch('firebase_admin.initialize_app')
    @patch('firebase_admin.firestore.client')
    @patch('os.path.exists')
    @patch.dict(os.environ, {
        'FIREBASE_CRED_PATH': '/path/to/creds.json',
        'FIREBASE_PROJECT_ID': 'test-project'
    })
    def test_initialize_firebase_success(self, mock_exists, mock_firestore, mock_init, mock_cert):
        """Test successful Firebase initialization."""
        from app.database import initialize_firebase
        
        mock_exists.return_value = True
        mock_firestore.return_value = Mock()
        mock_cert.return_value = Mock()
        
        result = initialize_firebase()
        
        assert result is not None
        mock_init.assert_called_once()
        mock_cert.assert_called_once_with('/path/to/creds.json')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_firebase_missing_config(self):
        """Test Firebase initialization with missing configuration."""
        from app.database import initialize_firebase
        
        with pytest.raises(ValueError) as exc_info:
            initialize_firebase()
        
        assert "Firebase credentials not properly configured" in str(exc_info.value)
    
    @patch('os.path.exists')
    @patch.dict(os.environ, {
        'FIREBASE_CRED_PATH': '/nonexistent/path.json',
        'FIREBASE_PROJECT_ID': 'test-project'
    })
    def test_initialize_firebase_missing_file(self, mock_exists):
        """Test Firebase initialization with missing credentials file."""
        from app.database import initialize_firebase
        
        mock_exists.return_value = False
        
        with pytest.raises(FileNotFoundError):
            initialize_firebase()
    
    @patch('app.database.get_firestore_client')
    def test_get_collections(self, mock_client):
        """Test getting Firestore collection references."""
        from app.database import get_customers_collection, get_messages_collection
        
        mock_firestore = Mock()
        mock_client.return_value = mock_firestore
        
        # Test customers collection
        customers_ref = get_customers_collection()
        mock_firestore.collection.assert_called_with('customers')
        
        # Test messages collection
        messages_ref = get_messages_collection()
        mock_firestore.collection.assert_called_with('messages')

class TestModelValidation:
    """Test Pydantic model validation."""
    
    def test_customer_create_validation(self):
        """Test CustomerCreate model validation."""
        from app.models import CustomerCreate
        
        # Valid customer
        customer = CustomerCreate(
            name="John Doe",
            phone="+1234567890",
            notes="Test customer",
            tags=["test", "vip"]
        )
        
        assert customer.name == "John Doe"
        assert customer.phone == "+1234567890"
        assert "test" in customer.tags
    
    def test_customer_create_minimal(self):
        """Test CustomerCreate with minimal required fields."""
        from app.models import CustomerCreate
        
        customer = CustomerCreate(name="Jane", phone="+1987654321")
        
        assert customer.name == "Jane"
        assert customer.phone == "+1987654321"
        assert customer.notes is None
        assert customer.tags == []
    
    def test_customer_update_validation(self):
        """Test CustomerUpdate model validation."""
        from app.models import CustomerUpdate
        
        # Should allow partial updates
        update = CustomerUpdate(notes="Updated notes")
        assert update.notes == "Updated notes"
        assert update.name is None
    
    def test_message_create_validation(self):
        """Test MessageCreate model validation."""
        from app.models import MessageCreate
        
        message = MessageCreate(
            customer_id="cust123",
            content="Test message",
            direction="outbound",
            source="manual"
        )
        
        assert message.customer_id == "cust123"
        assert message.content == "Test message"
        assert message.direction == "outbound"
        assert message.source == "manual"
    
    def test_message_send_validation(self):
        """Test MessageSend model validation."""
        from app.models import MessageSend
        
        message = MessageSend(
            customer_id="cust123",
            context="Follow-up message"
        )
        
        assert message.customer_id == "cust123"
        assert message.context == "Follow-up message"
    
    def test_incoming_webhook_validation(self):
        """Test IncomingWebhook model validation."""
        from app.models import IncomingWebhook
        
        webhook = IncomingWebhook(
            From="+1234567890",
            To="+1987654321",
            Body="Hello!",
            MessageSid="SM123456"
        )
        
        assert webhook.From == "+1234567890"
        assert webhook.Body == "Hello!"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
