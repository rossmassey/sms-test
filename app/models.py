"""
Pydantic models for Customer and Message data structures.
"""

from datetime import datetime
from typing import List, Optional, Literal, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class IncomingWebhook(BaseModel):
    """Model for Twilio incoming SMS webhook."""
    From: str = Field(..., description="Sender's phone number")
    To: str = Field(..., description="Recipient's phone number (your Twilio number)")
    Body: str = Field(..., description="Message body")
    MessageSid: str = Field(..., description="Twilio message SID")

    model_config = ConfigDict(extra="allow")


# New models for the four new message endpoints
class InitialSMSRequest(BaseModel):
    """Model for sending initial SMS messages."""
    name: str = Field(..., min_length=1, description="Customer name")
    phone: str = Field(..., min_length=1, description="Customer phone number")
    message_type: str = Field(..., min_length=1, description="Type of message (welcome, follow-up, reminder, etc.)")
    context: Optional[str] = Field(None, description="Additional context for message generation")


class InitialDemoRequest(BaseModel):
    """Model for initial demo messages."""
    name: str = Field(..., min_length=1, description="Customer name")
    message_type: str = Field(..., min_length=1, description="Type of message (welcome, follow-up, reminder, etc.)")
    context: Optional[str] = Field(None, description="Additional context for message generation")


class OngoingSMSRequest(BaseModel):
    """Model for ongoing SMS conversation."""
    phone: str = Field(..., min_length=1, description="Customer phone number")
    message_content: str = Field(..., min_length=1, description="User's message content")
    context: Optional[str] = Field(None, description="Additional context for response generation")


class OngoingDemoRequest(BaseModel):
    """Model for ongoing demo conversation."""
    name: str = Field(..., min_length=1, description="Customer name")
    message_history: List[Dict[str, Any]] = Field(..., description="Full conversation history")
    message_content: str = Field(..., min_length=1, description="Latest message content")
    context: Optional[str] = Field(None, description="Additional context for response generation")


class MessageResponse(BaseModel):
    """Response model for message operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Status message")
    response_content: Optional[str] = Field(None, description="Generated response content (for demo modes)")
    message_id: Optional[str] = Field(None, description="Message ID in database (for SMS modes)")
    customer_id: Optional[str] = Field(None, description="Customer ID")
    twilio_sid: Optional[str] = Field(None, description="Twilio message SID (for SMS modes)")


class APIResponse(BaseModel):
    """Standard API response model."""
    success: bool
    message: str
    data: Optional[dict] = None
