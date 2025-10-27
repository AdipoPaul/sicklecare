import os
from celery import shared_task
from django.utils import timezone
from twilio.rest import Client
from .models import Reminder, UserProfile
from .utils import get_ai_response, send_whatsapp_message  # custom Twilio helper

@shared_task
def send_due_reminders():
    now = timezone.now()
    reminders = Reminder.objects.filter(
        reminder_time__lte=now, is_active=True
    )
    for reminder in reminders:
        send_whatsapp_message(
            reminder.user.phone_number,
            f"🔔 Reminder: {reminder.message}"
        )
        if reminder.repeat_daily:
            reminder.reminder_time += timezone.timedelta(days=1)
        else:
            reminder.is_active = False
        reminder.save()

def send_to_deepseek_async(phone, user_msg):
    try:
        user = UserProfile.objects.get(phone_number=phone)
        ai_reply = get_ai_response(user, user_msg)

        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")

        if not account_sid or not auth_token:
            print("[ERROR] Missing Twilio credentials in environment variables.")
            return

        # Send message back via Twilio API
        client = Client(account_sid, auth_token)
        client.messages.create(
            from_="whatsapp:+14155238886",  # your Twilio sandbox number
            to=f"whatsapp:{phone}",
            body=ai_reply
        )
        print(f"[INFO] Sent AI reply to {phone}")
        
    except Exception as e:
        print(f"[ERROR] send_to_deepseek_async failed: {e}")