


# payment/urls.py
from django.urls import path
from .views import (
    CreatePaymentView, 
    VerifyPaymentView, 
    SubscriptionPlansList, 
    CreateSubscription, 
    VerifyPayment, 
    AddJobSlotsView, 
    VerifyJobSlotAddOnView
)

urlpatterns = [
    # Legacy endpoints for single job payments
    path("create-payment/", CreatePaymentView.as_view(), name="create_order"),
    path("verify-payment/", VerifyPaymentView.as_view(), name="verify-payment"),
    
    # Subscription-related endpoints
    path('subscription/plans/', SubscriptionPlansList.as_view(), name='subscription-plans-list'),
    path('subscription/create/', CreateSubscription.as_view(), name='create-subscription'),
    path('subscription/verify/', VerifyPayment.as_view(), name='verify-subscription-payment'),
    
    # Job slots add-on endpoints
    path('job-slots/add/', AddJobSlotsView.as_view(), name='add-job-slots'),
    path('job-slots/verify/', VerifyJobSlotAddOnView.as_view(), name='verify-job-slots'),
]

