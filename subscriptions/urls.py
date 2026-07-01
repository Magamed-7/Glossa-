from django.urls import path
from .views import (
    PlanListView,
    UserSubscriptionView,
    CreatePaymentView,
    DemoPayView,
    TrialActivationView,
    CreatePaymentRequestView,
    MyPaymentRequestView,
)

app_name = 'subscriptions'

urlpatterns = [
    path('plans/', PlanListView.as_view(), name='plan-list'),

    path('my/', UserSubscriptionView.as_view(), name='my-subscription'),

    path('pay/', CreatePaymentView.as_view(), name='create-payment'),

    path('demo-pay/', DemoPayView.as_view(), name='demo-pay'),

    path('trial/activate/', TrialActivationView.as_view(), name='trial-activate'),

    path('payment-request/', CreatePaymentRequestView.as_view(), name='create-payment-request'),

    path('payment-request/my/', MyPaymentRequestView.as_view(), name='my-payment-request'),
]
