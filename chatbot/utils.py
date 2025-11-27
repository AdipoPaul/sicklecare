import os
import requests
from django.utils import timezone
from .models import ChatHistory
from twilio.rest import Client


def get_ai_response(user, user_input):
    """
    Optimized DeepSeek response generator with context and response limiting.
    Designed for fast replies (~5-8s typical).
    """
    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return "⚠️ AI service unavailable. Please try again later."

        # Limit context to 3–5 latest messages for speed
        past_messages = ChatHistory.objects.filter(user=user).order_by("-timestamp")[:5][::-1]

        history = [
            {
                "role": "system",
                "content": "You are SickleCare, a caring WhatsApp assistant for sickle cell awareness. "
                           "Keep replies short, friendly, and under 1500 characters."
                           "Limit emojis strictly to **no more than 1 per message** and only if appropriate. "                    
            }
        ]

        for chat in past_messages:
            role = "user" if chat.sender == "user" else "assistant"
            history.append({"role": role, "content": chat.message})

        # Add latest user message
        history.append({"role": "user", "content": user_input.strip()})

        # Prepare API call
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip" 
        }
        payload = {
            "model": "deepseek-chat",
            "messages": history,
            "max_tokens": 300,          # keeps response concise
            "temperature": 0.6,         # reduces rambling
        }

        # Log time for benchmarking (optional)
        import time; start = time.time()

        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Extract AI response
        ai_reply = data["choices"][0]["message"]["content"].strip()

        # Limit for WhatsApp
        if len(ai_reply) > 1500:
            ai_reply = ai_reply[:1500].rsplit(' ', 1)[0] + "\n\n… Message shortened for WhatsApp."

        # Save to chat history
        ChatHistory.objects.bulk_create([
            ChatHistory(user=user, message=user_input, sender="user", timestamp=timezone.now()),
            ChatHistory(user=user, message=ai_reply, sender="bot", timestamp=timezone.now())
        ])

        print(f"DeepSeek response time: {time.time() - start:.2f}s")

        return ai_reply

    except requests.Timeout:
        return "⚠️ The AI service took too long to respond. Please try again."
    except Exception as e:
        print(f"AI Error: {e}")
        return "⚠️ AI service unavailable. Please try again later."
    
def handle_crisis(user, message):
    raw_contacts = user.emergency_contacts
    
    if isinstance(raw_contacts, list):
        contacts = [c for c in raw_contacts if c]
    elif isinstance(raw_contacts, str):
        contacts = [c.strip() for c in raw_contacts.split(",") if c.strip()]
    else:
        contacts = []

    alert_text = (
        f"🚨 *SickleCare Emergency Alert!*\n\n"
        f"User: {user.name or user.phone_number}\n"
        f"Phone: {user.phone_number}\n"
        f"Message: {message}\n\n"
        f"The user may be in crisis. Please contact them immediately."
    )

    for number in contacts:
        send_whatsapp_message(number, alert_text)

    # 2. Optionally send local medical facility suggestions
    if user.location:
        hospitals = get_nearby_hospitals(user.location)

        if hospitals:
            # Combine all hospitals into ONE text block
            hospital_lines = []
            for h in hospitals:
                hospital_lines.append(
                    f"🏥 *{h['name']}*\n📍 {h['address']}\n📞 {h.get('phone', 'N/A')}"
                )
            
            hospitals_text = "\n\n".join(hospital_lines)

            final_msg = (
                "🚨 Crisis Detected!\n"
                "I've notified your emergency contacts.\n\n"
                "Here are nearby hospitals:\n\n"
                f"{hospitals_text}\n\n"
                "Follow the steps above and stay safe. ❤️"
            )

            # Send ONE message only
            send_whatsapp_message(user.phone_number, final_msg)

        else:
            send_whatsapp_message(
                user.phone_number,
                "⚠️ No nearby hospitals were found for your location."
            )
            

def get_nearby_hospitals(user_location):
    google_api_key = os.getenv("GOOGLE_MAPS_KEY")

    url = (
        "https://maps.googleapis.com/maps/api/place/textsearch/json"
        f"?query=hospitals near {user_location}"
        f"&key={google_api_key}"
    )

    response = requests.get(url)
    data = response.json()

    hospitals = []
    
    for result in data.get("results", [])[:3]:  # Return top 3
        hospital = {
            "name": result["name"],
            "address": result.get("formatted_address", "N/A"),
            "location": result["geometry"]["location"],
            "phone": None
        }
        
        place_id = result.get("place_id")
        if place_id:
            details_url = (
                "https://maps.googleapis.com/maps/api/place/details/json"
                f"?place_id={place_id}"
                "&fields=formatted_phone_number"
                f"&key={google_api_key}"
            )
            details_response = requests.get(details_url)
            details_data = details_response.json()
            phone = details_data.get("result", {}).get("formatted_phone_number")
            if phone:
                hospital["phone"] = phone

        hospitals.append(hospital)       
    # print("GOOGLE API RESULT:", response.json())
    return hospitals
    
def send_emergency_alert(user, message):
    """
    Sends an alert to all emergency contacts for a user.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_whatsapp = "whatsapp:+14155238886"

    client = Client(account_sid, auth_token)

    if not user.emergency_contacts:
        return False
    
    raw_numbers = [num.strip() for num in user.emergency_contacts.split(",")]
    
    contacts = list({
        num.lstrip("+").replace(" ", "") 
        for num in raw_numbers 
        if num.strip().replace("+", "").isdigit()
    })
    
    if not contacts:
        print("No valid emergency contacts")
        return False

    # contacts = [num.strip() for num in user.emergency_contacts.split(",") if num.strip()]
    alert_msg = (
        f"🚨 *SickleCare Emergency Alert!*\n\n"
        f"User: {user.name or 'Unknown'}\n"
        f"Phone: {user.phone_number}\n"
        f"Message: {message}\n\n"
        f"Please reach out or check on them immediately."
    )

    for contact in contacts:
        try:
            client.messages.create(
                from_=from_whatsapp,
                to=f"whatsapp:+{contact}" if not contact.startswith("whatsapp:") else contact,
                body=alert_msg
            )
        except Exception as e:
            print(f"Error sending alert to {contact}: {e}")

    return True

def send_whatsapp_message(to, message):
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")

    if not account_sid or not auth_token:
        print("⚠️ Twilio credentials not set in environment variables.")
        return

    client = Client(account_sid, auth_token)
    
     # Twilio WhatsApp max per message
    MAX_LEN = 1600  

    # Split the message into chunks
    parts = [message[i:i+MAX_LEN] for i in range(0, len(message), MAX_LEN)]

    try:
        for part in parts:
            client.messages.create(
                body=part,
                from_=whatsapp_number,
            to=f"whatsapp:{to}"
        )
        print(f"WhatsApp message sent to {to}")
    except Exception as e:
        print(f"Failed to send message to {to}: {e}")
        

def send_whatsapp_media(to, media_url, caption=None):
    """
    Sends media (PDF, image, etc.)
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")

    client = Client(account_sid, auth_token)

    try:
        client.messages.create(
            body=caption or "",
            media_url=[media_url],
            from_=whatsapp_number,
            to=f"whatsapp:{to}"
        )
        print(f"Media sent to {to}: {media_url}")
    except Exception as e:
        print(f"Failed to send media to {to}: {e}")

