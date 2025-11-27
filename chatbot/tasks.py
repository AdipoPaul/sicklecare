from django.utils import timezone
from datetime import datetime

from .utils import send_whatsapp_message
from .models import Reminder

def handle_reminder_flow(user, incoming_msg, msg):

    if not user.pending_action:
        user.pending_action = "ask_reminder_text"
        user.save()
        msg.body("📌 Sure! What should I remind you about?")
        return True

    elif user.pending_action == "ask_reminder_text":
        user.temp_reminder_text = incoming_msg
        user.pending_action = "ask_reminder_time"
        user.save()
        msg.body("⏰ Great! What time? (24hr format HH:MM)")
        return True

    elif user.pending_action == "ask_reminder_time":
        try:
            datetime.strptime(incoming_msg, "%H:%M")
            Reminder.objects.create(
                user=user,
                message=user.temp_reminder_text,
                time=incoming_msg,
                recurring=True
            )
            msg.body(f"✅ Daily reminder set for *{incoming_msg}*")
        except ValueError:
            msg.body("❌ Invalid time format. Use HH:MM (24hr)")

        user.pending_action = None
        user.temp_reminder_text = None
        user.save()
        return True

    return False

        