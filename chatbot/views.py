from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.messaging_response import MessagingResponse
from .utils import get_ai_response
from .models import UserProfile

def get_or_create_user(phone_number, name=None):
    user, created = UserProfile.objects.get_or_create(phone_number=phone_number)
    if name and created:
        user.name = name
        user.save()
    return user

def generate_personalized_response(user, text):
    if "pain" in text.lower():
        return f"I'm sorry to hear that, {user.name or 'friend'}. Please ensure you hydrate and rest. If pain persists, seek medical attention."
    elif "reminder" in text.lower():
        return f"Sure {user.name or 'there'}, I can set a reminder for you. What would you like to be reminded about?"
    else:
        return f"Hi {user.name or 'there'}, how can I assist you today?"

# --- AI SERVICE HELPER ---
# def get_ai_response(user_input):
#     """
#     Uses DeepSeek (preferred) or OpenAI as fallback.
#     """
#     try:
#         api_key = os.getenv("DEEPSEEK_API_KEY")
#         if not api_key:
#             return "⚠️ AI service unavailable. Please try again later."

#         url = "https://api.deepseek.com/v1/chat/completions"
#         headers = {
#             "Authorization": f"Bearer {api_key}",
#             "Content-Type": "application/json"
#         }
#         payload = {
#             "model": "deepseek-chat",
#             "messages": [
#                 {"role": "system", "content": "You are SickleCare, a friendly WhatsApp assistant for sickle cell awareness."},
#                 {"role": "user", "content": user_input}
#             ]
#         }
#         response = requests.post(url, headers=headers, json=payload)
#         response.raise_for_status()
#         data = response.json()
#         return data["choices"][0]["message"]["content"].strip()
#     except Exception as e:
#         print(f"AI Error: {e}")
#         return "⚠️ AI service unavailable. Please try again later."

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
                    f"✅ Registration complete, {user.name}!\n\n"
                    "Type *menu* anytime to access:\n"
                    "1️⃣ Sickle Cell Info\n"
                    "2️⃣ Find Resources\n"
                    "3️⃣ Crisis Support\n"
                    "4️⃣ Daily Health Check\n\n"
                    "How can I assist you today?"
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
            elif incoming_msg.lower() == "reset":
                user.chats.all().delete()
                msg.body("🧠 Chat memory cleared! Let’s start fresh.")            
            else:
                # AI fallback for informational questions
                ai_reply = get_ai_response(user, incoming_msg)
                msg.body(ai_reply)
                
                # msg.body("⌛ Processing your request. Please wait...")                
                # threading.Thread(target=send_to_deepseek_async, args=(sender, incoming_msg)).start()
                
                return HttpResponse(str(response), content_type="application/xml")

        return HttpResponse(str(response), content_type="application/xml")

    return HttpResponse("OK")
