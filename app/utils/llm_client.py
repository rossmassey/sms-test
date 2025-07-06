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

# System message templates for consistency
SYSTEM_MESSAGE_BASE = "You are an AI assistant for NextGen MedSpa, a medical spa in Hatfield, MA."
SYSTEM_MESSAGE_GENERATE = f"{SYSTEM_MESSAGE_BASE} Generate warm, professional SMS messages for customers. Keep responses concise and friendly."
SYSTEM_MESSAGE_GENERATE_TYPED = f"{SYSTEM_MESSAGE_BASE} Generate friendly, professional {{message_type}} SMS messages for customers."
SYSTEM_MESSAGE_CONVERSATION = f"{SYSTEM_MESSAGE_BASE} Generate warm, professional responses to customer messages using conversation context."
SYSTEM_MESSAGE_AUTO_REPLY = f"{SYSTEM_MESSAGE_BASE} Process incoming SMS messages and decide whether to auto-reply or escalate to humans. Keep responses warm and professional."
SYSTEM_MESSAGE_ESCALATION = f"{SYSTEM_MESSAGE_BASE} Generate empathetic escalation messages for customers who need human assistance."
SYSTEM_MESSAGE_ANALYSIS = f"{SYSTEM_MESSAGE_BASE} Analyze customer messages for sentiment, urgency, and escalation needs."

# Length constraint for concise messages
LENGTH_CONSTRAINT = " Keep messages under 160 characters."

# Default business data - can be configured by staff
DEFAULT_BUSINESS_DATA = """
Business Information:
- Name: [Business Name - Please configure]
- Hours: Monday-Friday 9:00 AM - 5:00 PM, Weekend hours vary
- Phone: [Business Phone - Please configure]
- Email: [Business Email - Please configure]  
- Address: [Business Address - Please configure]
- Website: [Business Website - Please configure]
- Services: General customer service and support
- Emergency Contact: [After hours contact - Please configure]

Note: Staff should configure this business information for accurate customer service.
"""


def get_business_data() -> str:
    """
    Get business data for AI context. 
    This can be overridden to load from database/config file.
    
    Returns:
        str: Business information for AI context
    """
    # Check for environment variable override
    custom_business_data = os.getenv("BUSINESS_DATA")
    if custom_business_data:
        return custom_business_data

    # Check for business_config.txt file
    try:
        with open("business_config.txt", "r") as f:
            return f.read()
    except FileNotFoundError:
        pass

    # Return default template
    return DEFAULT_BUSINESS_DATA


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
You are an AI assistant for NextGen MedSpa, a medical spa offering advanced laser, skin, and body treatments in Hatfield, MA. You communicate via SMS text messages professionally and naturally.

