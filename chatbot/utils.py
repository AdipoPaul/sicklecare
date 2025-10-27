import os
import requests
from .models import ChatHistory
from twilio.rest import Client

def get_ai_response(user, user_input):
    """
    Uses DeepSeek with chat history context.
    """
    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return "⚠️ AI service unavailable. Please try again later."

        # Retrieve last 5 messages for context
        past_messages = ChatHistory.objects.filter(user=user).order_by("-timestamp")[:5][::-1]

        history = [
            {"role": "system", "content": "You are SickleCare, a friendly WhatsApp assistant for sickle cell awareness."}
        ]

        for chat in past_messages:
            role = "user" if chat.sender == "user" else "assistant"
            history.append({"role": role, "content": chat.message})

        # Add current message
        history.append({"role": "user", "content": user_input})

        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": "deepseek-chat", "messages": history}

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        ai_reply = data["choices"][0]["message"]["content"].strip()

        # Save both user message and bot reply to history
        ChatHistory.objects.create(user=user, message=user_input, sender="user")
        ChatHistory.objects.create(user=user, message=ai_reply, sender="bot")

        return ai_reply

    except Exception as e:
        print(f"AI Error: {e}")
        return "⚠️ AI service unavailable. Please try again later."

def send_whatsapp_message(to, message):
    """
    Sends a WhatsApp message via Twilio API.
    `to` should be a phone number in full international format (e.g., +2547XXXXXXXX).
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

    if not account_sid or not auth_token:
        print("⚠️ Twilio credentials not set in environment variables.")
        return

    client = Client(account_sid, auth_token)

    try:
        client.messages.create(
            body=message,
            from_=whatsapp_number,
            to=f"whatsapp:{to}"
        )
        print(f"✅ WhatsApp message sent to {to}")
    except Exception as e:
        print(f"❌ Failed to send message to {to}: {e}")
