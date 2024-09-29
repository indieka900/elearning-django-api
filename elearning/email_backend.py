from django.core.mail import get_connection, EmailMessage, EmailMultiAlternatives
from django.conf import settings

def send_email(
    subject : str, message : str, recipient_list : list, from_email=None, 
    use_accounts_backend=False, use_styling=True,
):
    
    email_user = settings.EMAIL_HOST_USER
    email_password = settings.EMAIL_HOST_PASSWORD

    # Set up the email connection with the specific credentials
    connection = get_connection(
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        username=email_user,
        password=email_password,
        use_tls=settings.EMAIL_USE_TLS,
        use_ssl=settings.EMAIL_USE_SSL
    )
    
    
    
    # Send the email
    if use_styling:
        email = EmailMultiAlternatives(
            subject,
            body=message,
            from_email=from_email or email_user,
            to=recipient_list,
            connection=connection
        )
    else:
        email = EmailMessage(
            subject,
            message,
            from_email=from_email or email_user,
            to=recipient_list,
            connection=connection
        )
    
    return email
    
    if(use_styling):
        email.attach_alternative(html_message, "text/html")
        
    email.send()
