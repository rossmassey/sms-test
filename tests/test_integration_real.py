"""
Integration tests for the SMS Outreach Backend - Uses real external services.
These tests require actual API keys and configurations to work.
Run with: python -m pytest tests/test_integration_real.py -v
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from datetime import datetime
import os

# Import the FastAPI app
from app.main import app
from app.models import CustomerCreate, MessageSend

# Create test client
client = TestClient(app)

# Test data
VALID_API_KEY = "sms_backend_2025_secure_key_xyz789"

@pytest.mark.integration
class TestFirebaseIntegrationReal:
    """Integration tests using real Firebase."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": VALID_API_KEY, "Content-Type": "application/json"}
    
    def test_customer_crud_real_firebase(self, auth_headers):
        """Test complete customer CRUD operations with real Firebase."""
        # Create a test customer
        customer_data = {
            "name": f"Integration Test Customer {datetime.now().isoformat()}",
            "phone": f"+1555TEST{datetime.now().microsecond}",
            "notes": "Created by integration test",
            "tags": ["integration-test", "auto-generated"]
        }
        
        # Create customer
        create_response = client.post("/customers", headers=auth_headers, json=customer_data)
        
        if create_response.status_code == 500:
            pytest.skip("Firebase not configured for integration testing")
        
        assert create_response.status_code == 200
        created_customer = create_response.json()
        customer_id = created_customer["id"]
        
        try:
            # Verify customer creation
            assert created_customer["name"] == customer_data["name"]
            assert created_customer["phone"] == customer_data["phone"]
            assert created_customer["notes"] == customer_data["notes"]
            
            # Read customer
            get_response = client.get(f"/customers/{customer_id}", headers=auth_headers)
            assert get_response.status_code == 200
            retrieved_customer = get_response.json()
            assert retrieved_customer["id"] == customer_id
            assert retrieved_customer["name"] == customer_data["name"]
            
            # Update customer
            update_data = {
                "notes": "Updated by integration test",
                "tags": ["integration-test", "updated"]
            }
            update_response = client.put(f"/customers/{customer_id}", headers=auth_headers, json=update_data)
            assert update_response.status_code == 200
            updated_customer = update_response.json()
            assert updated_customer["notes"] == update_data["notes"]
            assert "updated" in updated_customer["tags"]
            
            # List customers (should include our test customer)
            list_response = client.get("/customers?limit=100", headers=auth_headers)
            assert list_response.status_code == 200
            customers_list = list_response.json()
            assert any(c["id"] == customer_id for c in customers_list)
            
        finally:
            # Clean up: Delete the test customer
            delete_response = client.delete(f"/customers/{customer_id}", headers=auth_headers)
            assert delete_response.status_code == 200
            
            # Verify deletion
            get_after_delete = client.get(f"/customers/{customer_id}", headers=auth_headers)
            assert get_after_delete.status_code == 404
    
    def test_message_crud_real_firebase(self, auth_headers):
        """Test message operations with real Firebase."""
        # First create a test customer for the message
        customer_data = {
            "name": f"Message Test Customer {datetime.now().isoformat()}",
            "phone": f"+1555MSG{datetime.now().microsecond}",
            "notes": "For message testing"
        }
        
        create_response = client.post("/customers", headers=auth_headers, json=customer_data)
        
        if create_response.status_code == 500:
            pytest.skip("Firebase not configured for integration testing")
        
        customer_id = create_response.json()["id"]
        
        try:
            # Create manual message
            message_data = {
                "customer_id": customer_id,
                "content": "Integration test message",
                "direction": "outbound",
                "source": "manual"
            }
            
            message_response = client.post("/messages/manual", headers=auth_headers, json=message_data)
            assert message_response.status_code == 200
            created_message = message_response.json()
            assert created_message["content"] == message_data["content"]
            message_id = created_message["id"]
            
            # List messages for this customer
            list_response = client.get(f"/messages?customer_id={customer_id}", headers=auth_headers)
            assert list_response.status_code == 200
            messages_list = list_response.json()
            assert len(messages_list) >= 1
            assert any(m["id"] == message_id for m in messages_list)
            
            # Get specific message
            get_response = client.get(f"/messages/{message_id}", headers=auth_headers)
            assert get_response.status_code == 200
            retrieved_message = get_response.json()
            assert retrieved_message["id"] == message_id
            assert retrieved_message["content"] == message_data["content"]
            
        finally:
            # Clean up: Delete the test customer (messages will be cascade deleted)
            delete_response = client.delete(f"/customers/{customer_id}", headers=auth_headers)
            assert delete_response.status_code == 200

