from django.db import models
from django.utils import timezone

class UserProfile(models.Model):
    phone_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=20, choices=[
        ("patient", "Patient"),
        ("caregiver", "Caregiver"),
        ("donor", "Donor")
    ], blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    emergency_contacts = models.JSONField(default=list, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    condition_severity = models.CharField(max_length=50, blank=True, null=True)
    preferred_language = models.CharField(max_length=20, default='English')
    registered = models.BooleanField(default=False)
    last_interaction = models.DateTimeField(auto_now=True)
    pending_action = models.CharField(max_length=50, null=True, blank=True)
    temp_reminder_text = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.phone_number or self.name
    
class ChatHistory(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="chats")
    message = models.TextField()
    sender = models.CharField(max_length=10, choices=[("user", "User"), ("bot", "Bot")])
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.phone_number} ({self.sender})"

# models.py

class Resource(models.Model):
    CATEGORY_CHOICES = [
        ("education", "Sickle Cell Education"),
        ("emergency", "Emergency Guide"),
        ("nutrition", "Nutrition & Hydration"),
        ("pain", "Pain Management"),
        ("mental", "Mental Health"),
        ("caregiver", "Caregiver Guide"),
    ]

    title = models.CharField(max_length=200, default="Untitled Resource")
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    file = models.FileField(upload_to="resources/", null=True, blank=True)
    link = models.URLField(blank=True, null=True)
    language = models.CharField(max_length=20, default="English")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    

class Reminder(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="reminders")
    message = models.CharField(max_length=500)
    time = models.TimeField()  # HH:MM
    date = models.DateField(null=True, blank=True)
    recurring = models.BooleanField(default=False)  
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.phone_number} at {self.time} - {self.message}"
