from django.contrib import admin
from .models import UserProfile, Resource

admin.site.register(UserProfile)
admin.site.register(Resource)