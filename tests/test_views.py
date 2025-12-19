from django.test import TestCase, Client
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from core.models import Item, Order, OrderItem, Coupon, Address, Refund, UserProfile, Payment
from core.views import is_valid_form, create_ref_code
from datetime import datetime, timezone
from django.urls import reverse
from unittest.mock import patch, Mock
from stripe import error as stripe_error

class CreateRefCodeTest(TestCase):
    def test_create_ref_code_unique(self):
        ref_code1 = create_ref_code()
        ref_code2 = create_ref_code()
        self.assertNotEqual(ref_code1, ref_code2)
    
    def test_create_ref_code_length(self):
        ref_code = create_ref_code()
        self.assertEqual(len(ref_code), 20)


class CartViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="testuser")
        cls.user.set_password("testpassword")
        cls.user.save()
        cls.item = Item(title="Test Item",
                        price=float(2),
                        discount_price=float(1),
                        category="S",
                        label="S",
                        slug="test-item",
                        description="Test item",
                        image=None)
        cls.item.save()

    def setUp(self):
        self.client = Client()
        self.assertTrue(self.client.login(username="testuser", password="testpassword"))

    def test_add_to_cart_item_does_not_exist(self):
        response = self.client.get('/add-to-cart/nonexistent-item/')
        self.assertEqual(response.status_code, 404)

    def test_add_to_cart_adds_to_cart(self):
        order = Order.objects.create(user=self.user, ordered_date=datetime.now(timezone.utc), ordered=False)
        self.assertEqual(OrderItem.objects.count(), 0)

        response = self.client.post('/add-to-cart/test-item/')
        self.assertRedirects(response, reverse("core:order-summary"))

        order.refresh_from_db()
        self.assertEqual(order.items.first().quantity, 1)

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

    def test_add_to_cart_increases_quantity(self):
        order_item = OrderItem.objects.create(user=self.user, ordered=False, item=self.item, quantity=1)
        order = Order.objects.create(user=self.user,
                                     ordered_date=datetime.now(timezone.utc),
                                     ordered=False)
        order.items.set([order_item])
        order.save()

        response = self.client.post('/add-to-cart/test-item/')
        self.assertRedirects(response, reverse("core:order-summary"))

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

        order.refresh_from_db()
        self.assertEqual(order.items.first().quantity, 2)

        order_item.refresh_from_db()
        order_item = OrderItem.objects.get(user=self.user)
        self.assertEqual(order_item.quantity, 2)


    def test_add_to_cart_creates_new_order(self):
        self.assertEqual(Order.objects.count(), 0)

        response = self.client.post('/add-to-cart/test-item/')
        self.assertRedirects(response, reverse("core:order-summary"))

        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.items.first().quantity, 1)

    def test_remove_from_cart_item_does_not_exist(self):
        response = self.client.post('/remove-from-cart/nonexistent-item/')
        self.assertEqual(response.status_code, 404)

    def test_remove_from_cart_item_is_not_in_cart(self):
        Item.objects.create(title="Test Item 2",
                            price=float(5),
                            category='S',
                            label='P',
                            slug='test-item2',
                            description="Test item 2",
                            image=None)
        order_item = OrderItem.objects.create(user=self.user, ordered=False, item=self.item, quantity=1)
        order = Order.objects.create(user=self.user,
                                     ordered_date=datetime.now(timezone.utc),
                                     ordered=False)
        order.items.set([order_item])
        order.save()

        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().quantity, 1)

        response = self.client.post('/remove-from-cart/test-item2/')
        self.assertRedirects(response, reverse("core:product", args=['test-item2']))

        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().quantity, 1)
        self.assertEqual(order.items.first().item.slug, 'test-item')

    def test_remove_from_cart_removes_item_from_cart(self):
        order_item = OrderItem.objects.create(user=self.user, ordered=False, item=self.item, quantity=5)
        order = Order.objects.create(user=self.user,
                                     ordered_date=datetime.now(timezone.utc),
                                     ordered=False)
        order.items.set([order_item])
        order.save()

        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().quantity, 5)

        response = self.client.post('/remove-from-cart/test-item/')
        self.assertRedirects(response, reverse("core:order-summary"))

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(order.items.count(), 0)

    def test_remove_from_cart_order_does_not_exist(self):
        response = self.client.post('/remove-from-cart/test-item/')
        self.assertRedirects(response, reverse("core:product", args=['test-item']))

    def test_remove_single_item_from_cart_item_does_not_exist(self):
        response = self.client.post('/remove-item-from-cart/nonexistent-item/')
        self.assertEqual(response.status_code, 404)

    def test_remove_single_item_from_cart_removes_item_from_cart(self):
        order_item = OrderItem.objects.create(user=self.user, ordered=False, item=self.item, quantity=1)
        order = Order.objects.create(user=self.user,
                                     ordered_date=datetime.now(timezone.utc),
                                     ordered=False)
        order.items.set([order_item])
        order.save()

        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().quantity, 1)

        response = self.client.post('/remove-item-from-cart/test-item/')
        self.assertRedirects(response, reverse("core:order-summary"))

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(order.items.count(), 0)

    def test_remove_single_item_from_cart_decreases_quantity(self):
        order_item = OrderItem.objects.create(user=self.user, ordered=False, item=self.item, quantity=5)
        order = Order.objects.create(user=self.user,
                                     ordered_date=datetime.now(timezone.utc),
                                     ordered=False)
        order.items.set([order_item])
        order.save()

        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().quantity, 5)

        response = self.client.post('/remove-item-from-cart/test-item/')
        self.assertRedirects(response, reverse("core:order-summary"))

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().quantity, 4)

    def test_remove_single_item_from_cart_item_not_in_cart(self):
        Item.objects.create(title="Test Item 2",
                            price=float(5),
                            category='S',
                            label='P',
                            slug='test-item2',
                            description="Test item 2",
                            image=None)
        order_item = OrderItem.objects.create(user=self.user, ordered=False, item=self.item, quantity=1)
        order = Order.objects.create(user=self.user,
                                     ordered_date=datetime.now(timezone.utc),
                                     ordered=False)
        order.items.set([order_item])
        order.save()

        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().quantity, 1)

        response = self.client.post('/remove-item-from-cart/test-item2/')
        self.assertRedirects(response, reverse("core:product", args=['test-item2']))

        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().quantity, 1)
        self.assertEqual(order.items.first().item.slug, 'test-item')

    def test_remove_single_item_from_cart_order_does_not_exist(self):
        response = self.client.post('/remove-item-from-cart/test-item/')
        self.assertRedirects(response, reverse("core:product", args=['test-item']))


class CouponViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Coupon.objects.create(code="valid-coupon", amount=float(1))
        cls.user = User.objects.create(username="testuser")
        cls.user.set_password("testpassword")
        cls.user.save()

    def setUp(self):
        self.client = Client()
        self.assertTrue(self.client.login(username="testuser", password="testpassword"))

    def test_apply_coupon_success(self):
        order = Order.objects.create(user=self.user, ordered=False, ordered_date=datetime.now(timezone.utc))
        self.assertEqual(order.coupon, None)
        response = self.client.post('/add-coupon/', { 'code': 'valid-coupon' })
        self.assertRedirects(response, reverse('core:checkout'))
        order.refresh_from_db()
        self.assertEqual(order.coupon.code, 'valid-coupon')

    def test_apply_coupon_invalid_coupon(self):
        order = Order.objects.create(user=self.user, ordered=False, ordered_date=datetime.now(timezone.utc))
        self.assertEqual(order.coupon, None)
        response = self.client.post('/add-coupon/', { 'code': 'invalid-coupon' })
        self.assertRedirects(response, reverse('core:checkout'))
        order.refresh_from_db()
        self.assertEqual(order.coupon, None)

    def test_apply_coupon_no_active_order(self):
        response = self.client.post('/add-coupon/', { 'code': 'valid-coupon' })
        self.assertRedirects(response, reverse('core:checkout'))

    def test_apply_coupon_invalid_form(self):
        response = self.client.post('/add-coupon/', { 'invalid-form-field': 'valid-coupon' })
        self.assertEqual(response.status_code, 200)
        
class IsValidFormTest(TestCase):
    def test_is_valid_form_true(self):
        test_form = ['Foo Bar', 'foo@bar.com', '12345']
        self.assertTrue(is_valid_form(test_form))
    
    def test_is_valid_form_false(self):
        test_form = ['', 'foo@bar.com', '12345']
        self.assertFalse(is_valid_form(test_form))
    
    def test_is_valid_form_empty_list(self):
        test_form = []
        self.assertTrue(is_valid_form(test_form))

class CheckoutViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="Test User")
        cls.user.set_password("testpassword")
        cls.user.save()
        cls.item = Item.objects.create(
            title="Test Item",
            price=float(2),
            discount_price=float(1),
            category="S",
            label="S",
            slug="test-item",
            description="Test item",
            image=None
        )
        cls.shipping_address = Address.objects.create(
            user=cls.user,
            street_address="123 Main St",
            apartment_address="Apt 1",
            country="US",
            zip="12345",
            address_type="S"
        )
        cls.billing_address = Address.objects.create(
            user=cls.user,
            street_address="123 Main St",
            apartment_address="Apt 1",
            country="US",
            zip="12345",
            address_type="B"
        )
        cls.order = Order.objects.create(
            user=cls.user,
            ordered=False,
            ordered_date= datetime.now(timezone.utc)
        )
        cls.order_item = OrderItem.objects.create(
            item=cls.item,
            user=cls.user,
            quantity=2
        )
        cls.order.items.add(cls.order_item)
        cls.order.save()
        cls.url = reverse('core:checkout')
        cls.valid_address_data = {
            'shipping_address': '123 Main St',
            'shipping_zip': '12345',
            'shipping_country': 'US',
        }

    def setUp(self):
        """Runs before each test method"""
        self.client = Client()
        self.client.login(username="Test User", password="testpassword")

    def test_get_checkout_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'checkout.html')
        self.assertEqual(response.context['order'], self.order)
    
    def test_get_checkout_view_shipping_address_default(self):
        self.shipping_address.default = True
        self.shipping_address.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['default_shipping_address'], self.shipping_address)
    
    def test_get_checkout_view_shipping_address_not_default(self):
        self.shipping_address.default = False
        self.shipping_address.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('default_shipping_address'))
        
    def test_get_checkout_view_billing_address_default(self):
        self.billing_address.default = True
        self.billing_address.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['default_billing_address'], self.billing_address)
    
    def test_get_checkout_view_billing_address_not_default(self):
        self.billing_address.default = False
        self.billing_address.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('default_billing_address'))
    
    def test_get_checkout_view_no_active_order(self):
        self.order.ordered = True
        self.order.save()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('core:checkout'), fetch_redirect_response=False)
        
    def test_get_checkout_view_both_addresses_default(self):
        self.shipping_address.default = True
        self.shipping_address.save()
        self.billing_address.default = True
        self.billing_address.save()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'checkout.html')
        self.assertEqual(response.context['default_shipping_address'], self.shipping_address)
        self.assertEqual(response.context['default_billing_address'], self.billing_address)
        self.assertEqual(response.context['order'], self.order)
    
    def test_post_checkout_view_no_active_order(self):
        self.order.ordered = True
        self.order.save()
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('core:order-summary'), fetch_redirect_response=False)
    
    def test_post_checkout_view_invalid_form(self):
        with self.assertRaises(ValueError) as context:
            self.client.post(self.url, {
                'invalid-form-field': 'value',
            })
        
        self.assertIn("didn't return an HttpResponse", str(context.exception))
    
    # MC/DC Test Case 1: Default shipping exists + Same billing + Stripe
    def test_mcdc_default_shipping_same_billing_stripe(self):
        self.shipping_address.default = True
        self.shipping_address.save()
        response = self.client.post(self.url, {
            'payment_option': 'S',
            'use_default_shipping': True,
            'same_billing_address': True,
        })
        self.assertRedirects(response, reverse('core:payment', kwargs={'payment_option': 'stripe'}))

    # MC/DC Test Case 2: Default shipping NOT exists + Same billing
    def test_mcdc_default_shipping_not_exists_same_billing(self):
        # No default shipping address exists
        response = self.client.post(self.url, {
            'payment_option': 'S',
            'use_default_shipping': True,
            'same_billing_address': True,
        })
        self.assertRedirects(response, reverse('core:checkout'), fetch_redirect_response=False)

    # MC/DC Test Case 3+4: New shipping (valid form, set default) + Same billing + PayPal > Set default T/F does not affect the outcome, as long as the shipping address is valid
    def test_mcdc_new_shipping_set_default_same_billing_paypal(self):
        form_data = self.valid_address_data.copy()
        form_data.update({
            'payment_option': 'P',
            'use_default_shipping': False,
            'set_default_shipping': True,
            'same_billing_address': True,
        })
        response = self.client.post(self.url, form_data)
        self.assertRedirects(response, reverse('core:payment', kwargs={'payment_option': 'paypal'}))

    # MC/DC Test Case 5: Invalid shipping + Same billing => FOUND BUG
    def test_mcdc_invalid_shipping_same_billing(self):
        invalid_form_data = {
            'payment_option': 'S',
            'use_default_shipping': False,
            'shipping_address': '',
            'shipping_country': '',
            'shipping_zip': '',
            'same_billing_address': True,
        }
        with self.assertRaises(UnboundLocalError) as context:
            response = self.client.post(self.url, invalid_form_data)
            # Expected behavior: Redirect to checkout page with error message
            self.assertRedirects(response, reverse('core:checkout'), fetch_redirect_response=False)
            
        self.assertIn('shipping_address', str(context.exception))
        
    # MC/DC Test Case 6: Default shipping + Default billing
    def test_mcdc_default_shipping_default_billing_exists(self):
        self.shipping_address.default = True
        self.shipping_address.save()
        self.billing_address.default = True
        self.billing_address.save()
        response = self.client.post(self.url, {
            'payment_option': 'S',
            'use_default_shipping': True,
            'use_default_billing': True,
        })
        self.assertRedirects(response, reverse('core:payment', kwargs={'payment_option': 'stripe'}))
    
    # MC/DC Test Case 7: Default shipping + No default billing
    def test_mcdc_default_shipping_default_billing_not_exists(self):
        self.shipping_address.default = True
        self.shipping_address.save()
        self.billing_address.default = False
        self.billing_address.save()
        response = self.client.post(self.url, {
            'payment_option': 'S',
            'use_default_shipping': True,
            'use_default_billing': True,
        })
        self.assertRedirects(response, reverse('core:checkout'), fetch_redirect_response=False)

    # MC/DC Test Case 8: New shipping + Default billing
    def test_mcdc_valid_new_shipping_default_billing_exists(self):
        self.billing_address.default = True
        self.billing_address.save()
        form_data = self.valid_address_data.copy()
        form_data.update({
            'payment_option': 'S',
            'use_default_shipping': False,
            'set_default_shipping': False,
            'use_default_billing': True,
        })
        response = self.client.post(self.url, form_data)
        self.assertRedirects(response, reverse('core:payment', kwargs={'payment_option': 'stripe'}))
    
    # MC/DC Test Case 9: New shipping + Default billing not exists
    def test_mcdc_new_shipping_default_billing_not_exists(self):
        self.billing_address.default = False
        self.billing_address.save()
        form_data = self.valid_address_data.copy()
        form_data.update({
            'payment_option': 'S',
            'use_default_shipping': False,
            'set_default_shipping': False,
            'use_default_billing': True,
            'same_billing_address': False,
        })
        response = self.client.post(self.url, form_data)
        self.assertRedirects(response, reverse('core:checkout'), fetch_redirect_response=False)
    
    # MC/DC Test Case 10: Invalid shipping + Default billing
    def test_mcdc_invalid_shipping_default_billing(self):
        self.billing_address.default = True
        self.billing_address.save()
        form_data = {
            'payment_option': 'S',
            'use_default_shipping': False,
            'shipping_address': '',
            'shipping_country': '',
            'shipping_zip': '',
            'use_default_billing': True,
        }
        response = self.client.post(self.url, form_data)
        # Expected behavior: Due to missing required shipping address, 
        # it will redirect to checkout page with an error message
        self.assertRedirects(response, reverse('core:checkout'), fetch_redirect_response=False)
    
    # MC/DC Test Case 11 & 12: Default shipping + New billing + Set default billing (T/F) results in the same behavior
    def test_mcdc_default_shipping_new_billing_set_default(self):
        self.shipping_address.default = True
        self.shipping_address.save()
        self.billing_address.default = True
        self.billing_address.save()
        form_data = {
            'payment_option': 'S',
            'use_default_shipping': True,
            'set_default_billing': True,
            'billing_address': '123 Main St',
            'billing_country': 'US',
            'billing_zip': '12345',
        }
        response = self.client.post(self.url, form_data)
        self.assertRedirects(response, reverse('core:payment', kwargs={'payment_option': 'stripe'}))
    
    # MC/DC Test Case 13: Default shipping + New invalid billing
    def test_mcdc_default_shipping_invalid_billing(self):
        self.shipping_address.default = True
        self.shipping_address.save()
        self.billing_address.default = False
        self.billing_address.save()
        form_data = {
            'same_billing_address': False,
            'use_default_shipping': True,
            'payment_option': 'S',
            'billing_address': '',
            'billing_country': '',
            'billing_zip': '',
        }
        response = self.client.post(self.url, form_data)
        # Expected behavior: Due to missing required shipping address, 
        # it will redirect to checkout page with an error message
        self.assertRedirects(response, reverse('core:checkout'), fetch_redirect_response=False)
        
    # MC/DC Test Case 14 & 15: New shipping + New billing + Set default billing (T/F) results in the same behavior
    def test_mcdc_new_shipping_new_billing_set_default(self):
        form_data = self.valid_address_data.copy()
        form_data.update({
            'payment_option': 'S',
            'billing_address': '123 Main St',
            'billing_country': 'US',
            'billing_zip': '12345',
        })
        response = self.client.post(self.url, form_data)
        self.assertRedirects(response, reverse('core:payment', kwargs={'payment_option': 'stripe'}))

    # MC/DC Test Case 16: Invalid payment option
    def test_mcdc_invalid_payment_option(self):
        form_data = self.valid_address_data.copy()
        form_data.update({
            'same_billing_address': True,
            'payment_option': 'X',
        })
        # Expect invalid form response with Not an HttpRespons. The src code have unreachable condition
        with self.assertRaises(ValueError) as context:
            self.client.post(self.url, form_data)
        
        self.assertIn("didn't return an HttpResponse", str(context.exception))


