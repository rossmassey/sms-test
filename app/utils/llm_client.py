"""
OpenAI LLM client utilities for message composition and auto-replies.
"""

import os
from typing import List, Dict, Tuple, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

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
                {"role": "system", "content": "You are a helpful customer service AI that generates personalized SMS messages."},
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
                    {"role": "system", "content": "You are a helpful customer service AI. Generate concise SMS messages under 160 characters."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            message_content = response.choices[0].message.content.strip()
        
        return message_content
    
    except Exception as e:
        raise Exception(f"Error generating outbound message: {str(e)}")

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
                {"role": "system", "content": "You are a customer service AI that processes incoming SMS messages and decides whether to auto-reply or escalate to humans."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.3  # Lower temperature for more consistent responses
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse the response
        auto_reply = None
        should_escalate = True  # Default to escalation for safety
        
        lines = response_text.split('\n')
        for line in lines:
            if line.startswith('AUTO_REPLY:'):
                reply_content = line.replace('AUTO_REPLY:', '').strip()
                if reply_content and reply_content.upper() != 'NONE':
                    auto_reply = reply_content
            elif line.startswith('ESCALATE:'):
                escalate_value = line.replace('ESCALATE:', '').strip().lower()
                should_escalate = escalate_value in ['true', 'yes', '1']
        
        return auto_reply, should_escalate
    
    except Exception as e:
        # On error, escalate to human for safety
        print(f"Error generating auto-reply: {str(e)}")
        return None, True

async def analyze_message_sentiment(message: str) -> dict:
    """
    Analyze the sentiment and urgency of a message.
    
    Args:
        message: The message content to analyze
    
    Returns:
        dict: Analysis results including sentiment, urgency, and keywords
    """
    try:
        prompt = f"""
        Analyze the following SMS message for sentiment, urgency, and key topics:
        
        Message: "{message}"
        
        Provide analysis in this format:
        SENTIMENT: [positive/neutral/negative]
        URGENCY: [low/medium/high]
        KEYWORDS: [comma-separated key topics]
        CUSTOMER_INTENT: [brief description of what customer wants]
        """
        
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a message analysis AI that categorizes customer communications."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.1
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse response
        analysis = {
            'sentiment': 'neutral',
            'urgency': 'medium',
            'keywords': [],
            'customer_intent': 'Unknown'
        }
        
        lines = response_text.split('\n')
        for line in lines:
            if line.startswith('SENTIMENT:'):
                analysis['sentiment'] = line.replace('SENTIMENT:', '').strip().lower()
            elif line.startswith('URGENCY:'):
                analysis['urgency'] = line.replace('URGENCY:', '').strip().lower()
            elif line.startswith('KEYWORDS:'):
                keywords = line.replace('KEYWORDS:', '').strip()
                analysis['keywords'] = [k.strip() for k in keywords.split(',') if k.strip()]
            elif line.startswith('CUSTOMER_INTENT:'):
                analysis['customer_intent'] = line.replace('CUSTOMER_INTENT:', '').strip()
        
        return analysis
    
    except Exception as e:
        return {
            'sentiment': 'neutral',
            'urgency': 'medium',
            'keywords': [],
            'customer_intent': f'Analysis failed: {str(e)}'
        }
