from django.db import models
from user_auth.models import CustomUser as User

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('FAILED', 'Failed'),
        ('SUCCESS', 'Success'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('PAYPAL', 'PayPal'),
        ('MPESA', 'Mpesa'),
    ]

    PAYMENT_PLAN_CHOICES = [
        ('pay_upfront', 'Upfront'),
        ('2_month_inst', 'Two Months'),
        ('3_month_ins', 'Three Months'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    service_type = models.CharField(max_length=50)
    service_id = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    payment_plan = models.CharField(max_length=15, choices=PAYMENT_PLAN_CHOICES)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} - {self.service_type} - {self.status}' if self.user else f'{self.pk} - {self.service_type} - {self.status}'

class PreSignup(models.Model):
    """Model to store temporary user details before they sign up."""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    service_type = models.CharField(max_length=50)
    service_id = models.PositiveIntegerField()
    payment_id = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.service_type}"
    
class MpesaCallback(models.Model):
    """Model to store M-Pesa callback data."""

    merchant_request_id = models.CharField(max_length=255)
    checkout_request_id = models.CharField(max_length=255)
    result_code = models.IntegerField()  # 0 for success, other values indicate failure
    result_desc = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    mpesa_receipt_number = models.CharField(max_length=255, null=True, blank=True)
    transaction_date = models.DateTimeField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"Transaction {self.mpesa_receipt_number or self.checkout_request_id} - {self.result_desc}"

admin_model = [Payment, PreSignup, MpesaCallback]