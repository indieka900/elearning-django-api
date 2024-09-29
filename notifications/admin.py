from django.contrib import admin
from .models import NotificationPreference, Notification

admin.site.register(NotificationPreference)
admin.site.register(Notification)