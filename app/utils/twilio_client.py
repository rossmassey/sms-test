"""
Twilio client utilities for sending SMS and webhook validation.
"""

import base64
import hashlib
import hmac
import os

from dotenv import load_dotenv
from twilio.base.exceptions import TwilioException
from twilio.rest import Client

# Load environment variables
load_dotenv()

# Initialize Twilio client
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")

if not all([account_sid, auth_token, twilio_phone]):
    raise ValueError("Twilio credentials not properly configured in environment variables")

twilio_client = Client(account_sid, auth_token)


async def send_sms(to_phone: str, message_body: str) -> str:
    """
    Send an SMS message via Twilio.
    
    Args:
        to_phone: Recipient's phone number (in E.164 format)
        message_body: Content of the SMS message
    
    Returns:
        str: Twilio message SID
    
    Raises:
        Exception: If SMS sending fails
    """
    try:
        # Ensure phone number is in proper format
        if not to_phone.startswith('+'):
            # Add US country code if not present
            to_phone = f"+1{to_phone.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')}"

        message = twilio_client.messages.create(
            body=message_body,
            from_=twilio_phone,
            to=to_phone
        )

        return message.sid

    except TwilioException as e:
        raise Exception(f"Twilio error: {str(e)}")
    except Exception as e:
        raise Exception(f"SMS sending failed: {str(e)}")


def verify_webhook_signature(request_body: bytes, signature: str, url: str) -> bool:
    """
    Verify that the incoming webhook request is from Twilio.
    
    Args:
        request_body: Raw request body bytes
        signature: X-Twilio-Signature header value
        url: Full URL of the webhook endpoint
    
    Returns:
        bool: True if signature is valid, False otherwise
    """
    try:
        # Get auth token
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        if not auth_token:
            return False

        # Create expected signature
        expected_signature = base64.b64encode(
            hmac.new(
                auth_token.encode('utf-8'),
                url.encode('utf-8') + request_body,
                hashlib.sha1
            ).digest()
        ).decode('utf-8')

        # Compare signatures
        return hmac.compare_digest(expected_signature, signature)

    except Exception:
        return False


async def get_message_status(message_sid: str) -> dict:
    """
    Get the delivery status of a sent message.
    
    Args:
        message_sid: Twilio message SID
    
    Returns:
        dict: Message status information
    """
    try:
        message = twilio_client.messages(message_sid).fetch()

        return {
            'sid': message.sid,
            'status': message.status,
            'error_code': message.error_code,
            'error_message': message.error_message,
            'date_sent': message.date_sent,
            'date_updated': message.date_updated
        }

    except TwilioException as e:
        raise Exception(f"Error fetching message status: {str(e)}")


async def get_account_balance() -> float:
    """
    Get current Twilio account balance.
    
    Returns:
        float: Account balance in USD
    """
    try:
        balance = twilio_client.balance.fetch()
        return float(balance.balance)

    except TwilioException as e:
        raise Exception(f"Error fetching account balance: {str(e)}")


def format_phone_number(phone: str) -> str:
    """
    Format a phone number to E.164 format for Twilio.
    
    Args:
        phone: Phone number in various formats
    
    Returns:
        str: Phone number in E.164 format
    """
    # If already in E.164 format, return as-is
    if phone.startswith('+'):
        return phone

    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))

    # Add country code if not present (assumes US)
    if len(digits) == 10:
        digits = f"1{digits}"
    elif len(digits) == 11 and digits.startswith('1'):
        # Already has country code
        pass

    return f"+{digits}"
