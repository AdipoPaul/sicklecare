from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from django.utils import timezone
from .models import Reminder
from .utils import send_whatsapp_message


scheduler = BackgroundScheduler()

def send_due_reminders():
    now = datetime.now().strftime("%H:%M")

    # Fetch reminders matching the time and already created
    reminders = Reminder.objects.filter(
        time=now,
        recurring=True,
        created_at__lte=timezone.now()
    )

    for reminder in reminders:
        try:
            message = f"⏰ Reminder: {reminder.message}"
            send_whatsapp_message(reminder.user.phone_number, message)
            print(f"Reminder sent to {reminder.user.phone_number}: {reminder.message}")
        except Exception as e:
            print(f"Failed to send reminder to {reminder.user.phone_number}: {e}")


def start_scheduler():
    scheduler.add_job(send_due_reminders, 'cron', minute='*')  # runs every minute
    scheduler.start()
    print("Reminder scheduler started.")