Your role is to:
1. Answer questions about services, pricing, and availability
2. Help with appointment scheduling requests (but explain they'll need to call to confirm)
3. Provide information about treatments and policies
4. Handle promotional inquiries and appointment reminders
5. Communicate like a helpful, professional staff member - not a marketing bot

COMMUNICATION STYLE:
- Sound natural and conversational, like a real person
- Be helpful and professional, not overly promotional
- Avoid excessive emojis, exclamation points, or marketing language
- Don't sound like spam or automated marketing messages
- Keep responses concise but warm and personable

{business_data}

Incoming Message: "{incoming_message}"

Customer Information:
- Name: {customer_name}
- Phone: {customer_phone}
- Notes: {customer_notes}
- Tags: {customer_tags}

Recent Message History:
{message_history}

CRITICAL CONVERSATION RULES:
1. REVIEW YOUR PREVIOUS RESPONSES: Look at the message history above. If you've already given similar responses, VARY your wording significantly.
2. ANSWER QUESTIONS DIRECTLY: If the customer asks about a specific service (like "do you have a pool?"), give a clear direct answer first, then additional info.
3. AVOID REPETITION: Never send the exact same or nearly identical response multiple times. Each response should feel fresh and natural.
4. BE CONVERSATIONAL: Respond like a human staff member who remembers what they just said and adjusts accordingly.

IMPORTANT: Use the conversation history to provide personalized responses. If the customer mentioned specific services or had previous treatments, reference that context naturally.

CRITICAL: ESCALATE IMMEDIATELY if customer message contains ANY of these:

VIOLENCE/THREATS:
- ANY threats of violence ("kill", "hurt", "destroy", "burn", "shoot")
- ANY threatening language toward staff or property
- ANY mention of physical harm or retaliation

LEGAL ISSUES:
- ANY mention of suing, lawyers, attorneys, lawsuits
- ANY mention of legal action, malpractice, reporting
- ANY mention of state boards, licensing complaints

MEDICAL EMERGENCIES:
- ANY mention of severe pain, bleeding, allergic reactions
- ANY concerning physical symptoms or side effects
- ANY mention of complications, infections, or adverse reactions
- ANYTHING that could be a medical emergency

EXTREME ANGER/COMPLAINTS:
- Words like "unacceptable", "furious", "terrible", "worst"
- ANY demands for refunds or money back
- ANY insulting language toward staff or business
- ANY negative reviews or threats to damage reputation
- ANY complaints or worries about the staff or business

ALSO ESCALATE FOR:
- Complex appointment scheduling (direct them to call)
- Billing, payment, or refund questions
- Any confusion or unclear requests
- Anything requiring professional judgment

WHEN IN DOUBT: ESCALATE. Better safe than sorry for a medical spa business.

AUTO-REPLY for questions you can answer with business info:
- Basic hours questions ("what time do you close?")
- Location/address questions  
- Contact information questions
- Simple greeting messages
- Simple "thank you" messages
- Services ONLY if explicitly listed in business data above (DO NOT assume or invent services)
- Treatment descriptions and durations for listed services only
- Policies and cancellation info

CRITICAL SERVICE RULE: Only mention services explicitly listed in the business data above. If asked about services not on the list (spa, sauna, pool, massage, etc.), respond: "I don't see that service on our current menu. Please call (413) 555-0123 for the most up-to-date information."

CRITICAL: DO NOT CONTACT requests - if customer says ANY of these words/phrases, set DO_NOT_CONTACT=true:
- Contains "do not contact", "don't contact", "stop messaging", "stop texting", "don't text"
- Contains "remove me", "unsubscribe", "take me off", "opt out"
- Contains "leave me alone", "stop bothering", "don't want to hear"
- Contains "if you contact me again", "will sue", "legal action"
- Contains "stop calling", "stop contacting", "no more messages"
- Contains "I'm not interested", "not interested anymore"
- Any variation of requesting NO further contact

EXAMPLE RESPONSES for DO_NOT_CONTACT messages:
"DO NOT CONTACT ME" → DO_NOT_CONTACT: true
"don't contact me anymore" → DO_NOT_CONTACT: true
"stop messaging me" → DO_NOT_CONTACT: true
"remove me from your list" → DO_NOT_CONTACT: true
"unsubscribe" → DO_NOT_CONTACT: true
"leave me alone" → DO_NOT_CONTACT: true

When in doubt, ESCALATE. Only auto-reply if you have clear, factual information from the business data above.

Response format:
AUTO_REPLY: [your reply message or NONE if escalation needed]
ESCALATE: [true/false]
DO_NOT_CONTACT: [true/false] (true if customer wants no further contact)
REASON: [brief explanation]
"""

# Message type templates for different types of initial messages
MESSAGE_TYPE_TEMPLATES = {
    "welcome": """
Generate a warm, professional welcome message for new customer {customer_name} from NextGen MedSpa.
This is their first interaction with our medical spa in Hatfield, MA.
Context: {context}

Make the message friendly and professional, not overly promotional. Sound like a real person from the spa.
Avoid excessive emojis, exclamation points, or sales language.
Keep it under 160 characters and conversational.
Examples: "Hi Sarah, welcome to NextGen MedSpa! We're here to help with all your skincare needs. Any questions? Feel free to text back or call us at (413) 555-0123."
""",
    "follow-up": """
Generate a caring follow-up message for customer {customer_name} from NextGen MedSpa.
This is to check in after their recent interaction, visit, or treatment.
Context: {context}

Make the message caring, professional, and personalized. Reference their previous interaction if possible.
Ask how they're feeling or if they have questions. Keep it under 160 characters.
Examples: "Hi John! How are you feeling after your laser treatment? Any questions? We're here to help! 💙"
""",
    "reminder": """
Generate a helpful reminder message for customer {customer_name} from NextGen MedSpa.
This is to remind them about something important (appointment, follow-up care, etc.).
Context: {context}

Make the message helpful, clear, and friendly. Include relevant details and contact info.
Keep it under 160 characters but informative.
Examples: "Hi Lisa! Reminder: Your HydraFacial is tomorrow at 2pm. Please arrive 15 mins early! Questions? Call (413) 555-0123 📅"
""",
    "promotional": """
Generate a professional promotional message for customer {customer_name} from NextGen MedSpa.
This is to inform them about a special offer, discount, or new service.
Context: {context}

Make the message professional and informative, not pushy or overly salesy. Reference previous treatments if relevant.
Sound like helpful information, not spam. Keep it under 160 characters and conversational.
Examples: "Hi Emma, we have a special offer on laser treatments this month. Would be perfect as a follow-up to your recent visit. Call (413) 555-0123 if you're interested."
""",
    "support": """
Generate a supportive message for customer {customer_name} from NextGen MedSpa.
This is to help them with a question, concern, or provide guidance.
Context: {context}

Make the message helpful, reassuring, and professional. Show you care about their experience.
Keep it under 160 characters but warm and supportive.
Examples: "Hi Mark! We're here to help with any questions about your treatment. Our team is always available at (413) 555-0123! 💙"
""",
    "thank-you": """
Generate a heartfelt thank you message for customer {customer_name} from NextGen MedSpa.
This is to express gratitude for their business, referral, or positive feedback.
Context: {context}

Make the message warm, genuine, and appreciative. Reference their specific action if possible.
Keep it under 160 characters but heartfelt.
Examples: "Hi Rachel! Thank you for choosing NextGen MedSpa! Your trust means the world to us. Can't wait to see you again! 🌟"
""",
    "appointment": """
Generate an appointment-related message for customer {customer_name} from NextGen MedSpa.
This could be confirmation, reminder, rescheduling, or scheduling assistance.
Context: {context}

Make the message clear, professional, and helpful. Include relevant appointment details and contact info.
Keep it under 160 characters but informative.
Examples: "Hi David! Your Morpheus8 appointment is confirmed for Friday 3pm. Remember to arrive 15 mins early! Questions? (413) 555-0123 📅"
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
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": SYSTEM_MESSAGE_GENERATE},
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
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                     "content": SYSTEM_MESSAGE_GENERATE + LENGTH_CONSTRAINT},
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
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": SYSTEM_MESSAGE_GENERATE_TYPED.format(message_type=message_type)},
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
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                     "content": SYSTEM_MESSAGE_GENERATE_TYPED.format(message_type=message_type) + LENGTH_CONSTRAINT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )

            message_content = response.choices[0].message.content.strip()

        return message_content

    except Exception as e:
        raise Exception(f"Error generating initial message: {str(e)}")


