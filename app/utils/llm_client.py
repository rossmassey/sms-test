"""
OpenAI LLM client utilities for message composition and auto-replies.
"""

import os
from typing import List, Tuple, Optional, Dict, Any

from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key not configured in environment variables")

openai_client = AsyncOpenAI(api_key=api_key)

# Default prompt templates
DEFAULT_OUTBOUND_TEMPLATE = """
You are a friendly and professional customer service representative for a business. 
Generate a personalized SMS message for the following customer.

Customer Information:
- Name: {customer_name}
- Phone: {customer_phone}
- Notes: {customer_notes}
- Tags: {customer_tags}
- Last Visit: {customer_last_visit}

Additional Context: {context}

Guidelines:
- Keep the message under 160 characters if possible
- Be friendly but professional
- Personalize based on customer information
- Include a clear call-to-action if appropriate
- Use casual SMS language but maintain professionalism

Generate only the SMS message content, no additional text or explanations.
"""

DEFAULT_AUTO_REPLY_TEMPLATE = """
You are an AI assistant helping with customer service via SMS. 
Analyze the incoming message and determine if you can provide a helpful auto-reply.

Incoming Message: "{incoming_message}"

Customer Information:
- Name: {customer_name}
- Phone: {customer_phone}
- Notes: {customer_notes}
- Tags: {customer_tags}

Recent Message History:
{message_history}

Your task:
1. Determine if this message requires human escalation
2. If no escalation needed, generate an appropriate auto-reply

Escalate to human if:
- Customer is angry or frustrated
- Complex technical issues
- Billing/payment disputes
- Requests for refunds or cancellations
- Unclear or ambiguous requests
- Mentions of complaints or legal issues

If you can handle it automatically, provide a helpful response.

Response format:
AUTO_REPLY: [your reply message or NONE if escalation needed]
ESCALATE: [true/false]
REASON: [brief explanation]
"""

# Message type templates for different types of initial messages
MESSAGE_TYPE_TEMPLATES = {
    "welcome": """
Generate a warm welcome message for new customer {customer_name}.
This is their first interaction with our business.
Context: {context}
Keep it friendly, welcoming, and under 160 characters.
""",
    "follow-up": """
Generate a follow-up message for customer {customer_name}.
This is to check in after their recent interaction or visit.
Context: {context}
Keep it caring, professional, and under 160 characters.
""",
    "reminder": """
Generate a reminder message for customer {customer_name}.
This is to remind them about something important.
Context: {context}
Keep it helpful, clear, and under 160 characters.
""",
    "promotional": """
Generate a promotional message for customer {customer_name}.
This is to inform them about a special offer or promotion.
Context: {context}
Keep it exciting, valuable, and under 160 characters.
""",
    "support": """
Generate a support message for customer {customer_name}.
This is to help them with a question or issue.
Context: {context}
Keep it helpful, clear, and under 160 characters.
""",
    "thank-you": """
Generate a thank you message for customer {customer_name}.
This is to express gratitude for their business or action.
Context: {context}
Keep it warm, genuine, and under 160 characters.
""",
    "appointment": """
Generate an appointment-related message for customer {customer_name}.
This could be confirmation, reminder, or scheduling.
Context: {context}
Keep it clear, professional, and under 160 characters.
"""
}


async def generate_outbound_message(
        customer_data: dict,
        context: Optional[str] = None,
        prompt_template: Optional[str] = None
) -> str:
    """
    Generate an AI-powered outbound SMS message for a customer.
    
    Args:
        customer_data: Dictionary containing customer information
        context: Additional context for message generation
        prompt_template: Custom prompt template (optional)
    
    Returns:
        str: Generated SMS message content
    
    Raises:
        Exception: If message generation fails
    """
    try:
        # Use provided template or default
        template = prompt_template or DEFAULT_OUTBOUND_TEMPLATE

        # Format the prompt with customer data
        prompt = template.format(
            customer_name=customer_data.get('name', 'Valued Customer'),
            customer_phone=customer_data.get('phone', 'N/A'),
            customer_notes=customer_data.get('notes', 'No additional notes'),
            customer_tags=', '.join(customer_data.get('tags', [])) or 'None',
            customer_last_visit=customer_data.get('last_visit', 'Unknown'),
            context=context or 'General outreach message'
        )

        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are a helpful customer service AI that generates personalized SMS messages."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )

        message_content = response.choices[0].message.content.strip()

        # Ensure message isn't too long (SMS limit is 160 chars, but allow some buffer)
        if len(message_content) > 160:
            # Try to regenerate with stricter length requirement
            prompt += "\n\nIMPORTANT: The message MUST be under 160 characters."

            response = await openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system",
                     "content": "You are a helpful customer service AI. Generate concise SMS messages under 160 characters."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )

            message_content = response.choices[0].message.content.strip()

        return message_content

    except Exception as e:
        raise Exception(f"Error generating outbound message: {str(e)}")


