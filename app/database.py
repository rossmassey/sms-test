"""
Firebase Firestore database initialization and client setup.
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global Firestore client
db = None

def initialize_firebase():
    """
    Initialize Firebase Admin SDK and Firestore client.
    This should be called once during application startup.
    """
    global db
    
    if firebase_admin._apps:
        # Firebase already initialized
        db = firestore.client()
        return db
    
    # Get Firebase configuration from environment
    cred_path = os.getenv("FIREBASE_CRED_PATH")
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    
    if not cred_path or not project_id:
        raise ValueError("Firebase credentials not properly configured in environment variables")
    
    # Initialize Firebase with service account credentials
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
    else:
        raise FileNotFoundError(f"Firebase service account file not found: {cred_path}")
    
    firebase_admin.initialize_app(cred, {
        'projectId': project_id
    })
    
    # Initialize Firestore client
    db = firestore.client()
    return db

def get_firestore_client():
    """
    Get the Firestore client instance.
    Returns the global db client, initializing if necessary.
    """
    global db
    if db is None:
        db = initialize_firebase()
    return db

# Collection references
def get_customers_collection():
    """Get reference to customers collection."""
    return get_firestore_client().collection('customers')

def get_messages_collection():
    """Get reference to messages collection."""
    return get_firestore_client().collection('messages')