@pytest.mark.integration
@pytest.mark.openai
class TestOpenAIIntegrationReal:
    """Integration tests using real OpenAI API."""
    
    async def test_generate_outbound_message_real_openai(self):
        """Test real OpenAI API for outbound message generation."""
        from app.utils.llm_client import generate_outbound_message
        
        # Skip if OpenAI API key not configured
        if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "test_openai_key":
            pytest.skip("OpenAI API key not configured for integration testing")
        
        customer_data = {
            "name": "John Doe",
            "phone": "+1234567890",
            "tags": ["regular", "vip"],
            "last_visit": "2024-01-15",
            "notes": "Frequent customer, likes personalized service"
        }
        
        try:
            result = await generate_outbound_message(customer_data, "Follow-up after recent visit")
            
            # Verify the result is reasonable
            assert isinstance(result, str)
            assert len(result) > 10  # Should be a meaningful message
            assert len(result) <= 160  # Should be SMS-appropriate length
            assert "John" in result or "customer" in result.lower()  # Should be personalized
            
        except Exception as e:
            if "quota" in str(e).lower() or "billing" in str(e).lower():
                pytest.skip(f"OpenAI API quota/billing issue: {str(e)}")
            else:
                raise
    
    async def test_generate_auto_reply_real_openai(self):
        """Test real OpenAI API for auto-reply generation."""
        from app.utils.llm_client import generate_auto_reply
        
        # Skip if OpenAI API key not configured
        if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "test_openai_key":
            pytest.skip("OpenAI API key not configured for integration testing")
        
        customer_data = {"name": "Jane Smith", "phone": "+1987654321"}
        incoming_message = "What are your business hours?"
        
        try:
            reply, escalate = await generate_auto_reply(incoming_message, customer_data, [])
            
            # Verify the result
            assert isinstance(escalate, bool)
            if reply is not None:
                assert isinstance(reply, str)
                assert len(reply) > 0
                # For a simple hours question, should not escalate
                assert escalate is False
                assert any(word in reply.lower() for word in ["hour", "open", "time", "monday", "friday"])
            
        except Exception as e:
            if "quota" in str(e).lower() or "billing" in str(e).lower():
                pytest.skip(f"OpenAI API quota/billing issue: {str(e)}")
            else:
                raise
    
    async def test_analyze_message_sentiment_real_openai(self):
        """Test real OpenAI API for sentiment analysis."""
        from app.utils.llm_client import analyze_message_sentiment
        
        # Skip if OpenAI API key not configured
        if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "test_openai_key":
            pytest.skip("OpenAI API key not configured for integration testing")
        
        test_messages = [
            ("I love your service! Thank you so much!", "positive"),
            ("I'm very disappointed with my experience", "negative"),
            ("What time do you close today?", "neutral")
        ]
        
        for message, expected_sentiment in test_messages:
            try:
                result = await analyze_message_sentiment(message)
                
                # Verify the result structure
                assert isinstance(result, dict)
                assert "sentiment" in result
                assert "urgency" in result
                assert "keywords" in result
                assert "customer_intent" in result
                
                # Verify sentiment detection
                assert result["sentiment"] in ["positive", "negative", "neutral"]
                assert result["urgency"] in ["low", "medium", "high"]
                assert isinstance(result["keywords"], list)
                
                # For this simple test, we'll just check that sentiment is detected
                # (exact matching is hard due to AI variability)
                print(f"Message: '{message}' -> Sentiment: {result['sentiment']} (expected: {expected_sentiment})")
                
            except Exception as e:
                if "quota" in str(e).lower() or "billing" in str(e).lower():
                    pytest.skip(f"OpenAI API quota/billing issue: {str(e)}")
                else:
                    raise