async def generate_initial_message(
        customer_name: str,
        message_type: str,
        context: Optional[str] = None
) -> str:
    """
    Generate an initial AI message based on customer name and message type.
    
    Args:
        customer_name: Name of the customer
        message_type: Type of message (welcome, follow-up, reminder, etc.)
        context: Additional context for message generation
    
    Returns:
        str: Generated SMS message content
    
    Raises:
        Exception: If message generation fails
    """
    try:
        # Get template for message type, use generic if not found
        template = MESSAGE_TYPE_TEMPLATES.get(message_type, MESSAGE_TYPE_TEMPLATES["welcome"])
        
        # Format the prompt
        prompt = template.format(
            customer_name=customer_name,
            context=context or f"General {message_type} message"
        )

        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": f"You are a helpful customer service AI that generates {message_type} SMS messages."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )

        message_content = response.choices[0].message.content.strip()
        
        # Ensure message isn't too long
        if len(message_content) > 160:
            prompt += "\n\nIMPORTANT: The message MUST be under 160 characters."

            response = await openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system",
                     "content": f"You are a helpful customer service AI. Generate concise {message_type} SMS messages under 160 characters."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )

            message_content = response.choices[0].message.content.strip()

        return message_content

    except Exception as e:
        raise Exception(f"Error generating initial message: {str(e)}")


async def generate_auto_reply(
        incoming_message: str,
        customer_data: dict,
        message_history: List[dict]
) -> Tuple[Optional[str], bool]:
    """
    Generate an auto-reply to an incoming SMS and determine if escalation is needed.
    
    Args:
        incoming_message: The incoming SMS content
        customer_data: Dictionary containing customer information
        message_history: List of recent message history
    
    Returns:
        Tuple[Optional[str], bool]: (auto_reply_message, should_escalate)
    
    Raises:
        Exception: If auto-reply generation fails
    """
    try:
        # Format message history for context
        history_text = ""
        for msg in message_history[-5:]:  # Last 5 messages for context
            direction = "Customer" if msg.get('direction') == 'inbound' else "Us"
            history_text += f"{direction}: {msg.get('content', '')}\n"

        if not history_text:
            history_text = "No recent message history"

        # Format the prompt
        prompt = DEFAULT_AUTO_REPLY_TEMPLATE.format(
            incoming_message=incoming_message,
            customer_name=customer_data.get('name', 'Customer'),
            customer_phone=customer_data.get('phone', 'N/A'),
            customer_notes=customer_data.get('notes', 'No additional notes'),
            customer_tags=', '.join(customer_data.get('tags', [])) or 'None',
            message_history=history_text
        )

        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are a customer service AI that processes incoming SMS messages and decides whether to auto-reply or escalate to humans."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.3  # Lower temperature for more consistent responses
        )

        response_text = response.choices[0].message.content.strip()

        # Parse the response
        auto_reply = None
        should_escalate = False
        
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('AUTO_REPLY:'):
                reply_text = line.split('AUTO_REPLY:', 1)[1].strip()
                if reply_text.upper() != 'NONE':
                    auto_reply = reply_text
            elif line.startswith('ESCALATE:'):
                escalate_text = line.split('ESCALATE:', 1)[1].strip().lower()
                should_escalate = escalate_text in ['true', 'yes', '1']

        return auto_reply, should_escalate

    except Exception as e:
        # On error, escalate to human for safety
        print(f"Error generating auto-reply: {str(e)}")
        return None, True


async def generate_ongoing_response(
        incoming_message: str,
        customer_data: dict,
        message_history: List[dict],
        context: Optional[str] = None
) -> str:
    """
    Generate a response to an ongoing conversation.
    
    Args:
        incoming_message: The latest message from the customer
        customer_data: Dictionary containing customer information
        message_history: List of conversation history
        context: Additional context for response generation
    
    Returns:
        str: Generated response message
    
    Raises:
        Exception: If response generation fails
    """
    try:
        # Format message history for context
        history_text = ""
        for msg in message_history[-10:]:  # Last 10 messages for context
            role = "Customer" if msg.get('direction') == 'inbound' else "Assistant"
            history_text += f"{role}: {msg.get('content', '')}\n"

        if not history_text:
            history_text = "No previous conversation history"

        prompt = f"""
You are a helpful customer service AI assistant. Generate a response to the customer's message.

Customer Information:
- Name: {customer_data.get('name', 'Customer')}
- Phone: {customer_data.get('phone', 'N/A')}
- Notes: {customer_data.get('notes', 'No additional notes')}

Conversation History:
{history_text}

Latest Customer Message: "{incoming_message}"

Additional Context: {context or 'Ongoing conversation'}

Guidelines:
- Be helpful and professional
- Keep response under 160 characters
- Address the customer's specific question or concern
- Use their name when appropriate
- Provide actionable information when possible

Generate only the response message, no additional text.
"""

        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are a helpful customer service AI that generates appropriate responses to customer messages."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )

        message_content = response.choices[0].message.content.strip()
        
        # Ensure message isn't too long
        if len(message_content) > 160:
            prompt += "\n\nIMPORTANT: The response MUST be under 160 characters."

            response = await openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system",
                     "content": "You are a helpful customer service AI. Generate concise responses under 160 characters."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )

            message_content = response.choices[0].message.content.strip()

        return message_content

    except Exception as e:
        raise Exception(f"Error generating ongoing response: {str(e)}")


