from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.test import override_settings

from subscriptions.models import Plan, Subscription, PaymentEvent, TrialPeriod

User = get_user_model()


def make_plan(period='monthly', price='9.99', **kwargs):
    return Plan.objects.create(
        name=f'Plan {period}',
        period=period,
        price=price,
        currency='USD',
        is_active=True,
        **kwargs,
    )


def make_user(username='testuser', email='test@example.com', **kwargs):
    return User.objects.create_user(
        username=username,
        email=email,
        password='password123',
        is_verified=True,
        **kwargs,
    )


class PlanListTests(APITestCase):

    def setUp(self):
        self.url = reverse('subscriptions:plan-list')
        self.free_plan = make_plan(period='free', price='0.00')
        self.monthly_plan = make_plan(period='monthly')
        self.annual_plan = make_plan(period='annual', price='79.99')
        Plan.objects.create(
            name='Hidden', period='semi_annual', price='49.99',
            is_active=False,
        )

    def test_only_active_plans_returned(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  

    def test_no_auth_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserSubscriptionTests(APITestCase):

    def setUp(self):
        self.user = make_user()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('subscriptions:my-subscription')
        self.plan = make_plan()

    def test_no_subscription_returns_none(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['subscription'])
        self.assertIsNone(response.data['trial'])

    def test_active_subscription_returned(self):
        Subscription.objects.create(
            user=self.user, plan=self.plan, status='active',
            started_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=30),
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['subscription'])
        self.assertEqual(response.data['subscription']['status'], 'active')


@override_settings(DEBUG=True)
class DemoPayTests(APITestCase):

    def setUp(self):
        self.user = make_user(username='demouser', email='demo@example.com')
        self.client.force_authenticate(user=self.user)
        self.url = reverse('subscriptions:demo-pay')
        self.plan = make_plan()

    def test_demo_pay_creates_active_subscription(self):
        response = self.client.post(self.url, {'plan_id': str(self.plan.id)})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        sub = Subscription.objects.get(user=self.user)
        self.assertEqual(sub.status, 'active')

        payment = PaymentEvent.objects.get(subscription=sub)
        self.assertTrue(payment.is_demo)
        self.assertEqual(payment.status, 'success')

    def test_demo_pay_free_plan_fails(self):
        free = make_plan(period='free', price='0.00')
        
        response = self.client.post(self.url, {'plan_id': str(free.id)})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(DEBUG=False)
    def test_demo_pay_blocked_in_production(self):
        response = self.client.post(self.url, {'plan_id': str(self.plan.id)})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TrialActivationTests(APITestCase):

    def setUp(self):
        self.user = make_user(username='trialuser', email='trial@example.com')
        self.client.force_authenticate(user=self.user)
        self.url = reverse('subscriptions:trial-activate')
        self.monthly_plan = make_plan(period='monthly')

    def test_trial_activation_success(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        trial = TrialPeriod.objects.get(user=self.user)
        self.assertTrue(trial.is_used)
        self.assertGreater(trial.expires_at, timezone.now())

        sub = Subscription.objects.get(user=self.user, is_trial=True)
        self.assertEqual(sub.status, 'active')

    def test_trial_cannot_be_activated_twice(self):
        self.client.post(self.url)  
        response = self.client.post(self.url)  
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_trial_blocked_if_active_subscription_exists(self):
        Subscription.objects.create(
            user=self.user,
            plan=self.monthly_plan,
            status='active',
            started_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=30),
        )
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
