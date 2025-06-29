"""
Message management and SMS webhook API routes.
Handles sending SMS messages and processing incoming webhooks.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from google.cloud.firestore_v1.base_query import FieldFilter
from datetime import datetime

from ..models import Message, MessageCreate, MessageSend, IncomingWebhook, APIResponse
from ..database import get_messages_collection, get_customers_collection
from ..utils.twilio_client import send_sms, verify_webhook_signature
from ..utils.llm_client import generate_outbound_message, generate_auto_reply

router = APIRouter()

@router.get("/", response_model=List[Message])
async def list_messages(
    customer_id: Optional[str] = Query(None, description="Filter messages by customer ID"),
    limit: int = Query(100, description="Maximum number of messages to return"),
    offset: int = Query(0, description="Number of messages to skip")
):
    """
    Retrieve messages with optional customer filtering and pagination.
    """
    try:
        messages_ref = get_messages_collection()
        
        # Apply customer filter if provided
        if customer_id:
            # When filtering by customer_id, we can't also order by timestamp without a composite index
            # So we'll get all matching messages and sort them in Python
            query = messages_ref.where(filter=FieldFilter("customer_id", "==", customer_id))
            docs = query.stream()
            
            # Collect all messages and sort by timestamp in Python
            all_messages = []
            for doc in docs:
                try:
                    message_data = doc.to_dict()
                    message_data['id'] = doc.id
                    
                    # Skip invalid messages to maintain data integrity
                    if not message_data.get('customer_id') or not message_data.get('content'):
                        continue
                    
                    # Convert Firestore timestamp to datetime if needed
                    if 'timestamp' in message_data and hasattr(message_data['timestamp'], 'to_pydatetime'):
                        message_data['timestamp'] = message_data['timestamp'].to_pydatetime()
                    all_messages.append(Message(**message_data))
                except Exception as validation_error:
                    # Log the error but continue processing other messages
                    print(f"Skipping invalid message {doc.id}: {validation_error}")
                    continue
                    
            # Sort by timestamp (most recent first) and apply pagination
            all_messages.sort(key=lambda x: x.timestamp, reverse=True)
            messages = all_messages[offset:offset + limit]
        else:
            # When not filtering, we can order by timestamp directly
            query = messages_ref.order_by("timestamp", direction="DESCENDING").limit(limit).offset(offset)
            docs = query.stream()
            
            messages = []
            for doc in docs:
                try:
                    message_data = doc.to_dict()
                    message_data['id'] = doc.id
                    
                    # Skip invalid messages to maintain data integrity
                    if not message_data.get('customer_id') or not message_data.get('content'):
                        continue
                    
                    # Convert Firestore timestamp to datetime if needed
                    if 'timestamp' in message_data and hasattr(message_data['timestamp'], 'to_pydatetime'):
                        message_data['timestamp'] = message_data['timestamp'].to_pydatetime()
                    messages.append(Message(**message_data))
                except Exception as validation_error:
                    # Log the error but continue processing other messages
                    print(f"Skipping invalid message {doc.id}: {validation_error}")
                    continue
        
        return messages
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")

@router.post("/send", response_model=APIResponse)
async def send_message(message_request: MessageSend):
    """
    Generate an AI message and send it via SMS, then save to Firestore.
    """
    try:
        # Verify customer exists
        customers_ref = get_customers_collection()
        customer_doc = customers_ref.document(message_request.customer_id).get()
        
        if not customer_doc.exists:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer_data = customer_doc.to_dict()
        
        # Generate message using AI
        ai_message = await generate_outbound_message(
            customer_data=customer_data,
            context=message_request.context,
            prompt_template=message_request.prompt_template
        )
        
        # Try to send SMS via Twilio (handle if not configured)
        message_sid = None
        try:
            message_sid = await send_sms(
                to_phone=customer_data['phone'],
                message_body=ai_message
            )
        except Exception as twilio_error:
            # If Twilio is not configured or fails, we'll still save the message
            # but mark it as not sent
            print(f"Twilio error: {twilio_error}")
            message_sid = "NOT_SENT_TWILIO_ERROR"
        
        # Save message to Firestore
        messages_ref = get_messages_collection()
        message_data = {
            'customer_id': message_request.customer_id,
            'direction': 'outbound',
            'content': ai_message,
            'source': 'ai',
            'escalation': False,
            'timestamp': datetime.utcnow(),
            'twilio_sid': message_sid
        }
        
        doc_ref = messages_ref.add(message_data)[1]
        
        return APIResponse(
            success=True,
            message="Message generated successfully" + (" and sent via SMS" if message_sid and message_sid != "NOT_SENT_TWILIO_ERROR" else " (SMS not sent - Twilio not configured)"),
            data={
                'message_id': doc_ref.id,
                'twilio_sid': message_sid,
                'content': ai_message
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")

@router.post("/manual", response_model=Message)
async def create_manual_message(message: MessageCreate):
    """
    Create a manual message record (for messages sent outside the system).
    """
    try:
        # Verify customer exists
        customers_ref = get_customers_collection()
        customer_doc = customers_ref.document(message.customer_id).get()
        
        if not customer_doc.exists:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Save message to Firestore
        messages_ref = get_messages_collection()
        message_data = message.model_dump()
        message_data['timestamp'] = datetime.utcnow()
        
        doc_ref = messages_ref.add(message_data)[1]
        
        # Return created message
        message_data['id'] = doc_ref.id
        return Message(**message_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating message: {str(e)}")

@router.post("/incoming", response_model=APIResponse)
async def handle_incoming_sms(request: Request):
    """
    Twilio webhook endpoint for handling incoming SMS messages.
    Validates signature, saves message, and optionally sends AI auto-reply.
    """
    try:
        # Get request body and headers for signature verification
        body = await request.body()
        signature = request.headers.get('X-Twilio-Signature', '')
        
        # Verify webhook signature
        if not verify_webhook_signature(body, signature, str(request.url)):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse form data
        form_data = await request.form()
        webhook_data = IncomingWebhook(**dict(form_data))
        
        # Find customer by phone number
        customers_ref = get_customers_collection()
        customer_query = customers_ref.where(filter=FieldFilter("phone", "==", webhook_data.From))
        customer_docs = list(customer_query.stream())
        
        if not customer_docs:
            # Create new customer for unknown number
            customer_data = {
                'name': f"Unknown ({webhook_data.From})",
                'phone': webhook_data.From,
                'notes': "Auto-created from incoming SMS",
                'tags': ['unknown', 'incoming-sms']
            }
            customer_ref = customers_ref.add(customer_data)[1]
            customer_id = customer_ref.id
        else:
            customer_id = customer_docs[0].id
            customer_data = customer_docs[0].to_dict()
        
        # Save incoming message
        messages_ref = get_messages_collection()
        message_data = {
            'customer_id': customer_id,
            'direction': 'inbound',
            'content': webhook_data.Body,
            'source': 'manual',  # Incoming messages are from humans
            'escalation': False,
            'timestamp': datetime.utcnow(),
            'twilio_sid': webhook_data.MessageSid
        }
        
        message_ref = messages_ref.add(message_data)[1]
        
        # Generate AI auto-reply
        try:
            auto_reply, should_escalate = await generate_auto_reply(
                incoming_message=webhook_data.Body,
                customer_data=customer_data,
                message_history=[]  # TODO: Fetch recent message history
            )
            
            if auto_reply and not should_escalate:
                # Send auto-reply
                reply_sid = await send_sms(
                    to_phone=webhook_data.From,
                    message_body=auto_reply
                )
                
                # Save auto-reply message
                reply_data = {
                    'customer_id': customer_id,
                    'direction': 'outbound',
                    'content': auto_reply,
                    'source': 'ai',
                    'escalation': False,
                    'timestamp': datetime.utcnow(),
                    'twilio_sid': reply_sid
                }
                messages_ref.add(reply_data)
            
            elif should_escalate:
                # Mark for escalation
                message_ref.update({'escalation': True})
        
        except Exception as e:
            # Log auto-reply error but don't fail the webhook
            print(f"Auto-reply generation failed: {str(e)}")
        
        return APIResponse(
            success=True,
            message="Incoming message processed successfully",
            data={'message_id': message_ref.id}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing incoming message: {str(e)}")

@router.get("/{message_id}", response_model=Message)
async def get_message(message_id: str):
    """
    Retrieve a specific message by ID.
    """
    try:
        messages_ref = get_messages_collection()
        doc = messages_ref.document(message_id).get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Message not found")
        
        message_data = doc.to_dict()
        message_data['id'] = doc.id
        
        # Convert Firestore timestamp to datetime if needed
        if 'timestamp' in message_data and hasattr(message_data['timestamp'], 'to_pydatetime'):
            message_data['timestamp'] = message_data['timestamp'].to_pydatetime()
        
        return Message(**message_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving message: {str(e)}")
