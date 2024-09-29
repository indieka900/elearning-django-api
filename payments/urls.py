from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, MpesaCallbackView

router = DefaultRouter()
# Payment endmpoint for all payment methods
router.register(r'make-payment', PaymentViewSet, basename='payments')

urlpatterns = [
    path('', include(router.urls)),
    path('paypal/execute/', PaymentViewSet.as_view({'post': 'process_paypal_payment'}), name='process_paypal_payment'),
    path('mpesa/status/<int:payment_id>/', PaymentViewSet.as_view({'get': 'mpesa_transaction_status'}), name='mpesa_transaction_status'),
    path('mpesa/callback/', MpesaCallbackView.as_view(), name='mpesa_callback'),
]
