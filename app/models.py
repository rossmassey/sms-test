"""
Pydantic models for Customer and Message data structures.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class CustomerBase(BaseModel):
    """Base customer model with common fields."""
    name: str = Field(..., min_length=1, description="Customer's full name")
    phone: str = Field(..., min_length=1, description="Customer's phone number")
    notes: Optional[str] = Field(None, description="Additional notes about the customer")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorizing customers")
    last_visit: Optional[str] = Field(None, description="Last visit date/time")

class CustomerCreate(CustomerBase):
    """Model for creating a new customer."""
    pass

class CustomerUpdate(BaseModel):
    """Model for updating an existing customer."""
    name: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    last_visit: Optional[str] = None

class Customer(CustomerBase):
    """Complete customer model with ID."""
    id: str = Field(..., description="Unique customer identifier")
    
    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    """Base message model with common fields."""
    customer_id: str = Field(..., description="Reference to customer ID")
    direction: Literal["inbound", "outbound"] = Field(..., description="Message direction")
    content: str = Field(..., description="Message content")
    source: Literal["ai", "manual"] = Field(..., description="Message source")
    escalation: bool = Field(default=False, description="Whether message requires escalation")

class MessageCreate(BaseModel):
    """Model for creating a new message."""
    customer_id: str
    content: str
    direction: Literal["inbound", "outbound"] = "outbound"
    source: Literal["ai", "manual"] = "ai"
    escalation: bool = False

class MessageSend(BaseModel):
    """Model for sending a new AI-generated message."""
    customer_id: str = Field(..., description="Customer to send message to")
    context: Optional[str] = Field(None, description="Additional context for AI message generation")
    prompt_template: Optional[str] = Field(None, description="Custom prompt template for message generation")

class Message(MessageBase):
    """Complete message model with ID and timestamp."""
    id: str = Field(..., description="Unique message identifier")
    timestamp: datetime = Field(..., description="Message timestamp")
    
    class Config:
        from_attributes = True

class IncomingWebhook(BaseModel):
    """Model for Twilio incoming SMS webhook."""
    From: str = Field(..., description="Sender's phone number")
    To: str = Field(..., description="Recipient's phone number (your Twilio number)")
    Body: str = Field(..., description="Message body")
    MessageSid: str = Field(..., description="Twilio message SID")
    
    class Config:
        # Allow additional fields from Twilio webhook
        extra = "allow"

class APIResponse(BaseModel):
    """Standard API response model."""
    success: bool
    message: str
    data: Optional[dict] = None
