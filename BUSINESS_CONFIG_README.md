# Business Configuration for AI Customer Service

## Overview
The AI customer service system can now answer basic business questions automatically (like hours, location, contact info) instead of escalating everything to staff.

## How to Configure Your Business Information

### Method 1: Edit the business_config.txt file (Recommended)
1. Open the `business_config.txt` file in the project root
2. Update the information with your actual business details:
   - Business name and contact information
   - Operating hours (be specific!)
   - Address and location details
   - Services offered
   - Website and social media
   - Emergency contact procedures
   - Any other frequently asked information

### Method 2: Environment Variable (Advanced)
Set the `BUSINESS_DATA` environment variable with your business information.

## What Questions Will AI Handle Automatically?
Once configured, the AI can answer:
- ✅ "What time do you close?"
- ✅ "What's your address?"
- ✅ "What's your phone number?"
- ✅ "What services do you offer?"
- ✅ Basic greetings and thank you messages

## What Still Gets Escalated?
The AI will still escalate to staff for:
- ❌ Any complaints or concerns
- ❌ Health-related questions or side effects
- ❌ Appointment scheduling/booking
- ❌ Billing or payment questions
- ❌ Complex service details
- ❌ Anything requiring professional judgment

## Example Configuration
```
Business Information:
- Name: Your Spa Name
- Hours: Monday-Friday 9AM-9PM, Saturday 9AM-6PM, Sunday 10AM-5PM
- Phone: (555) 123-4567
- Email: info@yourspa.com
- Address: 123 Main St, Your City, State 12345
- Services: Botox, Facials, Massage, Skincare
- Website: www.yourspa.com
```

## Testing
After updating the configuration:
1. Restart the backend server
2. Test with questions like "what time do you close?"
3. Verify the AI responds with correct information instead of escalating

## Benefits
- Faster customer service for basic questions
- Reduces staff workload for simple inquiries
- Customers get immediate answers for common questions
- Staff can focus on complex issues that need human attention 