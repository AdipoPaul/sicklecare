from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.messaging_response import MessagingResponse
import threading
from .tasks import handle_reminder_flow
from .utils import get_ai_response, handle_crisis, send_emergency_alert, send_whatsapp_message
from .models import Resource, UserProfile

def get_or_create_user(phone_number, name=None):
    user, created = UserProfile.objects.get_or_create(phone_number=phone_number)
    if name and created:
        user.name = name
        user.save()
    return user

def detect_crisis(message):
    crisis_keywords = ["pain", "crisis", "can't breathe", "severe", "hospital"]
    return any(word in message.lower() for word in crisis_keywords)

def handle_ai_async(user, text):
    reply = get_ai_response(user, text)
    send_whatsapp_message(user.phone_number, reply)
    


@csrf_exempt
def whatsapp_webhook(request):
    if request.method == "POST":
        incoming_msg = request.POST.get("Body", "").strip()
        sender = request.POST.get("From", "").replace("whatsapp:", "")

        response = MessagingResponse()
        msg = response.message()

        user, _ = UserProfile.objects.get_or_create(phone_number=sender)

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
        
        if user.pending_action == "set_location_for_crisis":
            user.location = incoming_msg
            user.pending_action = None
            user.save()
            msg.body("Thanks. I will use this location to send help suggestions.")
            return HttpResponse(str(response), content_type="application/xml")
        
        # Continue emergency contact registration
        if user.pending_action == "add_emergency_contact":
            number = incoming_msg.strip()

            # Simple validation
            if not number.startswith("+") or len(number) < 10:
                msg.body("❌ Invalid number format. Please send a valid WhatsApp number including country code.\n\nExample: +254712345678")
                return HttpResponse(str(response), content_type="application/xml")

            # Initialize list if empty
            if not user.emergency_contacts:
                user.emergency_contacts = []

            # Save number
            user.emergency_contacts.append(number)
            user.pending_action = None
            user.save()

            msg.body(
                f"✅ Emergency contact *{number}* saved!\n"
                "You can add more later by typing *add contact*.\n\n"
                "If you're still in crisis, just say: *help* or *I'm in pain*."
            )
            return HttpResponse(str(response), content_type="application/xml")


        # --- Commands and menu ---
        if incoming_msg.lower() == "menu":
            msg.body(
                "📋 *Main Menu*\n"
                "1️⃣ Sickle Cell Info\n"
                "2️⃣ Find Resources\n"
                "3️⃣ Crisis Support\n\n"
                "Type 1, 2, or 3."
            )
            return HttpResponse(str(response), content_type="application/xml")

        if incoming_msg == "1":
            msg.body("🧬 Ask me anything about Sickle Cell Disease.")
            return HttpResponse(str(response), content_type="application/xml")

        # if incoming_msg == "2":
        #     msg.body(
        #         "📚 *Resources Menu*\n"
        #         "1️⃣ Emergency Guide\n"
        #         "2️⃣ Pain Management\n"
        #         "3️⃣ Medication Guide\n"
        #         "4️⃣ Sickle Cell Education\n"
        #         "5️⃣ Mental Health\n"
        #         "6️⃣ Caregiver Support\n"
        #         "7️⃣ Sickle Cell Communities\n\n"
        #         "Type the number to view a resource."
        #     )
        #     return HttpResponse(str(response), content_type="application/xml")
        
        # # --- Resource Selection Handling ---
        # resource_map = {
        #     "1": "Emergency Guide",
        #     "2": "Pain Management",
        #     "3": "Medication Guide",
        #     "4": "Sickle Cell Education",
        #     "5": "Mental Health",
        #     "6": "Caregiver Support",
        #     "7": "Sickle Cell Communities",
        # }
        
        if incoming_msg == "2":
            msg.body(
                "🌍 *Sickle Cell Communities & Support Groups*\n\n"
                
                "🔴 *YouTube Channels*\n"
                "• Sickle Cell 101: https://www.youtube.com/@sicklecell101\n"
                "• Sickle Cell Society UK: https://www.youtube.com/@SickleCellUK\n\n"

                "🔵 *Facebook Groups*\n"
                "• Sickle Cell Warriors: https://www.facebook.com/groups/SCWarriors\n"
                "• Sickle Cell Association: https://www.facebook.com/sicklecellassociation\n\n"

                "🟣 *Instagram Communities*\n"
                "• @sicklecell101: https://instagram.com/sicklecell101\n"
                "• @sicklecellwarriors: https://instagram.com/sicklecellwarriors\n\n"

                "🟠 *Reddit Community*\n"
                "• r/Sicklecell: https://www.reddit.com/r/sicklecell/\n"
                "• r/ChronicIllnes: https://www.reddit.com/r/ChronicIllness/\n\n"
                
                "🌐 *Helpful Websites*\n"
                "• Sickle Cell 101: https://www.sicklecell101.org\n"
                "• Sickle Cell Society UK: https://www.sicklecellsociety.org\n"
                "• CDC Sickle Cell Info: https://www.cdc.gov/ncbddd/sicklecell\n"
                "• WHO Sickle Cell: https://www.who.int/health-topics/sickle-cell-disease\n\n"
                
                "Feel free to explore these communities for support and information!"
            )
            return HttpResponse(str(response), content_type="application/xml")
        
        # if incoming_msg in resource_map:
        #    title = resource_map[incoming_msg]
        #    resource = Resource.objects.filter(title__icontains=title).first()
        #    if resource:
        #        text = f"📖 *{resource.title}*\n\n{resource.description or ''}"
        #        if resource.link:
        #            text += f"\n🔗 More info: {resource.link}"
        #        msg.body(text[:1500])  # WhatsApp-friendly limit
        #    else:
        #        msg.body("⚠️ Sorry, this resource is currently unavailable.")
        #    return HttpResponse(str(response), content_type="application/xml")

        # --- Menu Options - Crisis Support ---
        if incoming_msg == "3":
            msg.body("🚑 Crisis support activated. How are you feeling?")
            return HttpResponse(str(response), content_type="application/xml")

        # Crisis check
        if detect_crisis(incoming_msg):
            
            # 1. Require location next
            if not user.location:
                msg.body(
                    "📍 I need your location name to guide you to the nearest hospital.\n"
                    "Please send your location (e.g., 'Nairobi', 'Kisumu', 'Rongai')."
                )
                user.pending_action = "set_location_for_crisis"
                user.save()
                return HttpResponse(str(response), content_type="application/xml")


            # 2. Require emergency contacts first
            if not user.emergency_contacts or len(user.emergency_contacts) == 0:
                msg.body(
                    "⚠️ You have *no emergency contacts* saved.\n"
                    "Please send at least *one phone number* of someone to notify during a crisis.\n\n"
                    "Example: +254712345678"
                )
                user.pending_action = "add_emergency_contact"
                user.save()
                return HttpResponse(str(response), content_type="application/xml")

            
            # 3. If both exist → proceed with crisis help
            handle_crisis(user, incoming_msg)

            # msg.body(
            #     "🚨 *Crisis Detected!*\n"
            #     "I've notified your emergency contacts and sent you nearby hospitals.\n"
            #     "Follow the steps above and stay safe."
            # )            
            return HttpResponse(str(response), content_type="application/xml")
        
        # --- 1. CLEAR LOCATION ---
        if incoming_msg.lower() in ["clear location", "reset location"]:
            user.location = None
            user.save()

            msg.body("🗑️ Your saved location has been cleared.\nYou can set a new one by typing:\n\n• location Nairobi\n• set location Kisumu")
            return HttpResponse(str(response), content_type="application/xml")


        # --- 2. CLEAR EMERGENCY CONTACTS ---
        if incoming_msg.lower() in ["clear contacts", "reset contacts", "delete contacts"]:
            user.emergency_contacts = []
            user.save()

            msg.body("🗑️ All emergency contacts have been removed.\nYou can add a new one anytime using:\n\n• add contact\n• +2547xxxxxxxx")
            return HttpResponse(str(response), content_type="application/xml")
        
        # --- Reset chat history ---
        if incoming_msg.lower() == "reset":
            user.chats.all().delete()
            msg.body("🧠 Chat memory cleared!")
            return HttpResponse(str(response), content_type="application/xml")
        
        # --- Reminder flow ---
        if incoming_msg.lower() in ["reminder", "set reminder", "remind me"]:
            handle_reminder_flow(user, incoming_msg, msg)
            return HttpResponse(str(response), content_type="application/xml")
        
        # Add emergency contact flow
        if incoming_msg.lower() in ["add contact", "add emergency contact"]:
            msg.body("📞 Send the phone number of your emergency contact.\nExample: +254712345678")
            user.pending_action = "add_emergency_contact"
            user.save()
            return HttpResponse(str(response), content_type="application/xml")
        
        # Continue reminder conversation if pending
        if user.pending_action:
            handled = handle_reminder_flow(user, incoming_msg, msg)
            if handled:
                return HttpResponse(str(response), content_type="application/xml")
                
        #  --- AI HANDLING (ASYNC) ---
        # Save user message first
        user.chats.create(message=incoming_msg, sender="user")

        # Immediate WhatsApp response
        threading.Thread(target=handle_ai_async, args=(user, incoming_msg)).start()

        return HttpResponse(str(response), content_type="application/xml")

    return HttpResponse("OK")
