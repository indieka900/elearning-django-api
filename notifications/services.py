from .models import Notification, NotificationPreference
from django.conf import settings
from elearning.email_backend import send_email

class NotificationService:
    @staticmethod
    def send_notification(user, notification_type, content, email_subject=None, email_body=None, 
                          recipient_email=None, sender_email=None, use_accounts_backend=False, 
                          use_styling=True, attachments=None):
        # Create platform notification
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            content=content
        )

        # Check user preferences
        try:
            preferences = NotificationPreference.objects.get(user=user)
        except NotificationPreference.DoesNotExist:
            preferences = NotificationPreference.objects.create(user=user)

        # Check if the user has turned off this notification type
        if getattr(preferences, notification_type, True):
            if email_subject and email_body:
                recipient_email = recipient_email or user.email
                sender_email = sender_email or settings.DEFAULT_FROM_EMAIL

                email = send_email(
                    subject=email_subject,
                    message=email_body,
                    recipient_list=[recipient_email],
                    from_email=sender_email,
                    use_accounts_backend=use_accounts_backend,
                    use_styling=use_styling
                )

                # Attach files if any
                if attachments:
                    for attachment in attachments:
                        email.attach(attachment['name'], attachment['content'], attachment['content_type'])

                email.send()
                notification.is_sent_as_email = True
                notification.save()

        return notification

    @staticmethod
    def get_unread_notifications(user):
        return Notification.objects.filter(user=user, is_read=False)

    @staticmethod
    def mark_as_read(notification_id):
        notification = Notification.objects.get(id=notification_id)
        notification.is_read = True
        notification.save()