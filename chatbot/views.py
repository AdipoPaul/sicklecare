from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.messaging_response import MessagingResponse
from .models import UserProfile
import requests
import os

# --- AI SERVICE HELPER ---
def get_ai_response(user_input):
    """
    Uses DeepSeek (preferred) or OpenAI as fallback.
    """
    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return "⚠️ AI service unavailable. Please try again later."

        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are SickleCare, a friendly WhatsApp assistant for sickle cell awareness."},
                {"role": "user", "content": user_input}
            ]
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"AI Error: {e}")
        return "⚠️ AI service unavailable. Please try again later."

# --- CRISIS DETECTOR ---
def detect_crisis(message):
    """
    Simple keyword-based crisis detector.
    You can improve this with NLP later.
    """
    crisis_keywords = ["pain", "crisis", "emergency", "can't breathe", "severe", "hospital"]
    return any(word in message.lower() for word in crisis_keywords)

# --- MAIN WHATSAPP WEBHOOK ---
@csrf_exempt
def whatsapp_webhook(request):
    if request.method == "POST":
        incoming_msg = request.POST.get("Body", "").strip()
        sender = request.POST.get("From", "").replace("whatsapp:", "")
        response = MessagingResponse()
        msg = response.message()

        user, created = UserProfile.objects.get_or_create(phone_number=sender)

        # --- Registration flow ---
        if not user.registered:
            msg.body("👋 Welcome to *SickleCare*! Please reply with your *name* to register.")
            user.registered = True
            user.save()
            return HttpResponse(str(response), content_type="application/xml")

        if not user.name:
            user.name = incoming_msg
            msg.body(f"Thanks {user.name}! Are you a *Patient*, *Caregiver*, or *Donor*?")
            user.save()
            return HttpResponse(str(response), content_type="application/xml")

        if not user.role:
            if incoming_msg.lower() in ["patient", "caregiver", "donor"]:
                user.role = incoming_msg.lower()
                user.save()
                msg.body("✅ Registration complete! Type *menu* to see options.")
            else:
                msg.body("Please reply with one of: Patient, Caregiver, or Donor.")
            return HttpResponse(str(response), content_type="application/xml")

        # --- Menu and interactions ---
        if incoming_msg.lower() == "menu":
            msg.body(
                "📋 *Main Menu*\n"
                "1️⃣ Sickle Cell Info\n"
                "2️⃣ Find Resources\n"
                "3️⃣ Crisis Support\n\n"
                "Type 1, 2, or 3."
            )
        elif incoming_msg == "1":
            msg.body("🧬 You can ask me anything about Sickle Cell Disease.\nExample: What causes sickle cell disease?")
        elif incoming_msg == "2":
            msg.body("🏥 You can find nearby resources soon! (Feature under development)")
        elif incoming_msg == "3":
            msg.body(
                "🚨 *Crisis Support Guide:*\n"
                "1️⃣ Stay hydrated.\n"
                "2️⃣ Use a warm compress.\n"
                "3️⃣ Contact your doctor or go to the nearest hospital.\n\n"
                "If severe, call emergency services immediately."
            )
        else:
            # Crisis detection
            if detect_crisis(incoming_msg):
                msg.body(
                    "🚨 *Crisis Detected!*\n"
                    "If you are in pain:\n"
                    "1️⃣ Stay hydrated.\n"
                    "2️⃣ Use a warm compress.\n"
                    "3️⃣ Contact your doctor or go to the nearest hospital.\n\n"
                    "If severe or life-threatening, call emergency services immediately."
                )
            else:
                # AI fallback for informational questions
                ai_reply = get_ai_response(incoming_msg)
                msg.body(ai_reply)

        return HttpResponse(str(response), content_type="application/xml")

    return HttpResponse("OK")
