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
    condition_severity = models.CharField(max_length=50, blank=True, null=True)
    preferred_language = models.CharField(max_length=20, default='English')
    registered = models.BooleanField(default=False)
    last_interaction = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.phone_number or self.name
    
class ChatHistory(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="chats")
    message = models.TextField()
    sender = models.CharField(max_length=10, choices=[("user", "User"), ("bot", "Bot")])
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.phone_number} ({self.sender})"

class Resource(models.Model):
    category = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    contact = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.category})"
    

class Reminder(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    reminder_type = models.CharField(max_length=50)  # e.g., Medication, Hydration
    message = models.TextField()
    reminder_time = models.DateTimeField(default=timezone.now)
    repeat_daily = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.reminder_type} - {self.user.name}"
