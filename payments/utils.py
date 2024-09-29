from decimal import Decimal
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
import paypalrestsdk
import requests
from notifications.services import NotificationService
from payments.models import Payment, PreSignup
from payments.serializers import PaymentSerializer, PreSignupSerializer
from user_auth.models import CustomUser
from .mpesa_client import MpesaClient
from elearning.models import SubscriptionPlan

class PaymentUtils:
    @staticmethod
    def configure_paypal():
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET,
        })

    @staticmethod
    def handle_pre_signup(data):
        pre_signup_serializer = PreSignupSerializer(data=data)
        if not pre_signup_serializer.is_valid():
            return None, Response(pre_signup_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        pre_signup, created = PreSignup.objects.get_or_create(
            email=data['email'],
            defaults=data
        )

        if not created:
            for attr, value in data.items():
                setattr(pre_signup, attr, value)
            pre_signup.save()

        return pre_signup, None

    @staticmethod
    def create_payment(data, pre_signup):
        serializer = PaymentSerializer(data=data)
        if serializer.is_valid():
            payment = serializer.save()
            pre_signup.payment_id = payment
            pre_signup.save()
            return payment, None
        return None, Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def handle_paypal_payment(payment: Payment):
        PaymentUtils.configure_paypal()
        paypal_payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": settings.FRONTEND_URL + "/payment/success",
                "cancel_url": settings.FRONTEND_URL + "/payment/cancel"
            },
            "transactions": [{
                "amount": {
                    "total": str(payment.amount),
                    "currency": "USD"
                },
                "description": f"Payment for {payment.service_type}"
            }]
        })

        if paypal_payment.create():
            payment.transaction_id = paypal_payment.id
            payment.status = 'PENDING'
            payment.save()

            approval_url = next(link.href for link in paypal_payment.links if link.rel == "approval_url")
            return Response({"paymentID": paypal_payment.id, "approval_url": approval_url}, status=status.HTTP_201_CREATED)
        else:
            payment.status = 'FAILED'
            payment.save()
            return Response({"error": paypal_payment.error}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def handle_mpesa_payment(payment: Payment, phone_number):
        mpesa_client = MpesaClient()
        response = mpesa_client.lipa_na_mpesa_online(
            phone_number=phone_number,
            amount=float(payment.amount),
            account_reference=payment.service_type,
            transaction_desc=f"Payment for {payment.service_type}",
            callback_url=settings.MPESA_CALLBACK_URL,
        )

        if response.get("ResponseCode") == "0":
            payment.transaction_id = response.get("MerchantRequestID")
            payment.status = 'PENDING'
            payment.save()
            data = {
                "message": "Mpesa payment initiated successfully.",
                "payment_id":payment.pk
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            payment.status = 'FAILED'
            payment.save()
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def execute_paypal_payment(payment_id, payer_id):
        PaymentUtils.configure_paypal()
        payment = get_object_or_404(Payment, transaction_id=payment_id)

        # check if payment is already completed
        if payment.status == 'SUCCESS':
            return Response({"status": "Payment already completed"}, status=status.HTTP_200_OK)

        paypal_payment = paypalrestsdk.Payment.find(payment_id)

        if paypal_payment.execute({"payer_id": payer_id}):
            payment.status = 'SUCCESS'
            payment.save()
            return Response({"status": "Payment completed"}, status=status.HTTP_200_OK)
        else:
            if paypal_payment.error['name'] == 'PAYMENT_ALREADY_DONE':
                return Response({"status": "Payment already completed"}, status=status.HTTP_200_OK)
            elif paypal_payment.error['name'] == 'PAYMENT_NOT_APPROVED_FOR_EXECUTION':
                payment.status = 'FAILED'
                payment.save()
                return Response({
                    "error": paypal_payment.error['message']
                }, status=status.HTTP_200_OK)
            else:
                payment.status = 'FAILED'
                payment.save()
                return Response(paypal_payment.error, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def fetch_mpesa_transaction(request_id):
        payment = get_object_or_404(Payment, transaction_id=request_id)
        url = f"https://mpepe-one.vercel.app/transaction/{request_id}/"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            if data['result_code'] == 0:
                payment.status = "SUCCESS"
                payment.save()
               
               # Fetch PreSignup information
            pre_signup = PreSignup.objects.filter(payment_id=payment.id).first()
            if pre_signup:
                # Check if the user exists
                user = CustomUser.objects.filter(email=pre_signup.email).first()
                if user:
                    # Use NotificationService if the user exists
                    NotificationService.send_notification(
                        user=user,
                        notification_type='transaction',
                        content=f'Payment with transaction ID {request_id} was successful.',
                        email_subject='Payment Successful',
                        email_body=f"Dear {user.username},\n\nYour payment with transaction ID {request_id} was successful.",
                    )
                else:
                    # Send email directly if user does not exist
                    email_body = f"Dear {pre_signup.first_name},\n\nYour payment with transaction ID {request_id} was successful."
                    send_mail(
                        subject='Payment Successful',
                        message=email_body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[pre_signup.email],
                        fail_silently=False,
                    )
                return Response({"message": "Payment was made succesfully"}, status=status.HTTP_200_OK)
            else:
                payment.status = "FAILED"

            payment.save()
            return Response({"error": "Transaction failed"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to fetch transaction data from mpepe app."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @staticmethod
    def get_student_data(user, service_type='course'):
        # Find all payments made by the user for the given service_type
        payments = Payment.objects.filter(user=user, service_type=service_type)

        total_fees = Decimal(0)
        for payment in payments:
            try:
                subscription_plan = SubscriptionPlan.objects.get(course_id=payment.service_id)
                total_fees += Decimal(subscription_plan.display_price)  # Use display_price, or any other field
            except SubscriptionPlan.DoesNotExist:
                continue

        # Calculate amount paid, balance, and refund
        amount_paid = payments.filter(status='SUCCESS').aggregate(Sum('amount'))['amount__sum'] or 0
        balance = total_fees - amount_paid
        refund = payments.filter(status='REFUND').aggregate(Sum('amount'))['amount__sum'] or 0

        transactions = PaymentUtils.get_student_transactions(user=user, service_type=service_type)

        return {
            'summary': {
                'total_fees': f"{total_fees:.2f}", 
                'amount_paid': f"{amount_paid:.2f}",
                'balance': f"{balance:.2f}",
                'refund': f"{refund:.2f}"
            },
            'transactions': transactions
        }

    @staticmethod
    def get_student_transactions(user, service_type='course'):
        # Retrieve all transactions for a specific student and service_type
        return Payment.objects.filter(user=user, service_type=service_type, status='SUCCESS').order_by('-timestamp')

    @staticmethod
    def get_admin_data(service_type='course'):
        # Calculate total earnings, refund, and net earnings for the admin based on the service_type
        total_earnings = Payment.objects.filter(service_type=service_type, status='SUCCESS').aggregate(Sum('amount'))['amount__sum'] or 0
        refund = Payment.objects.filter(service_type=service_type, status='REFUND').aggregate(Sum('amount'))['amount__sum'] or 0
        net_earnings = total_earnings - refund

        transactions = PaymentUtils.get_admin_transactions(service_type=service_type)

        return {
            'summary': {
                'total_earnings': total_earnings,
                'refund': refund,
                'net_earnings': net_earnings
            },
            'transactions': transactions
        }
    

    @staticmethod
    def get_admin_transactions(service_type='course'):
        # Retrieve all transactions for a specific service_type (for admin)
        return Payment.objects.filter(service_type=service_type, status='SUCCESS').order_by('-timestamp')