class StripeCreateCalled(Exception):
    pass


class StripeRetrieveCalled(Exception):
    pass


class StripeChargeCalled(Exception):
    pass


class StripeListSourcesCalled(Exception):
    pass


class MockCustomer():
    def __init__(self):
        self.sources = MockStripeCustomerSources()

    def __getitem__(self, i):
        return 1


class MockStripeCustomerSources():
    def create(self, source):
        pass

    def __getitem__(self):
        return 1


class PaymentViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="Test User")
        self.user.set_password("testpassword")
        self.user.save()
        self.item = Item.objects.create(title="Test Item",
                                       price=float(5),
                                       category='S',
                                       label='P',
                                       slug='test-item',
                                       description="Test item",
                                       image=None)
        self.billing_address = Address.objects.create(user=self.user,
                                                     street_address="Test street",
                                                     apartment_address="1",
                                                     country="US",
                                                     zip="00000",
                                                     address_type='B')
        self.url = reverse('core:payment', kwargs={"payment_option": "any"})
        self.valid_post_form_data = {'stripeToken': 'valid-stripe-token',
                                     'save': True,
                                     'use_default': True}
        self.client = Client()
        self.client.login(username="Test User", password="testpassword")

    def test_get_mcdc_anonymous_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/accounts/login/?next=/payment/any')

    def test_get_mcdc_no_active_order(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, '/')

    def test_get_mcdc_no_billing_address(self):
        Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc))
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('core:checkout'))
        self.assertEqual(str(list(get_messages(response.wsgi_request))[0]),
                         "You have not added a billing address")

    def test_get_mcdc_no_oneclick_purchasing(self):
        order = Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc),
                             billing_address=self.billing_address)
        order_item = OrderItem.objects.create(user=self.user,
                                              ordered=False,
                                              item=self.item,
                                              quantity=1)
        order.items.add(order_item)
        order.save()
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.one_click_purchasing = False
        user_profile.save()
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "payment.html")
        self.assertNotIn('card', response.context)

    @patch('stripe.Customer.list_sources',
            return_value={'data': [{'last4': '1234',
                                     'exp_month': '12',
                                     'exp_year': '25'}]})
    def test_get_mcdc_card_list_not_empty(self, mock_list_sources):
        Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc),
                             billing_address=self.billing_address)
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.one_click_purchasing = True
        user_profile.save()
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "payment.html")
        self.assertIn('card', response.context)
        self.assertContains(response, '1234')

    @patch('stripe.Customer.list_sources', return_value={'data': []})
    def test_get_mcdc_card_list_empty(self, mock_list_sources):
        Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc),
                             billing_address=self.billing_address)
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.one_click_purchasing = True
        user_profile.save()
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "payment.html")
        self.assertNotIn('card', response.context)
        self.assertNotContains(response, '1234')

    def test_post_mcdc_anonymous_user(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertRedirects(response, '/accounts/login/?next=/payment/any')

    def test_post_mcdc_no_active_order(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, '/')

    @patch('stripe.Customer.create', return_value=None)
    @patch('stripe.Customer.retrieve', return_value=None)
    @patch('stripe.Charge.create', return_value=None)
    def test_post_mcdc_form_not_valid(self, mock_create, mock_retrieve, mock_charge):
        Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc),
                             billing_address=self.billing_address)
        form_data = None
        response = self.client.post(self.url, form_data, fetch_redirect_response=False)
        self.assertRedirects(response,
                             reverse("core:payment", kwargs={'payment_option': 'any'}),
                             fetch_redirect_response=False)
        self.assertEqual(str(list(get_messages(response.wsgi_request))[0]),
                         "Invalid data received")

    @patch('stripe.Customer.retrieve',
           side_effect=stripe_error.StripeError("Unexpected Stripe error while retrieving customer"))
    def test_post_mcdc_save_customer_retrieve_stripe_error(self, mock_retrieve):
        Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc),
                             billing_address=self.billing_address)
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.stripe_customer_id = 'valid-stripe-customer-id'
        user_profile.save()
        response = self.client.post(self.url, self.valid_post_form_data)
        self.assertRedirects(response, reverse("core:payment", kwargs={'payment_option': 'any'}))

    @patch('stripe.Customer.create',
           side_effect=stripe_error.StripeError("Unexpected Stripe error while creating customer"))
    def test_post_mcdc_save_customer_create_stripe_error(self, mock_create):
        Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc),
                             billing_address=self.billing_address)
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.stripe_customer_id = ''
        user_profile.save()
        response = self.client.post(self.url, self.valid_post_form_data)
        self.assertRedirects(response, reverse("core:payment", kwargs={'payment_option': 'any'}))

    @patch('stripe.Customer.create', return_value=None, side_effect=StripeCreateCalled)
    def test_post_mcdc_save_stripe_customer_id_is_blank(self, mock_create):
        Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc),
                             billing_address=self.billing_address)
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.stripe_customer_id = ''
        user_profile.save()

        with self.assertRaises(StripeCreateCalled):
            self.client.post(self.url, self.valid_post_form_data)

    @patch('stripe.Customer.create', return_value=None, side_effect=StripeCreateCalled)
    def test_post_mcdc_save_stripe_customer_id_is_none(self, mock_create):
        Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc),
                             billing_address=self.billing_address)
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.stripe_customer_id = None
        user_profile.save()

        with self.assertRaises(StripeCreateCalled):
            self.client.post(self.url, self.valid_post_form_data)

    @patch('stripe.Customer.create', return_value=MockCustomer())
    @patch('stripe.Charge.create', return_value={'id': 'charge-id'})
    def test_post_mcdc_save_customer_create_success(self, mock_create, mock_charge):
        order_item = OrderItem.objects.create(user=self.user, ordered=False, item=self.item, quantity=1)
        order = Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc),
                             billing_address=self.billing_address)
        order.items.set([order_item])
        order.save()
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.stripe_customer_id = None
        user_profile.save()

        self.assertEqual(Payment.objects.count(), 0)
        response = self.client.post(self.url, self.valid_post_form_data, fetch_redirect_response=False)
        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.assertEqual(str(list(get_messages(response.wsgi_request))[0]),
                         "Your order was successful!")
        self.assertEqual(Payment.objects.count(), 1)

    @patch('stripe.Customer.retrieve', return_value=Mock(sources=MockStripeCustomerSources()))
    @patch('stripe.Charge.create', return_value={'id': 'charge-id'})
    def test_post_mcdc_save_customer_retrieve_success_charge_create_success(self, mock_retrieve, mock_charge):
        Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc),
                             billing_address=self.billing_address)
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.stripe_customer_id = 'valid-stripe-customer-id'
        user_profile.save()

        self.assertEqual(Payment.objects.count(), 0)
        response = self.client.post(self.url, self.valid_post_form_data, fetch_redirect_response=False)
        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.assertEqual(str(list(get_messages(response.wsgi_request))[0]),
                         "Your order was successful!")
        self.assertEqual(Payment.objects.count(), 1)

    @patch('stripe.Customer.retrieve', return_value=Mock(sources=MockStripeCustomerSources()))
    @patch('stripe.Charge.create', return_value=None, side_effect=stripe_error.StripeError)
    def test_post_mcdc_save_charge_create_stripe_error(self, mock_retrieve, mock_charge):
        Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc),
                             billing_address=self.billing_address)
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.stripe_customer_id = 'valid-stripe-customer-id'
        user_profile.save()

        self.assertEqual(Payment.objects.count(), 0)
        response = self.client.post(self.url, self.valid_post_form_data, fetch_redirect_response=False)
        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.assertEqual(str(list(get_messages(response.wsgi_request))[0]),
                         "Something went wrong. You were not charged. Please try again.")
        self.assertEqual(Payment.objects.count(), 0)

    @patch('stripe.Customer.retrieve', return_value=Mock(sources=MockStripeCustomerSources()))
    @patch('stripe.Charge.create',
           return_value=None,
           side_effect=stripe_error.APIConnectionError(message="Mocked APIConnectionError"))
    def test_post_mcdc_save_charge_create_api_connection_error(self, mock_retrieve, mock_charge):
        Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc),
                             billing_address=self.billing_address)
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.stripe_customer_id = 'valid-stripe-customer-id'
        user_profile.save()

        self.assertEqual(Payment.objects.count(), 0)
        response = self.client.post(self.url, self.valid_post_form_data, fetch_redirect_response=False)
        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.assertEqual(str(list(get_messages(response.wsgi_request))[0]),
                         "Network error")
        self.assertEqual(Payment.objects.count(), 0)

    @patch('stripe.Customer.retrieve', return_value=Mock(sources=MockStripeCustomerSources()))
    @patch('stripe.Charge.create', return_value=None, side_effect=stripe_error.AuthenticationError)
    def test_post_mcdc_save_charge_create_authentication_error(self, mock_retrieve, mock_charge):
        Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc),
                             billing_address=self.billing_address)
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.stripe_customer_id = 'valid-stripe-customer-id'
        user_profile.save()

        self.assertEqual(Payment.objects.count(), 0)
        response = self.client.post(self.url, self.valid_post_form_data, fetch_redirect_response=False)
        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.assertEqual(str(list(get_messages(response.wsgi_request))[0]),
                         "Not authenticated")
        self.assertEqual(Payment.objects.count(), 0)

    @patch('stripe.Customer.retrieve', return_value=Mock(sources=MockStripeCustomerSources()))
    @patch('stripe.Charge.create',
           return_value=None,
           side_effect=stripe_error.InvalidRequestError(message="Mocked InvalidRequestError",
                                                        param="PARAM"))
    def test_post_mcdc_save_charge_create_invalid_request_error(self, mock_retrieve, mock_charge):
        Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc),
                             billing_address=self.billing_address)
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.stripe_customer_id = 'valid-stripe-customer-id'
        user_profile.save()

        self.assertEqual(Payment.objects.count(), 0)
        response = self.client.post(self.url, self.valid_post_form_data, fetch_redirect_response=False)
        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.assertEqual(str(list(get_messages(response.wsgi_request))[0]),
                         "Invalid parameters")
        self.assertEqual(Payment.objects.count(), 0)

    @patch('stripe.Customer.retrieve', return_value=Mock(sources=MockStripeCustomerSources()))
    @patch('stripe.Charge.create', return_value=None, side_effect=stripe_error.RateLimitError)
    def test_post_mcdc_save_charge_create_rate_limit_error(self, mock_retrieve, mock_charge):
        Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc),
                             billing_address=self.billing_address)
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.stripe_customer_id = 'valid-stripe-customer-id'
        user_profile.save()

        self.assertEqual(Payment.objects.count(), 0)
        response = self.client.post(self.url, self.valid_post_form_data, fetch_redirect_response=False)
        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.assertEqual(str(list(get_messages(response.wsgi_request))[0]),
                         "Rate limit error")
        self.assertEqual(Payment.objects.count(), 0)

    @patch('stripe.Customer.retrieve', return_value=Mock(sources=MockStripeCustomerSources()))
    @patch('stripe.Charge.create',
           return_value=None,
           side_effect=stripe_error.CardError(message="MESSAGE",
                                              param="PARAM",
                                              code="CODE",
                                              json_body={'error': {
                                                  'message': 'Mocked card error'
                                              }}))
    def test_post_mcdc_save_charge_create_card_error(self, mock_retrieve, mock_charge):
        Order.objects.create(user=self.user,
                             ordered=False,
                             ordered_date=datetime.now(timezone.utc),
                             billing_address=self.billing_address)
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.stripe_customer_id = 'valid-stripe-customer-id'
        user_profile.save()

        self.assertEqual(Payment.objects.count(), 0)
        response = self.client.post(self.url, self.valid_post_form_data, fetch_redirect_response=False)
        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.assertEqual(str(list(get_messages(response.wsgi_request))[0]),
                         "Mocked card error")
        self.assertEqual(Payment.objects.count(), 0)


class RequestRefundViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="testuser", email="testuser@example.com")
        cls.user.set_password("testpassword")
        cls.user.save()

    def setUp(self):
        self.order = Order.objects.create(user=self.user,
                                          ordered_date=datetime.now(timezone.utc),
                                          ordered=True,
                                          ref_code='order-ref')
        self.client = Client()
        self.assertTrue(self.client.login(username="testuser", password="testpassword"))

    def test_request_refund_success(self):
        self.assertFalse(self.order.refund_requested)
        response = self.client.post('/request-refund/',
                                    {
                                        'ref_code': 'order-ref',
                                        'message': 'Valid message.',
                                        'email': 'testuser@example.com'
                                    })

        self.assertRedirects(response, reverse('core:request-refund'))
        self.assertEquals(str(list(get_messages(response.wsgi_request))[0]),
                          "Your request was received.")

        self.order.refresh_from_db()
        self.assertTrue(self.order.refund_requested)

        self.assertEqual(Refund.objects.count(), 1)
        refund = Refund.objects.first()
        self.assertEqual(refund.order, self.order)
        self.assertEqual(refund.reason, "Valid message.")
        self.assertEqual(refund.email, "testuser@example.com")

    def test_request_refund_order_does_not_exist(self):
        self.assertFalse(self.order.refund_requested)
        response = self.client.post('/request-refund/',
                                    {
                                        'ref_code': 'nonexisent-ref-code',
                                        'message': 'Valid message.',
                                        'email': 'testuser@example.com'
                                    })

        self.assertRedirects(response, reverse('core:request-refund'))
        self.assertEquals(str(list(get_messages(response.wsgi_request))[0]),
                          "This order does not exist.")

        self.order.refresh_from_db()
        self.assertFalse(self.order.refund_requested)

        self.assertEqual(Refund.objects.count(), 0)

    def test_request_refund_wrong_email_creates_refund(self):
        self.assertFalse(self.order.refund_requested)
        self.assertEqual(self.order.user.email, 'testuser@example.com')

        self.assertFalse(self.order.refund_requested)
        response = self.client.post('/request-refund/',
                                    {'ref_code': 'order-ref',
                                     'message': 'Valid message.',
                                     'email': 'wrong-user@example.com'})

        self.assertRedirects(response, reverse('core:request-refund'))
        self.assertEquals(str(list(get_messages(response.wsgi_request))[0]),
                          "Your request was received.")

        self.order.refresh_from_db()
        self.assertTrue(self.order.refund_requested)

        self.assertEqual(Refund.objects.count(), 1)
        refund = Refund.objects.first()
        self.assertEqual(refund.order, self.order)
        self.assertEqual(refund.reason, "Valid message.")
        self.assertEqual(refund.email, "wrong-user@example.com")

    def test_request_refund_invalid_form(self):
        response = self.client.post('/request-refund/',
                                    {'ref_code': 'order-ref',
                                    'message': '',
                                    'email': 'testuser@example.com'})
        self.assertRedirects(response, reverse('core:request-refund'))

class OrderSummaryViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.user.set_password("testpassword")
        self.user.save()
        self.client = Client()

    def test_get_summary_success(self):
        self.order = Order.objects.create(user=self.user,
                                          ordered_date=datetime.now(timezone.utc),
                                          ordered=False)
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get("/order-summary/", follow=True)
        self.assertTemplateUsed(response, 'order_summary.html')

    def test_get_summary_no_active_order(self):
        self.order = Order.objects.create(user=self.user,
                                          ordered_date=datetime.now(timezone.utc),
                                          ordered=True)
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get("/order-summary/", follow=True)
        self.assertRedirects(response, '/')
        self.assertEquals(str(list(get_messages(response.wsgi_request))[0]),
                          "You do not have an active order")

    def test_get_summary_user_not_logged_in(self):
        response = self.client.get("/order-summary/", follow=True)
        self.assertRedirects(response, '/accounts/login/?next=/order-summary/')