def _check_do_not_contact_patterns(message: str) -> bool:
    """
    Check if message contains do-not-contact patterns using deterministic string matching.
    
    Args:
        message: The incoming message to check
    
    Returns:
        bool: True if message contains do-not-contact patterns
    """
    message_lower = message.lower().strip()
    
    # Exact phrase patterns
    do_not_contact_patterns = [
        "do not contact",
        "don't contact",
        "stop messaging",
        "stop texting",
        "don't text",
        "stop calling",
        "stop contacting",
        "remove me",
        "unsubscribe",
        "take me off",
        "opt out",
        "leave me alone",
        "stop bothering",
        "don't want to hear",
        "no more messages",
        "not interested",
        "if you contact me again i will sue",
        "if you contact me again, i will sue"
    ]
    
    # Check for exact patterns
    for pattern in do_not_contact_patterns:
        if pattern in message_lower:
            return True
    
    # Check for common variations
    if any(phrase in message_lower for phrase in [
        "stop", "don't", "remove", "unsubscribe", "opt out"
    ]) and any(phrase in message_lower for phrase in [
        "contact", "message", "text", "call", "bother"
    ]):
        return True
    
    return False


def _check_critical_escalation_patterns(message: str) -> bool:
    """
    Check for critical threats that must ALWAYS escalate using deterministic pattern matching.
    
    Args:
        message: The incoming message to check
    
    Returns:
        bool: True if message contains critical escalation patterns
    """
    message_lower = message.lower().strip()
    
    # Violence/threat patterns
    violence_patterns = [
        "kill", "hurt", "harm", "destroy", "burn", "shoot", "attack", "beat",
        "murder", "violence", "weapon", "gun", "knife", "bomb", "explode", "pay",
        "know where you live", "find you", "get you", "come for you"
    ]
    
    # Legal threat patterns  
    legal_patterns = [
        "sue", "lawyer", "attorney", "lawsuit", "legal action", "malpractice",
        "court", "judge", "litigation", "state board", "licensing", "report you",
        "legal", "action"
    ]
    
    # Medical emergency patterns
    medical_emergency_patterns = [
        "severe pain", "bleeding", "allergic reaction", "can't breathe", 
        "emergency", "hospital", "infection", "swollen", "rash", "burning",
        "doesn't look right", "looks wrong", "something wrong", "something is wrong", "not right"
    ]
    
    # Extreme anger patterns
    extreme_anger_patterns = [
        "unacceptable", "furious", "terrible", "worst", "horrible", "disgusting",
        "incompetent", "idiots", "stupid", "hate you", "money back", "never coming back",
        "never again", "done with you", "awful", "pathetic"
    ]
    
    # Check violence patterns
    for pattern in violence_patterns:
        if pattern in message_lower:
            return True
    
    # Check legal patterns
    for pattern in legal_patterns:
        if pattern in message_lower:
            return True
            
    # Check medical emergency patterns
    for pattern in medical_emergency_patterns:
        if pattern in message_lower:
            return True
            
    # Check extreme anger patterns
    for pattern in extreme_anger_patterns:
        if pattern in message_lower:
            return True
    
    # Specific threat combinations
    if any(threat in message_lower for threat in ["going to", "will", "gonna"]) and \
       any(action in message_lower for action in ["kill", "hurt", "destroy", "sue", "report"]):
        return True
    
    return False


