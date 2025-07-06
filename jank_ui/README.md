# 🚀 SMS Outreach System - Jank Demo UI

This is a basic React UI to demonstrate the SMS outreach system functionality.

## 🎯 What This Demo Shows

- **Customer Management**: Add and list customers
- **AI Conversations**: Start AI-powered conversations with customers
- **Mock SMS**: Simulate customer responses (since Twilio isn't set up)
- **Manual Intervention**: Staff can manually respond at any time
- **Real-time Updates**: Messages refresh automatically

## 🔧 Setup

1. **Start the Backend** (from main project root):
   ```bash
   cd ..
   python run_dev.py
   ```
   Backend should be running on http://localhost:8000

2. **Start the Frontend** (in this directory):
   ```bash
   npm start
   ```
   Frontend will open on http://localhost:3000

## 🎮 How to Use

### 1. Add a Customer

- Click "➕ Add Customer"
- Fill in name, phone, notes, tags
- Click "Add Customer"

### 2. Start a Conversation

- Go back to "📋 Customers"
- Click "View Conversation" for any customer
- Click "🚀 Start AI Conversation"
- Choose message type (follow-up, welcome, etc.)
- Add context if needed
- AI will generate and "send" the initial message

### 3. Mock Customer Responses

- In the conversation view, use "📱 Mock Customer Response"
- Type what the customer would text back
- AI will automatically generate and "send" a response
- Continue the conversation as long as you want

### 4. Manual Intervention

- Use "👩‍💼 Manual Staff Response" to override AI
- Type your own message to send as staff
- This simulates when escalation happens

## 🔍 What to Look For

- **AI Message Generation**: See how AI creates personalized messages
- **Conversation Flow**: Watch how AI maintains context
- **Status Indicators**:
    - 🟢 AI Active
    - 🔴 Escalated
    - ⚫ No Messages
- **Message Sources**: See "ai" vs "manual" sources
- **Auto-refresh**: Messages update every 3 seconds

## ⚠️ Limitations

- **No Real SMS**: Uses demo endpoints since Twilio not configured
- **No CSS**: Intentionally ugly for rapid development
- **Basic Error Handling**: Alerts for errors
- **Hardcoded API Key**: For demo purposes only

## 🎯 For Your Business Partner

This shows exactly how the system works:

1. **Staff starts conversations** with one click
2. **AI handles customer replies** automatically
3. **Staff can intervene** when needed
4. **Everything is tracked** in the database

The real system will work the same way, but with actual SMS instead of mock responses!
