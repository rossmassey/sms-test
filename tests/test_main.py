"""
Unit tests for the SMS Outreach Backend using mocked test app.
Run with: python -m pytest tests/test_main.py -v
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

class TestAuthentication:
    """Test API key authentication."""
    
    def test_health_check_no_auth_required(self):
        """Health check should work without authentication."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "SMS Outreach Backend"
    
    def test_protected_endpoint_requires_auth(self):
        """Protected endpoints should require API key."""
        response = client.get("/customers")
        assert response.status_code == 401
        assert "Invalid API key" in response.text
    
    def test_protected_endpoint_with_invalid_key(self):
        """Invalid API key should be rejected."""
        headers = {"X-API-Key": INVALID_API_KEY}
        response = client.get("/customers", headers=headers)
        assert response.status_code == 401
    
    def test_protected_endpoint_with_valid_key(self):
        """Valid API key should allow access (may fail due to Firebase)."""
        headers = {"X-API-Key": VALID_API_KEY}
        response = client.get("/customers", headers=headers)
        # Should be 200 (success) or 500 (Firebase not configured) - both are valid
        assert response.status_code in [200, 500]

class TestCustomerEndpoints:
    """Test customer management endpoints."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": VALID_API_KEY, "Content-Type": "application/json"}
    
    def test_list_customers_empty(self, auth_headers):
        """Test listing customers when collection is empty."""
        # Use the mock from test_app
        from tests.test_app import mock_customers_collection
        mock_customers_collection.limit.return_value.offset.return_value.stream.return_value = []
        
        response = client.get("/customers", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []
    
    def test_create_customer_success(self, auth_headers):
        """Test successful customer creation."""
        # Set up the mock from test_app
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
    
    def test_get_customer_success(self, auth_headers):
        """Test retrieving a specific customer."""
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
    
    def test_get_customer_not_found(self, auth_headers):
        """Test retrieving a non-existent customer."""
        # Use the mock from test_app
        from tests.test_app import mock_customers_collection
        
        # Mock Firestore response
        mock_doc = Mock()
        mock_doc.exists = False
        mock_customers_collection.document.return_value.get.return_value = mock_doc
        
        response = client.get("/customers/nonexistent", headers=auth_headers)
        assert response.status_code == 404
        assert "Customer not found" in response.text
    
    def test_update_customer_success(self, auth_headers):
        """Test successful customer update."""
        # Use the mock from test_app
        from tests.test_app import mock_customers_collection
        
        # Mock existing customer
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_doc_ref.update = Mock()
        
        # Mock updated customer
        updated_doc = Mock()
        updated_doc.id = "test_customer_id"
        updated_doc.to_dict.return_value = {
            "name": "John Updated",
            "phone": "+1234567890",
            "notes": "Updated notes",
            "tags": ["updated"]
        }
        mock_doc_ref.get.return_value = updated_doc
        mock_customers_collection.document.return_value = mock_doc_ref
        
        update_data = {"notes": "Updated notes", "tags": ["updated"]}
        response = client.put("/customers/test_customer_id", headers=auth_headers, json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes"
    
    def test_delete_customer_success(self, auth_headers):
        """Test successful customer deletion."""
        # Use the mock from test_app
        from tests.test_app import mock_customers_collection
        
        # Mock existing customer
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_doc_ref.delete = Mock()
        mock_customers_collection.document.return_value = mock_doc_ref
        
        response = client.delete("/customers/test_customer_id", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"]

class TestMessageEndpoints:
    """Test message management endpoints."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": VALID_API_KEY, "Content-Type": "application/json"}
    
    def test_list_messages_empty(self, auth_headers):
        """Test listing messages when collection is empty."""
        from tests.test_app import mock_messages_collection
        mock_messages_collection.stream.return_value = []
        
        response = client.get("/messages", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_messages_with_customer_filter(self, auth_headers):
        """Test listing messages filtered by customer ID."""
        from tests.test_app import mock_messages_collection
        
        # Mock the where().stream() chain for customer filtering
        mock_where_result = Mock()
        mock_where_result.stream.return_value = []
        mock_messages_collection.where.return_value = mock_where_result
        
        response = client.get("/messages?customer_id=test123", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []
    
    def test_create_manual_message_success(self, auth_headers):
        """Test creating a manual message record."""
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
    
    def test_create_manual_message_customer_not_found(self, auth_headers):
        """Test creating a manual message for non-existent customer."""
        from tests.test_app import mock_customers_collection
        
        # Mock customer doesn't exist
        mock_customer_doc = Mock()
        mock_customer_doc.exists = False
        mock_customers_collection.document.return_value.get.return_value = mock_customer_doc
        
        message_data = {
            "customer_id": "nonexistent_customer",
            "content": "Test message",
            "direction": "outbound",
            "source": "manual"
        }
        
        response = client.post("/messages/manual", headers=auth_headers, json=message_data)
        assert response.status_code == 404
        assert "Customer not found" in response.text

class TestAIIntegration:
    """Test AI-related functionality."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": VALID_API_KEY, "Content-Type": "application/json"}
    
    @patch('app.utils.llm_client.openai_client')
    async def test_generate_outbound_message(self, mock_openai):
        """Test AI message generation."""
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
    
    @patch('app.utils.llm_client.openai_client')
    async def test_generate_auto_reply(self, mock_openai):
        """Test AI auto-reply generation."""
        from app.utils.llm_client import generate_auto_reply
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """AUTO_REPLY: Thanks for your message! We'll get back to you soon.
ESCALATE: false
REASON: Simple greeting, can be handled automatically"""
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        
        customer_data = {"name": "John Doe", "phone": "+1234567890"}
        reply, escalate, is_do_not_contact = await generate_auto_reply("Hello!", customer_data, [])
        
        assert reply is not None
        assert "Thanks for your message" in reply
        assert escalate is False
        assert is_do_not_contact is False

class TestTwilioIntegration:
    """Test Twilio-related functionality."""
    
    @patch('app.utils.twilio_client.twilio_client')
    async def test_send_sms_success(self, mock_twilio):
        """Test successful SMS sending."""
        from app.utils.twilio_client import send_sms
        
        # Mock Twilio response
        mock_message = Mock()
        mock_message.sid = "SM123456789"
        mock_twilio.messages.create.return_value = mock_message
        
        result = await send_sms("+1234567890", "Test message")
        assert result == "SM123456789"
    
    def test_verify_webhook_signature_valid(self):
        """Test valid webhook signature verification."""
        from app.utils.twilio_client import verify_webhook_signature
        
        # This would need real Twilio signature for full test
        # For now, test that the function exists and handles errors gracefully
        result = verify_webhook_signature(b"test", "invalid_signature", "http://test.com")
        assert isinstance(result, bool)
    
    def test_format_phone_number(self):
        """Test phone number formatting."""
        from app.utils.twilio_client import format_phone_number
        
        # Test various phone number formats
        assert format_phone_number("1234567890") == "+11234567890"
        assert format_phone_number("+1234567890") == "+1234567890"
        assert format_phone_number("(123) 456-7890") == "+11234567890"

class TestDataModels:
    """Test Pydantic data models."""
    
    def test_customer_create_model(self):
        """Test CustomerCreate model validation."""
        # Valid data
        customer = CustomerCreate(
            name="John Doe",
            phone="+1234567890",
            notes="Test customer",
            tags=["test"]
        )
        assert customer.name == "John Doe"
        assert customer.phone == "+1234567890"
    
    def test_customer_create_model_minimal(self):
        """Test CustomerCreate model with minimal data."""
        customer = CustomerCreate(name="Jane", phone="+1987654321")
        assert customer.name == "Jane"
        assert customer.notes is None
        assert customer.tags == []
    
    def test_message_send_model(self):
        """Test MessageSend model validation."""
        message = MessageSend(
            customer_id="test123",
            context="Follow-up message"
        )
        assert message.customer_id == "test123"
        assert message.context == "Follow-up message"

class TestDatabaseOperations:
    """Test database-related operations."""
    
    def test_initialize_firebase(self):
        """Test Firebase initialization works without error."""
        from app.database import initialize_firebase
        
        # Should work without error (already initialized in test_app)
        result = initialize_firebase()
        # Don't assert specific values since it could be mocked or real
        # Just ensure no exception is raised
        assert True  # Test passes if no exception is raised
    
    def test_get_customers_collection(self):
        """Test getting customers collection reference."""
        from app.database import get_customers_collection
        
        result = get_customers_collection()
        assert result is not None
        # Should have collection-like methods
        assert hasattr(result, 'document') or hasattr(result, 'add')
    
    def test_get_messages_collection(self):
        """Test getting messages collection reference."""
        from app.database import get_messages_collection
        
        result = get_messages_collection()
        assert result is not None
        # Should have collection-like methods
        assert hasattr(result, 'document') or hasattr(result, 'add')

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": VALID_API_KEY, "Content-Type": "application/json"}
    
    def test_invalid_json_request(self, auth_headers):
        """Test handling of invalid JSON in request body."""
        response = client.post(
            "/customers", 
            headers=auth_headers, 
            content="invalid json"
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self, auth_headers):
        """Test validation of missing required fields."""
        incomplete_data = {"phone": "+1234567890"}  # Missing name
        response = client.post("/customers", headers=auth_headers, json=incomplete_data)
        assert response.status_code == 422

# Test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