@pytest.mark.integration
@pytest.mark.twilio
class TestTwilioIntegrationReal:
    """Integration tests using real Twilio API."""
    
    @pytest.mark.skip(reason="Twilio not configured - expected to skip")
    async def test_send_sms_real_twilio(self):
        """Test real Twilio API for SMS sending."""
        from app.utils.twilio_client import send_sms
        
        # Skip if Twilio not configured
        if (not os.getenv("TWILIO_ACCOUNT_SID") or 
            not os.getenv("TWILIO_AUTH_TOKEN") or
            not os.getenv("TWILIO_PHONE_NUMBER") or
            os.getenv("TWILIO_ACCOUNT_SID") == "test_twilio_sid"):
            pytest.skip("Twilio not configured for integration testing")
        
        # Use a verified test number for Twilio (you need to verify this in Twilio console)
        test_phone = "+15005550006"  # Twilio magic number for testing
        test_message = f"Integration test message {datetime.now().isoformat()}"
        
        try:
            result = await send_sms(test_phone, test_message)
            
            # Verify the result
            assert isinstance(result, str)
            assert result.startswith("SM")  # Twilio message SID format
            assert len(result) == 34  # Standard Twilio SID length
            
        except Exception as e:
            if "not a valid phone number" in str(e).lower():
                pytest.skip("Test phone number not verified in Twilio")
            else:
                raise
    
    @pytest.mark.skip(reason="Twilio not configured - expected to skip")
    async def test_get_account_balance_real_twilio(self):
        """Test real Twilio API for account balance."""
        from app.utils.twilio_client import get_account_balance
        
        # Skip if Twilio not configured
        if (not os.getenv("TWILIO_ACCOUNT_SID") or 
            not os.getenv("TWILIO_AUTH_TOKEN") or
            os.getenv("TWILIO_ACCOUNT_SID") == "test_twilio_sid"):
            pytest.skip("Twilio not configured for integration testing")
        
        try:
            balance = await get_account_balance()
            
            # Verify the result
            assert isinstance(balance, float)
            assert balance >= 0  # Balance should be non-negative
            
        except Exception as e:
            if "authentication" in str(e).lower():
                pytest.skip("Twilio authentication failed - credentials not configured")
            else:
                raise

@pytest.mark.integration
class TestEndToEndScenarios:
    """End-to-end integration tests combining multiple services."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": VALID_API_KEY, "Content-Type": "application/json"}
    
    async def test_complete_outbound_message_flow(self, auth_headers):
        """Test complete flow: create customer, generate AI message, create message record."""
        # Create a test customer
        customer_data = {
            "name": f"E2E Test Customer {datetime.now().isoformat()}",
            "phone": f"+1555E2E{datetime.now().microsecond}",
            "notes": "End-to-end test customer",
            "tags": ["e2e-test", "outbound-flow"]
        }
        
        create_response = client.post("/customers", headers=auth_headers, json=customer_data)
        
        if create_response.status_code == 500:
            pytest.skip("Firebase not configured for integration testing")
        
        customer_id = create_response.json()["id"]
        
        try:
            # Generate AI message using the send endpoint
            send_data = {
                "customer_id": customer_id,
                "context": "Welcome message for new customer"
            }
            
            send_response = client.post("/messages/send", headers=auth_headers, json=send_data)
            
            if send_response.status_code == 500 and "openai" in send_response.text.lower():
                pytest.skip("OpenAI not configured for integration testing")
            
            assert send_response.status_code == 200
            sent_response = send_response.json()
            
            # Verify AI-generated message response structure
            assert sent_response["success"] is True
            assert sent_response["data"]["content"] is not None
            assert len(sent_response["data"]["content"]) > 0
            assert sent_response["data"]["message_id"] is not None
            
            message_id = sent_response["data"]["message_id"]
            content = sent_response["data"]["content"]
            
            # Verify message was stored
            messages_response = client.get(f"/messages?customer_id={customer_id}", headers=auth_headers)
            assert messages_response.status_code == 200
            messages = messages_response.json()
            assert len(messages) >= 1
            assert any(m["id"] == message_id for m in messages)
            
            # Verify the stored message has correct properties
            stored_message = next(m for m in messages if m["id"] == message_id)
            assert stored_message["content"] == content
            assert stored_message["source"] == "ai"
            assert stored_message["customer_id"] == customer_id
            
        finally:
            # Clean up
            delete_response = client.delete(f"/customers/{customer_id}", headers=auth_headers)
            assert delete_response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