async def generate_auto_reply(
        incoming_message: str,
        customer_data: dict,
        message_history: List[dict]
) -> Tuple[Optional[str], bool, bool]:
    """
    Generate an auto-reply to an incoming SMS and determine if escalation is needed.
    
    Args:
        incoming_message: The incoming SMS content
        customer_data: Dictionary containing customer information
        message_history: List of recent message history
    
    Returns:
        Tuple[Optional[str], bool, bool]: (auto_reply_message, should_escalate, is_do_not_contact)
    
    Raises:
        Exception: If auto-reply generation fails
    """
    try:
        # First check for do-not-contact patterns deterministically
        if _check_do_not_contact_patterns(incoming_message):
            return None, True, True
        
        # Check for critical escalation patterns that must always escalate
        if _check_critical_escalation_patterns(incoming_message):
            print(f"[DEBUG] Critical escalation pattern detected: {incoming_message}")
            # Generate an escalation acknowledgment message
            escalation_message = await generate_escalation_message(
                incoming_message, customer_data.get('name', 'Customer')
            )
            return escalation_message, True, False  # Send acknowledgment, escalate, not do_not_contact
        
        # Format message history for context
        history_text = ""
        for msg in message_history[-5:]:  # Last 5 messages for context
            direction = "Customer" if msg.get('direction') == 'inbound' else "Us"
            history_text += f"{direction}: {msg.get('content', '')}\n"

        if not history_text:
            history_text = "No recent message history"

        # Format the prompt
        prompt = DEFAULT_AUTO_REPLY_TEMPLATE.format(
            business_data=get_business_data(),
            incoming_message=incoming_message,
            customer_name=customer_data.get('name', 'Customer'),
            customer_phone=customer_data.get('phone', 'N/A'),
            customer_notes=customer_data.get('notes', 'No additional notes'),
            customer_tags=', '.join(customer_data.get('tags', [])) or 'None',
            message_history=history_text
        )

        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": SYSTEM_MESSAGE_AUTO_REPLY},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7  # Higher temperature for more varied, natural responses
        )

        response_text = response.choices[0].message.content.strip()

        # Parse the response
        auto_reply = None
        should_escalate = False
        is_do_not_contact = False

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
            elif line.startswith('DO_NOT_CONTACT:'):
                do_not_contact_text = line.split('DO_NOT_CONTACT:', 1)[1].strip().lower()
                is_do_not_contact = do_not_contact_text in ['true', 'yes', '1']

        return auto_reply, should_escalate, is_do_not_contact

    except Exception as e:
        # On error, escalate to human for safety
        print(f"Error generating auto-reply: {str(e)}")
        return None, True, False


