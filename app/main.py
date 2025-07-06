"""
FastAPI application main module.
Sets up the FastAPI app, middleware, and router registration.
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

from .database import initialize_firebase
from .routes import customers, messages

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    # Initialize Firebase
    initialize_firebase()
    yield


# Create FastAPI app
app = FastAPI(
    title="SMS Outreach Backend",
    description="AI-powered SMS outreach backend with Firebase and Twilio integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security dependency for API key authentication
async def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key for protected endpoints."""
    expected_api_key = os.getenv("API_KEY")
    if not expected_api_key:
        raise HTTPException(status_code=500, detail="API key not configured")

    if x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return x_api_key


# Health check endpoint
@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SMS Outreach Backend",
        "version": "1.0.0"
    }


# Include routers
app.include_router(
    customers.router,
    prefix="/customers",
    tags=["customers"],
    dependencies=[Depends(verify_api_key)]
)

app.include_router(
    messages.router,
    prefix="/messages",
    tags=["messages"],
    dependencies=[Depends(verify_api_key)]
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
