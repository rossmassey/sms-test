"""
Test configuration and fixtures for the SMS Outreach Backend test suite.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(scope="session")
def mock_environment():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        'FIREBASE_CRED_PATH': 'test-firebase-creds.json',
        'FIREBASE_PROJECT_ID': 'test-project',
        'TWILIO_ACCOUNT_SID': 'test_twilio_sid',
        'TWILIO_AUTH_TOKEN': 'test_twilio_token',
        'TWILIO_PHONE_NUMBER': '+1234567890',
        'OPENAI_API_KEY': 'test_openai_key',
        'API_KEY': 'sms_backend_2025_secure_key_xyz789'
    }):
        yield

@pytest.fixture
def mock_firebase():
    """Mock Firebase operations."""
    with patch('firebase_admin.initialize_app'), \
         patch('firebase_admin.firestore.client') as mock_client:
        mock_client.return_value = Mock()
        yield mock_client

@pytest.fixture
def mock_openai():
    """Mock OpenAI operations."""
    with patch('app.utils.llm_client.openai_client') as mock_client:
        yield mock_client

@pytest.fixture
def mock_twilio():
    """Mock Twilio operations."""
    with patch('app.utils.twilio_client.twilio_client') as mock_client:
        yield mock_client

# Test data fixtures
@pytest.fixture
def sample_customer_data():
    """Sample customer data for testing."""
    return {
        "name": "Test Customer",
        "phone": "+1234567890",
        "notes": "Sample customer for testing",
        "tags": ["test", "sample"]
    }

@pytest.fixture
def sample_message_data():
    """Sample message data for testing."""
    return {
        "customer_id": "test_customer_id",
        "content": "Test message content",
        "direction": "outbound",
        "source": "manual",
        "escalation": False
    }

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "openai: mark test as requiring OpenAI")
    config.addinivalue_line("markers", "twilio: mark test as requiring Twilio")
    config.addinivalue_line("markers", "firebase: mark test as requiring Firebase")

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add unit test marker to all tests in test_main.py
        if "test_main" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to integration tests
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add performance marker to performance tests
        if "test_performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        # Add slow marker to tests that might be slow
        if any(keyword in item.name.lower() for keyword in ["concurrent", "load", "memory", "performance"]):
            item.add_marker(pytest.mark.slow)
