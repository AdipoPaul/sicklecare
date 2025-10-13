from django.db import models

class UserProfile(models.Model):
    phone_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=20, choices=[
        ("patient", "Patient"),
        ("caregiver", "Caregiver"),
        ("donor", "Donor")
    ], blank=True, null=True)
    registered = models.BooleanField(default=False)
    last_interaction = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone_number} - {self.role}"

class Resource(models.Model):
    category = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    contact = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.category})"