async def generate_escalation_message(
        incoming_message: str,
        customer_name: str
) -> str:
    """
    Generate a contextual escalation acknowledgment message.
    
    Args:
        incoming_message: The message that triggered escalation
        customer_name: Customer's name
    
    Returns:
        str: Contextual escalation acknowledgment message
    """
    try:
        prompt = f"""
Generate a brief, empathetic escalation acknowledgment message for a customer.

Customer Name: {customer_name}
Their Message: "{incoming_message}"

The message should:
- Acknowledge their concern empathetically
- Indicate that a staff member will help them
- Be professional but warm
- Be under 160 characters
- Use their name

Examples:
- "Hi Sarah, I understand your concern about the side effects. A staff member will contact you shortly to help resolve this."
- "Hi John, I'm sorry to hear about this issue. One of our team members will reach out to you right away."

Generate only the message, no extra text.
"""

        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": SYSTEM_MESSAGE_ESCALATION},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        # Fallback message if generation fails
        return f"Hi {customer_name}, I understand your concern. A staff member will contact you shortly to help resolve this."


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
{SYSTEM_MESSAGE_BASE} Generate a warm, professional response to the customer's message.

{get_business_data()}

Customer Information:
- Name: {customer_data.get('name', 'Customer')}
- Phone: {customer_data.get('phone', 'N/A')}
- Notes: {customer_data.get('notes', 'No additional notes')}

Conversation History:
{history_text}

Latest Customer Message: "{incoming_message}"

Additional Context: {context or 'Ongoing conversation'}

Guidelines:
- Be warm, friendly, and professional (NextGen MedSpa style)
- Keep response under 160 characters
- Use conversation history to provide personalized responses
- Reference previous treatments or services mentioned naturally
- Use their name when appropriate
- Provide actionable information about our services
- For appointments, direct them to call (413) 555-0123

Generate only the response message, no additional text.
"""

        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": SYSTEM_MESSAGE_CONVERSATION},
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
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                     "content": SYSTEM_MESSAGE_CONVERSATION + LENGTH_CONSTRAINT},
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
{SYSTEM_MESSAGE_BASE} Generate a warm, professional response to the customer's message.

{get_business_data()}

Customer Name: {customer_name}

Conversation History:
{history_text}

Latest Customer Message: "{incoming_message}"

Additional Context: {context or 'Demo conversation'}

Guidelines:
- Be warm, friendly, and professional (NextGen MedSpa style)
- Keep response under 160 characters
- Use conversation history to provide personalized responses
- Reference previous treatments or services mentioned naturally
- Use their name when appropriate
- Provide actionable information about our services
- For appointments, direct them to call (413) 555-0123

Generate only the response message, no additional text.
"""

        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": SYSTEM_MESSAGE_CONVERSATION},
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
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                     "content": SYSTEM_MESSAGE_CONVERSATION + LENGTH_CONSTRAINT},
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
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": SYSTEM_MESSAGE_ANALYSIS},
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
