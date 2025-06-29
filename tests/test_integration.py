"""
Integration tests for the SMS Outreach Backend.
These tests require actual services to be configured.
Run with: python -m pytest tests/test_integration.py -v
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app

# Create test client
client = TestClient(app)

VALID_API_KEY = "sms_backend_2025_secure_key_xyz789"

class TestRealFirebaseIntegration:
    """Integration tests with real Firebase (if configured)."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": VALID_API_KEY, "Content-Type": "application/json"}
    
    @pytest.mark.integration
    def test_real_customer_crud_flow(self, auth_headers):
        """Test complete customer CRUD flow with real Firebase."""
        # Create customer
        customer_data = {
            "name": "Integration Test Customer",
            "phone": "+1555123TEST",
            "notes": "Created during integration testing",
            "tags": ["integration", "test", "automated"]
        }
        
        create_response = client.post("/customers", headers=auth_headers, json=customer_data)
        
        if create_response.status_code == 500:
            pytest.skip("Firebase not configured for integration testing")
        
        assert create_response.status_code == 200
        created_customer = create_response.json()
        customer_id = created_customer["id"]
        
        try:
            # Read customer
            get_response = client.get(f"/customers/{customer_id}", headers=auth_headers)
            assert get_response.status_code == 200
            retrieved_customer = get_response.json()
            assert retrieved_customer["name"] == customer_data["name"]
            
            # Update customer
            update_data = {"notes": "Updated during integration testing"}
            update_response = client.put(f"/customers/{customer_id}", headers=auth_headers, json=update_data)
            assert update_response.status_code == 200
            updated_customer = update_response.json()
            assert updated_customer["notes"] == update_data["notes"]
            
            # List customers (should include our test customer)
            list_response = client.get("/customers", headers=auth_headers)
            assert list_response.status_code == 200
            customers = list_response.json()
            customer_ids = [c["id"] for c in customers]
            assert customer_id in customer_ids
            
        finally:
            # Cleanup: Delete the test customer
            delete_response = client.delete(f"/customers/{customer_id}", headers=auth_headers)
            assert delete_response.status_code == 200
    
    @pytest.mark.integration
    def test_real_message_creation_flow(self, auth_headers):
        """Test message creation with real Firebase."""
        # First create a test customer
        customer_data = {
            "name": "Message Test Customer",
            "phone": "+1555MSG TEST",
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
            
            # List messages for this customer
            list_response = client.get(f"/messages?customer_id={customer_id}", headers=auth_headers)
            assert list_response.status_code == 200
            messages = list_response.json()
            assert len(messages) >= 1
            
        finally:
            # Cleanup
            client.delete(f"/customers/{customer_id}", headers=auth_headers)

class TestRealOpenAIIntegration:
    """Integration tests with real OpenAI (if configured)."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": VALID_API_KEY, "Content-Type": "application/json"}
    
    @pytest.mark.integration
    @pytest.mark.openai
    def test_real_ai_message_generation(self, auth_headers):
        """Test AI message generation with real OpenAI API."""
        # First create a test customer
        customer_data = {
            "name": "AI Test Customer",
            "phone": "+1555AI TEST",
            "notes": "VIP customer, very important",
            "tags": ["vip", "regular"]
        }
        
        create_response = client.post("/customers", headers=auth_headers, json=customer_data)
        
        if create_response.status_code == 500:
            pytest.skip("Firebase not configured for integration testing")
        
        customer_id = create_response.json()["id"]
        
        try:
            # Test AI message generation
            ai_request = {
                "customer_id": customer_id,
                "context": "Follow-up after recent appointment"
            }
            
            ai_response = client.post("/messages/send", headers=auth_headers, json=ai_request)
            
            if ai_response.status_code == 500 and "OpenAI" in ai_response.text:
                pytest.skip("OpenAI not properly configured for integration testing")
            
            # The response might fail due to Twilio not being configured, but we can check
            # if it got past the AI generation phase
            response_data = ai_response.json()
            
            # If it fails due to Twilio, that's expected in testing
            if "Twilio" in str(response_data):
                pytest.skip("Twilio not configured (expected for AI-only testing)")
            
            # If it succeeded, verify the AI generated content
            if ai_response.status_code == 200:
                assert "content" in response_data["data"]
                assert len(response_data["data"]["content"]) > 0
                
        finally:
            # Cleanup
            client.delete(f"/customers/{customer_id}", headers=auth_headers)

class TestAPIDocumentation:
    """Test that API documentation is working."""
    
    def test_openapi_json_available(self):
        """Test that OpenAPI JSON schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        openapi_data = response.json()
        assert "openapi" in openapi_data
        assert "paths" in openapi_data
    
    def test_docs_ui_available(self):
        """Test that Swagger UI documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_ui_available(self):
        """Test that ReDoc UI documentation is available."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

class TestEndpointCoverage:
    """Verify all documented endpoints exist."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": VALID_API_KEY}
    
    def test_all_customer_endpoints_exist(self, auth_headers):
        """Test that all customer endpoints from README exist."""
        endpoints = [
            ("GET", "/customers", [200]),  # Should return list
            ("POST", "/customers", [200, 400, 422]),  # Should accept POST, may fail validation
            ("GET", "/customers/test_id", [200, 404]),  # Should accept GET, may not exist
            ("PUT", "/customers/test_id", [200, 404, 400, 422]),  # Should accept PUT, may not exist
            ("DELETE", "/customers/test_id", [200, 404]),  # Should accept DELETE, may not exist
            ("GET", "/customers/search/phone?phone=+1234567890", [200, 404])  # Should accept search
        ]
        
        for method, path, allowed_codes in endpoints:
            if method == "GET":
                response = client.get(path, headers=auth_headers)
            elif method == "POST":
                response = client.post(path, headers=auth_headers, json={})
            elif method == "PUT":
                response = client.put(path, headers=auth_headers, json={})
            elif method == "DELETE":
                response = client.delete(path, headers=auth_headers)
            
            # Should not get 405 (method not allowed) - this indicates endpoint doesn't exist
            assert response.status_code != 405, f"Endpoint {method} {path} method not allowed"
            # Should get an expected status code
            assert response.status_code in allowed_codes, f"Endpoint {method} {path} returned unexpected status {response.status_code}"
    
    def test_all_message_endpoints_exist(self, auth_headers):
        """Test that all message endpoints from README exist."""
        endpoints = [
            ("GET", "/messages", [200]),  # Should return list
            ("GET", "/messages?customer_id=test123", [200]),  # Should return filtered list
            ("GET", "/messages/test_id", [200, 404]),  # Should accept GET, may not exist
            ("POST", "/messages/send", [200, 400, 422]),  # Should accept POST, may fail validation
            ("POST", "/messages/manual", [200, 400, 422]),  # Should accept POST, may fail validation
            ("POST", "/messages/incoming", [200, 400, 401, 422])  # This one still requires auth
        ]
        
        for method, path, allowed_codes in endpoints:
            headers = auth_headers  # All endpoints require auth now
            
            if method == "GET":
                response = client.get(path, headers=headers)
            elif method == "POST":
                response = client.post(path, headers=headers, json={})
            
            # Should not get 405 (method not allowed) - this indicates endpoint doesn't exist
            assert response.status_code != 405, f"Endpoint {method} {path} method not allowed"
            # Should get an expected status code
            assert response.status_code in allowed_codes, f"Endpoint {method} {path} returned unexpected status {response.status_code}"

# Pytest markers for conditional testing
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test requiring real services")
    config.addinivalue_line("markers", "openai: mark test as requiring OpenAI API")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not integration"])
