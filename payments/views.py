from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from .models import Payment, PreSignup, MpesaCallback
from .serializers import PreSignupSerializer, PaymentSerializer
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import paypalrestsdk
from django.conf import settings
from rest_framework import viewsets
from rest_framework.views import APIView 
from elearning.models import Enrollment
from .utils import PaymentUtils
from .mpesa_client import MpesaClient

from django.shortcuts import get_object_or_404
import requests, json
from datetime import datetime


class PaymentViewSet(viewsets.ViewSet):
    """ Handle different payment transactions for various services. """
    permission_classes = [AllowAny]

    def create(self, request):
        # Handle pre-signup
        pre_signup_data = {
            'email': request.data.get('email'),
            'first_name': request.data.get('first_name'),
            'last_name': request.data.get('last_name'),
            'service_type': request.data.get('service_type'),
            'service_id': request.data.get('service_id'),
            'phone_number': request.data.get('phone_number')
        }

        # validate presignup data
        pre_signup_serializer = PreSignupSerializer(data=pre_signup_data)
        if not pre_signup_serializer.is_valid():
            return Response(pre_signup_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # check if presignup exists
        pre_signup, created = PreSignup.objects.get_or_create(
            email=pre_signup_data['email'],
            defaults=pre_signup_data
        )

        if not created:
            for attr, value in pre_signup_data.items():
                setattr(pre_signup, attr, value)
            pre_signup.save()

        # create payment
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save()
            pre_signup.payment_id = payment
            pre_signup.save()

            if payment.payment_method == 'PAYPAL':
                return PaymentUtils.handle_paypal_payment(payment)
            elif payment.payment_method == 'MPESA':
                return PaymentUtils.handle_mpesa_payment(payment, pre_signup.phone_number)
            else:
                return Response({"error": "Invalid payment method."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def process_paypal_payment(self, request):
        """ Process PayPal payment. """
        payment_id = request.data.get('paymentID')
        payer_id = request.data.get('payerID')
        return PaymentUtils.execute_paypal_payment(payment_id, payer_id)

    def mpesa_transaction_status(self, request, payment_id):
        """ Fetch M-Pesa transaction status. """
        try:
            transaction_id = Payment.objects.get(id=payment_id).transaction_id
            return PaymentUtils.fetch_mpesa_transaction(transaction_id)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

class MpesaCallbackView(APIView):
    """ Handle M-Pesa callback from Safaricom. """
    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode('utf-8'))
        callback_data = data.get("Body", {}).get("stkCallback", {})

        # Extract basic transaction details
        merchant_request_id = callback_data.get("MerchantRequestID")
        checkout_request_id = callback_data.get("CheckoutRequestID")
        result_code = callback_data.get("ResultCode")
        result_desc = callback_data.get("ResultDesc")

        # Variables for optional fields
        amount = None
        mpesa_receipt_number = None
        transaction_date = None
        phone_number = None

        # Parse the metadata if the transaction was successful
        if result_code == 0:
            callback_metadata = callback_data.get("CallbackMetadata", {}).get("Item", [])
            for item in callback_metadata:
                if item["Name"] == "Amount":
                    amount = item["Value"]
                elif item["Name"] == "MpesaReceiptNumber":
                    mpesa_receipt_number = item["Value"]
                elif item["Name"] == "TransactionDate":
                    transaction_date = datetime.strptime(str(item["Value"]), "%Y%m%d%H%M%S")
                elif item["Name"] == "PhoneNumber":
                    phone_number = str(item["Value"])

        # Save the data to the database
        MpesaCallback.objects.create(
            merchant_request_id=merchant_request_id,
            checkout_request_id=checkout_request_id,
            result_code=result_code,
            result_desc=result_desc,
            amount=amount,
            mpesa_receipt_number=mpesa_receipt_number,
            transaction_date=transaction_date,
            phone_number=phone_number
        )

        return Response({"ResultCode": 0, "ResultDesc": "Accepted"}, status=status.HTTP_200_OK)