async def generate_demo_response(
        incoming_message: str,
        customer_name: str,
        message_history: List[Dict[str, Any]],
        context: Optional[str] = None
) -> str:
    """
    Generate a demo response using provided message history.
    
    Args:
        incoming_message: The latest message from the customer
        customer_name: Name of the customer
        message_history: List of conversation history with role and content
        context: Additional context for response generation
    
    Returns:
        str: Generated response message
    
    Raises:
        Exception: If response generation fails
    """
    try:
        # Format message history for context
        history_text = ""
        for msg in message_history[-10:]:  # Last 10 messages for context
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            history_text += f"{role.capitalize()}: {content}\n"

        if not history_text:
            history_text = "No previous conversation history"

        prompt = f"""
You are a helpful customer service AI assistant. Generate a response to the customer's message.

Customer Name: {customer_name}

Conversation History:
{history_text}

Latest Customer Message: "{incoming_message}"

Additional Context: {context or 'Demo conversation'}

Guidelines:
- Be helpful and professional
- Keep response under 160 characters
- Address the customer's specific question or concern
- Use their name when appropriate
- Provide actionable information when possible

Generate only the response message, no additional text.
"""

        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are a helpful customer service AI that generates appropriate responses to customer messages."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )

        message_content = response.choices[0].message.content.strip()
        
        # Ensure message isn't too long
        if len(message_content) > 160:
            prompt += "\n\nIMPORTANT: The response MUST be under 160 characters."

            response = await openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system",
                     "content": "You are a helpful customer service AI. Generate concise responses under 160 characters."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )

            message_content = response.choices[0].message.content.strip()

        return message_content

    except Exception as e:
        raise Exception(f"Error generating demo response: {str(e)}")


async def analyze_message_sentiment(message: str) -> dict:
    """
    Analyze the sentiment and urgency of a message.
    
    Args:
        message: The message to analyze
    
    Returns:
        dict: Analysis results with sentiment, urgency, and escalation recommendation
    
    Raises:
        Exception: If analysis fails
    """
    try:
        prompt = f"""
Analyze the sentiment and urgency of this customer message:

Message: "{message}"

Provide analysis in this format:
SENTIMENT: [positive/neutral/negative]
URGENCY: [low/medium/high]
KEYWORDS: [key words or phrases that indicate emotion/intent]
CUSTOMER_INTENT: [question/complaint/compliment/request/inquiry]
ESCALATE: [true/false] (should this be escalated to a human?)
REASON: [brief explanation of the analysis]
"""

        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are an AI that analyzes customer messages for sentiment, urgency, and escalation needs."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.3
        )

        response_text = response.choices[0].message.content.strip()
        
        # Parse the response
        analysis = {
            'sentiment': 'neutral',
            'urgency': 'low',
            'keywords': [],
            'customer_intent': 'inquiry',
            'escalate': False,
            'reason': ''
        }
        
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('SENTIMENT:'):
                analysis['sentiment'] = line.split('SENTIMENT:', 1)[1].strip().lower()
            elif line.startswith('URGENCY:'):
                analysis['urgency'] = line.split('URGENCY:', 1)[1].strip().lower()
            elif line.startswith('KEYWORDS:'):
                keywords_text = line.split('KEYWORDS:', 1)[1].strip()
                analysis['keywords'] = [k.strip() for k in keywords_text.split(',')]
            elif line.startswith('CUSTOMER_INTENT:'):
                analysis['customer_intent'] = line.split('CUSTOMER_INTENT:', 1)[1].strip().lower()
            elif line.startswith('ESCALATE:'):
                escalate_text = line.split('ESCALATE:', 1)[1].strip().lower()
                analysis['escalate'] = escalate_text in ['true', 'yes', '1']
            elif line.startswith('REASON:'):
                analysis['reason'] = line.split('REASON:', 1)[1].strip()

        return analysis

    except Exception as e:
        raise Exception(f"Error analyzing message sentiment: {str(e)}")
