"""
Test configuration for pytest.
"""

import os
import sys
import pytest
from unittest.mock import patch

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables."""
    test_vars = {
        "FIREBASE_CRED_PATH": "./firebase-service-account-sample.json",
        "FIREBASE_PROJECT_ID": "test-project",
        "TWILIO_ACCOUNT_SID": "test_sid",
        "TWILIO_AUTH_TOKEN": "test_token",
        "TWILIO_PHONE_NUMBER": "+1234567890",
        "OPENAI_API_KEY": "test_openai_key",
        "API_KEY": "sms_backend_2025_secure_key_xyz789"
    }
    
    with patch.dict(os.environ, test_vars):
        yield test_vars

@pytest.fixture
def mock_firestore():
    """Mock Firestore client for testing."""
    from unittest.mock import Mock
    
    mock_client = Mock()
    mock_collection = Mock()
    mock_document = Mock()
    
    # Mock the collection and document chain
    mock_client.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document
    mock_collection.add.return_value = (None, mock_document)
    
    with patch('app.database.firestore.client', return_value=mock_client):
        yield mock_client
