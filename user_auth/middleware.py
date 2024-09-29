import user_agents
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import requests

from elearning.email_backend import send_email
from .models import KnownDevice

from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
import requests
import user_agents

class DeviceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            user_agent = user_agents.parse(request.META.get('HTTP_USER_AGENT', ''))
            device = user_agent.device.family or "Other"
            os = user_agent.os.family or "Unknown OS"
            browser = user_agent.browser.family or "Unknown Browser"

            # print(f"Authenticated user: {request.user.email}, Device: {device}, OS: {os}, Browser: {browser}")

            if KnownDevice.is_new_device(request.user, device, os, browser):
                # print(f"New device detected for user: {request.user.email}")
                KnownDevice.objects.create(user=request.user, device=device, os=os, browser=browser)
                self.send_new_device_alert(request, request.user, device, os, browser)
       
        return response

    def send_new_device_alert(self, request, user, device, os, browser):
        ip_address =  request.META.get('REMOTE_ADDR')
        city = self.get_city_from_ip(ip_address)
        login_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        device_identifier = f"{device} - {os} - {browser}"
        subject = 'Security Alert: New Device Login Notification'
        
        message = f"""
        Dear {user.email},

        We wanted to inform you that a new device has logged into your wHTa Networks account. For your security, we want to ensure that it was you who authorized this login.

        Login Details:
        Date and Time: {login_time}
        Device: {device_identifier}
        Location: {city}

        If this login was authorized by you, no further action is needed. However, if you do not recognize this activity, please follow these steps immediately:
        Change Your Password: [link to change password]
        Report Unauthorized Access: Contact Support via the form on the website.
        Review Account Activity: [link to account activities]

        Your security is our priority, and we are here to assist you with any concerns.

        Best Regards,
        """
        
        my_email = send_email(
            subject, 
            message, 
            recipient_list=[user.email],
            use_accounts_backend=True ,
            use_styling=False,
        )
        my_email.send()
        # print("Email sent")

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        # print(f"Client IP: {ip}")
        return ip

    def get_city_from_ip(self, ip_address):
        try:
            response = requests.get("https://ipapi.co/41.90.179.241/json").json()
            city = response.get("city")
            # print(f"City from IP: {city}")
            return city
        except Exception as e:
            # print(f"Error fetching city from IP: {e}")
            return "Unknown"
