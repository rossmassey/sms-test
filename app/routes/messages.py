"""
Message management and SMS webhook API routes.
Handles sending SMS messages and processing incoming webhooks.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from google.cloud.firestore_v1.base_query import FieldFilter

from ..database import get_messages_collection, get_customers_collection
from ..models import (
    Message, MessageCreate, MessageSend, IncomingWebhook, APIResponse,
    InitialSMSRequest, InitialDemoRequest, OngoingSMSRequest, 
    OngoingDemoRequest, MessageResponse
)
from ..utils.llm_client import (
    generate_outbound_message, generate_auto_reply, generate_initial_message,
    generate_ongoing_response, generate_demo_response
)
from ..utils.twilio_client import send_sms, verify_webhook_signature

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
            # When not filtering, get all messages and sort in Python to avoid index requirement
            query = messages_ref
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
            
            # Sort by timestamp in Python and apply pagination
            messages.sort(key=lambda x: x.timestamp, reverse=True)
            messages = messages[offset:offset + limit]

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
            message="Message generated successfully" + (
                " and sent via SMS" if message_sid and message_sid != "NOT_SENT_TWILIO_ERROR" else " (SMS not sent - Twilio not configured)"),
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


@router.post("/initial/sms", response_model=MessageResponse)
async def send_initial_sms(request: InitialSMSRequest):
    """
    Send initial SMS message to customer.
    Creates customer if doesn't exist, generates AI message, sends SMS.
    """
    try:
        customers_ref = get_customers_collection()
        
        # Find customer by phone number
        customer_query = customers_ref.where(filter=FieldFilter("phone", "==", request.phone))
        customer_docs = list(customer_query.stream())
        
        if customer_docs:
            # Customer exists, use existing customer
            customer_doc = customer_docs[0]
            customer_id = customer_doc.id
            customer_data = customer_doc.to_dict()
            customer_data['id'] = customer_id
        else:
            # Customer doesn't exist, create new one
            customer_data = {
                'name': request.name,
                'phone': request.phone,
                'notes': f"Auto-created for {request.message_type} message",
                'tags': ['auto-created'],
                'last_visit': None
            }
            customer_ref = customers_ref.add(customer_data)[1]
            customer_id = customer_ref.id
            customer_data['id'] = customer_id

        # Generate initial message using AI
        ai_message = await generate_initial_message(
            customer_name=request.name,
            message_type=request.message_type,
            context=request.context
        )

        # Send SMS via Twilio
        message_sid = None
        try:
            message_sid = await send_sms(
                to_phone=request.phone,
                message_body=ai_message
            )
        except Exception as twilio_error:
            print(f"Twilio error: {twilio_error}")
            message_sid = "NOT_SENT_TWILIO_ERROR"

        # Save message to Firestore
        messages_ref = get_messages_collection()
        message_data = {
            'customer_id': customer_id,
            'direction': 'outbound',
            'content': ai_message,
            'source': 'ai',
            'escalation': False,
            'timestamp': datetime.utcnow(),
            'twilio_sid': message_sid,
            'message_type': request.message_type
        }

        message_ref = messages_ref.add(message_data)[1]

        return MessageResponse(
            success=True,
            message="Initial SMS message sent successfully" if message_sid != "NOT_SENT_TWILIO_ERROR" else "Initial message generated (SMS not sent - Twilio not configured)",
            response_content=None,  # SMS mode doesn't return content
            message_id=message_ref.id,
            customer_id=customer_id,
            twilio_sid=message_sid
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending initial SMS message: {str(e)}")


@router.post("/initial/demo", response_model=MessageResponse)
async def send_initial_demo(request: InitialDemoRequest):
    """
    Generate initial demo message without sending SMS.
    Returns the AI-generated message content.
    """
    try:
        # Generate initial message using AI
        ai_message = await generate_initial_message(
            customer_name=request.name,
            message_type=request.message_type,
            context=request.context
        )

        return MessageResponse(
            success=True,
            message="Initial demo message generated successfully",
            response_content=ai_message,
            message_id=None,  # Demo mode doesn't save to database
            customer_id=None,
            twilio_sid=None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating initial demo message: {str(e)}")


@router.post("/ongoing/sms", response_model=MessageResponse)
async def send_ongoing_sms(request: OngoingSMSRequest):
    """
    Continue SMS conversation with customer.
    Looks up conversation history, generates AI response, sends SMS.
    """
    try:
        customers_ref = get_customers_collection()
        
        # Find customer by phone number
        customer_query = customers_ref.where(filter=FieldFilter("phone", "==", request.phone))
        customer_docs = list(customer_query.stream())
        
        if not customer_docs:
            raise HTTPException(status_code=404, detail="Customer not found with this phone number")
        
        customer_doc = customer_docs[0]
        customer_id = customer_doc.id
        customer_data = customer_doc.to_dict()
        customer_data['id'] = customer_id

        # Get conversation history
        messages_ref = get_messages_collection()
        # Query without ordering to avoid composite index requirement
        history_query = messages_ref.where(filter=FieldFilter("customer_id", "==", customer_id))
        history_docs = list(history_query.stream())
        
        # Convert to message history format and sort in Python
        message_history = []
        for doc in history_docs:
            msg_data = doc.to_dict()
            message_history.append({
                'direction': msg_data.get('direction'),
                'content': msg_data.get('content'),
                'timestamp': msg_data.get('timestamp')
            })
        
        # Sort by timestamp in Python and take last 10
        message_history.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
        message_history = message_history[:10]
        message_history.reverse()  # Reverse to get chronological order

        # Save the incoming user message first
        user_message_data = {
            'customer_id': customer_id,
            'direction': 'inbound',
            'content': request.message_content,
            'source': 'manual',
            'escalation': False,
            'timestamp': datetime.utcnow()
        }
        messages_ref.add(user_message_data)

        # Generate AI response
        ai_response = await generate_ongoing_response(
            incoming_message=request.message_content,
            customer_data=customer_data,
            message_history=message_history,
            context=request.context
        )

        # Send SMS response
        message_sid = None
        try:
            message_sid = await send_sms(
                to_phone=request.phone,
                message_body=ai_response
            )
        except Exception as twilio_error:
            print(f"Twilio error: {twilio_error}")
            message_sid = "NOT_SENT_TWILIO_ERROR"

        # Save AI response message
        response_message_data = {
            'customer_id': customer_id,
            'direction': 'outbound',
            'content': ai_response,
            'source': 'ai',
            'escalation': False,
            'timestamp': datetime.utcnow(),
            'twilio_sid': message_sid
        }

        response_message_ref = messages_ref.add(response_message_data)[1]

        return MessageResponse(
            success=True,
            message="SMS response sent successfully" if message_sid != "NOT_SENT_TWILIO_ERROR" else "Response generated (SMS not sent - Twilio not configured)",
            response_content=None,  # SMS mode doesn't return content
            message_id=response_message_ref.id,
            customer_id=customer_id,
            twilio_sid=message_sid
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending ongoing SMS response: {str(e)}")


@router.post("/ongoing/demo", response_model=MessageResponse)
async def send_ongoing_demo(request: OngoingDemoRequest):
    """
    Generate demo response to ongoing conversation.
    Uses provided chat history to generate appropriate response.
    """
    try:
        # Generate demo response using provided history
        ai_response = await generate_demo_response(
            incoming_message=request.message_content,
            customer_name=request.name,
            message_history=request.message_history,
            context=request.context
        )

        return MessageResponse(
            success=True,
            message="Demo response generated successfully",
            response_content=ai_response,
            message_id=None,  # Demo mode doesn't save to database
            customer_id=None,
            twilio_sid=None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating ongoing demo response: {str(e)}")


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
