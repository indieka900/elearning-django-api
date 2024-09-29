import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
import base64
from datetime import datetime

class MpesaClient:
    """
    Client for interacting with the Safaricom M-Pesa API.

    This class provides methods to authenticate, perform STK push payments, and register C2B URLs.

    Attributes:
        consumer_key (str): The M-Pesa API consumer key.
        consumer_secret (str): The M-Pesa API consumer secret.
        api_base_url (str): The base URL for the M-Pesa API, determined by environment.
    """

    def __init__(self):
        """
        Initializes the MpesaClient with consumer key, secret, and API base URL.
        """

        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.api_base_url = "https://sandbox.safaricom.co.ke" if settings.MPESA_ENVIRONMENT == 'sandbox' else "https://api.safaricom.co.ke"

    def authenticate(self):
        """
        Authenticates with the M-Pesa API to obtain an access token.

        Returns:
            str: The access token if authentication is successful, else None.
        """

        auth_url = f"{self.api_base_url}/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(auth_url, auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret))
        if response.status_code == 200:
            return response.json()['access_token']
        return None

    def lipa_na_mpesa_online(self, phone_number, amount, account_reference, transaction_desc, callback_url):
        """
        Initiates an STK push payment request to M-Pesa.

        Args:
            phone_number (str): The phone number of the customer.
            amount (int): The amount to be paid.
            account_reference (str): The account reference for the transaction.
            transaction_desc (str): A description of the transaction.
            callback_url (str): The URL for receiving callback notifications.

        Returns:
            dict: The response from the M-Pesa API.
        """

        access_token = self.authenticate()
        if not access_token:
            return {"error": "Failed to authenticate"}

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}".encode()).decode('utf-8')

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerBuyGoodsOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": settings.MPESA_PARTYB,
            # "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        api_url = f"{self.api_base_url}/mpesa/stkpush/v1/processrequest"
        response = requests.post(api_url, json=payload, headers=headers)

        return response.json()

    def register_c2b_urls(self, validation_url, confirmation_url):
        """
        Registers C2B validation and confirmation URLs with the M-Pesa API.

        Args:
            validation_url (str): The URL for validation requests.
            confirmation_url (str): The URL for confirmation requests.

        Returns:
            dict: The response from the M-Pesa API.
        """

        access_token = self.authenticate()
        if not access_token:
            return {"error": "Failed to authenticate"}

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "ShortCode": settings.MPESA_SHORTCODE,
            "ResponseType": "Completed",
            "ConfirmationURL": confirmation_url,
            "ValidationURL": validation_url
        }

        api_url = f"{self.api_base_url}/mpesa/c2b/v1/registerurl"
        response = requests.post(api_url, json=payload, headers=headers)

        return response.json()
