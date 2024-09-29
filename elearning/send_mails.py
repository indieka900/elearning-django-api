from user_auth.models import CustomUser as User
from django.conf import settings
from .email_backend import send_email

def format_role(role):
    words = role.split('-')
    words = [word.capitalize() for word in words]
    formatted = ' '.join(words)
    
    return formatted

# sending registration mails
def send_registration_emails(user: User):
    # Email to the registered user
    user_subject = "Welcome to My Site!"
    user_message = f"""
    Hi {user.username},

    Thank you for registering with My Site. We are excited to have you on board as a {user.role}!

    If you have any questions or need assistance, feel free to reach out to our support team.

    Best regards,
    My Site Team
    """

    # Sending email to the user
    my_email = send_email(
            subject=user_subject, 
            message=user_message, 
            recipient_list=[user.email],
            use_accounts_backend=True ,
            use_styling=False,
    )
    my_email.send()

    # Email to the academy team
    academy_subject = "New User Registration Notification"
    academy_message = f"""
    A new user has registered on My Site.

    Details:
    Name: {user.first_name} {user.last_name}
    Username: {user.username}
    Email: {user.email}
    Role: {user.role}

    Please follow up as necessary.

    Best regards,
    System Notification
    """

    # Sending email to the academy team
    _email = send_email(
            subject=academy_subject, 
            message=academy_message, 
            recipient_list=['indiekaj@gmail.com'],
            use_accounts_backend=True ,
            use_styling=False,
    )
    _email.send()
    
# Send the instractor invitation links
def send_invitation_emails(user: User, email, password, username, student=False):
    role = "Student" if student else "Instructor"
    frontend_url = f"{settings.FRONTEND_URL}/login"
    support_email = settings.SUPPORT_EMAIL
    
    # Common email subject and message for the user
    user_subject = f"Invitation to join My Site as a {role}"
    user_message = f"""
    Hello {username},

    You have been invited to join our platform as a {role}. Below are your login credentials to access your account:

        Login Details:

        Email: {email}
        Password: {password}
        Please log in to your account using the link below and update your password for security purposes:

        {frontend_url}

    We are excited to have you on board. If you have any questions or need assistance, feel free to reach out to us at {support_email}.

    Best regards,
    My Site Team
    """

    # Sending email to the invited user
    my_email = send_email(
        subject=user_subject, 
        message=user_message, 
        recipient_list=[email],
        use_accounts_backend=True,
        use_styling=False,
    )
    my_email.send()

    # Academy team email details
    academy_subject = f"New {role} Invitation"
    academy_message = f"""
    {user.email} has invited a new {role}.

    Details:
    Email: {email}

    Please follow up as necessary.

    Best regards,
    System Notification
    """

    # Sending email to the academy team
    _email = send_email(
        subject=academy_subject, 
        message=academy_message, 
        recipient_list=['indiekaj@gmail.com'],
        use_accounts_backend=True,
        use_styling=False,
    )
    _email.send()

        
