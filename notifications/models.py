from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('chat', 'Chat'),
        ('live_class', 'Live Class'),
        ('assignment', 'Assignment'),
        ('submission', 'Submission'),
        ('transaction', 'Transaction'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.notification_type} for {self.user.username}"

class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    chat = models.BooleanField(default=True)
    live_class = models.BooleanField(default=True)
    assignment = models.BooleanField(default=True)
    submission = models.BooleanField(default=True)
    transaction = models.BooleanField(default=True)

    def __str__(self):
        return f"Preferences for {self.user.username}"