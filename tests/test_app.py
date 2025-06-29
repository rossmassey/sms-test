"""
Test-specific FastAPI app configuration that doesn't initialize real Firebase.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Create persistent mocks for the database module
mock_firestore_client = Mock()
mock_customers_collection = Mock()
mock_messages_collection = Mock()

# Set up default mock behavior for empty responses
mock_customers_collection.limit.return_value.offset.return_value.stream.return_value = []
mock_messages_collection.order_by.return_value.limit.return_value.offset.return_value.stream.return_value = []

# Set up default mock behavior for document operations
default_doc_ref = Mock()
default_doc_ref.id = "default_test_id"
default_doc_ref.get.return_value.exists = False

mock_customers_collection.add.return_value = (None, default_doc_ref)
mock_customers_collection.document.return_value = default_doc_ref

mock_messages_collection.add.return_value = (None, default_doc_ref)
mock_messages_collection.document.return_value = default_doc_ref

# Patches for Firebase modules (but don't start them automatically)
firebase_admin_patch = patch.dict('sys.modules', {
    'firebase_admin': Mock(),
    'firebase_admin.credentials': Mock(),
    'firebase_admin.firestore': Mock()
})

database_patches = [
    patch('app.database.initialize_firebase'),
    patch('app.database.get_firestore_client', return_value=mock_firestore_client),
    patch('app.database.get_customers_collection', return_value=mock_customers_collection),
    patch('app.database.get_messages_collection', return_value=mock_messages_collection),
]

def start_patches():
    """Start all database patches for mocked tests."""
    firebase_admin_patch.start()
    for p in database_patches:
        p.start()

def stop_patches():
    """Stop all database patches."""
    try:
        firebase_admin_patch.stop()
    except RuntimeError:
        pass  # Patch wasn't started
    for p in database_patches:
        try:
            p.stop()
        except RuntimeError:
            pass  # Patch wasn't started

# Only start patches if we're explicitly in a mocked test context
_patches_started = False

def ensure_patches_started():
    """Ensure patches are started for mocked tests."""
    global _patches_started
    if not _patches_started:
        start_patches()
        _patches_started = True

# Import app modules after checking if we need patches
# This will be called when creating the test app
def get_mocked_app_modules():
    """Get app modules with mocking applied."""
    ensure_patches_started()
    from app.routes import customers, messages
    from app.main import verify_api_key
    return customers, messages, verify_api_key

# Cleanup function for patches
def cleanup_patches():
    """Stop all database patches safely."""
    global _patches_started
    if _patches_started:
        stop_patches()
        _patches_started = False

@asynccontextmanager
async def app_lifespan(app):
    """Test lifespan that doesn't initialize Firebase."""
    # Don't initialize Firebase for tests
    yield

# Create test FastAPI app with mocked modules
customers, messages, verify_api_key = get_mocked_app_modules()

test_app = FastAPI(
    title="SMS Outreach Backend (Test)",
    description="AI-powered SMS outreach backend with Firebase and Twilio integration (Test Mode)",
    version="1.0.0",
    lifespan=app_lifespan
)

# Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware
test_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@test_app.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SMS Outreach Backend",
        "mode": "test"
    }

# Include routers with authentication
test_app.include_router(
    customers.router, 
    prefix="/customers", 
    tags=["customers"],
    dependencies=[Depends(verify_api_key)]
)

test_app.include_router(
    messages.router, 
    prefix="/messages", 
    tags=["messages"],
    dependencies=[Depends(verify_api_key)]
)
