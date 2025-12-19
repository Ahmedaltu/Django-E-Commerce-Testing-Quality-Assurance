from django.test import TestCase
from core.models import Item, OrderItem, Order, Coupon, UserProfile, Address, Payment, Refund
from django.contrib.auth.models import User
from datetime import datetime, timezone

class UserProfileTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="Test User")

    def test_user_profile_str(self):
        user_profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(str(user_profile), "Test User")

class ItemTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.item = Item.objects.create(title="Test Item",
                        price=float(2),
                        discount_price=float(1),
                        category="S",
                        label="S",
                        slug="test-item",
                        description="Test item",
                        image=None)
        cls.item.save()

    def test_item_str(self):
        self.assertEqual(str(self.item), self.item.title)

    def test_get_absolute_url(self):
        self.assertEqual(self.item.get_absolute_url(), "/product/test-item/")
        
    def test_get_add_to_cart_url(self):
        self.assertEqual(self.item.get_add_to_cart_url(), "/add-to-cart/test-item/")

    def test_get_remove_from_cart_url(self):
        self.assertEqual(self.item.get_remove_from_cart_url(), "/remove-from-cart/test-item/")
        
class OrderItemTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="Test User")
        cls.item = Item(title="Test Item",
                        price=float(2),
                        discount_price=float(1),
                        category="S",
                        label="S",
                        slug="test-item",
                        description="Test item",
                        image=None)
        cls.item.save()

    def test_order_item_str(self):
        order_item = OrderItem.objects.create(item=self.item, user=self.user, quantity=1)
        self.assertEqual(str(order_item), "1 of Test Item")

    def test_total_item_price_floating_point_accuracy(self):
        self.item.price = float(99.99)
        self.item.discount_price = float(89.99)
        self.item.save()
        order_item = OrderItem.objects.create(item=self.item, user=self.user, quantity=3)
        self.assertEqual(order_item.get_total_item_price(), float(299.97))

    def test_total_discount_item_price_floating_point_accuracy(self):
        self.item.price = float(99.99)
        self.item.discount_price = float(89.99)
        self.item.save()
        order_item = OrderItem.objects.create(item=self.item, user=self.user, quantity=3)
        self.assertEqual(order_item.get_total_discount_item_price(), float(269.97))

    def test_get_amount_saved_floating_point_accuracy(self):
        self.item.price = float(99.99)
        self.item.discount_price = float(89.99)
        self.item.save()
        order_item = OrderItem.objects.create(item=self.item, user=self.user, quantity=3)
        self.assertEqual(order_item.get_amount_saved(), float(299.97) - float(269.97))

    def test_get_final_price_discount(self):
        self.item.price = float(2)
        self.item.discount_price = float(1)
        self.item.save()
        order_item = OrderItem.objects.create(item=self.item, user=self.user, quantity=2)
        self.assertEqual(order_item.get_final_price(), float(2))

    def test_get_final_price_no_discount(self):
        self.item.price = float(2)
        self.item.discount_price = None
        self.item.save()
        order_item = OrderItem.objects.create(item=self.item, user=self.user, quantity=2)
        self.assertEqual(order_item.get_final_price(), float(4))

    def test_get_final_price_zero_discount_price(self):
        self.item.price = float(2)
        self.item.discount_price = float(0)
        self.item.save()
        order_item = OrderItem.objects.create(item=self.item, user=self.user, quantity=2)
        self.assertEqual(order_item.get_final_price(), float(4))


class OrderTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="Test User")
        self.item = Item(title="Test Item",
                        price=float(2),
                        discount_price=float(1),
                        category="S",
                        label="S",
                        slug="test-item",
                        description="Test item",
                        image=None)
        self.item.save()
        self.order_item = OrderItem.objects.create(item=self.item, user=self.user, quantity=2)
        self.order = Order.objects.create(user=self.user, ordered_date=datetime.now(timezone.utc))
        self.order.items.add(self.order_item)
        self.order.save()
        self.coupon = Coupon.objects.create(code="testcoupon", amount=float(1))

    def test_order_str(self):
        self.assertEqual(str(self.order), "Test User")

    def test_get_total_no_coupon(self):
        self.item.price = float(5)
        self.item.discount_price = None
        self.item.save()
        self.order_item.quantity = 3
        self.order_item.save()
        self.assertEqual(self.order.get_total(), float(15))

    def test_get_total_with_coupon(self):
        self.item.price = float(5)
        self.item.discount_price = None
        self.item.save()
        self.order_item.quantity = 3
        self.order_item.save()
        self.coupon.amount = float(4)
        self.coupon.save()
        self.order.coupon = self.coupon
        self.order.save()
        self.assertEqual(self.order.get_total(), float(11))

    def test_get_total_with_excessive_coupon(self):
        self.coupon.amount = float(999)
        self.coupon.save()
        self.order.coupon = self.coupon
        self.order.save()
        self.assertEqual(self.order.get_total(), float(0))
        
class AddressTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="Test User")
        cls.address = Address.objects.create(
            user=cls.user, 
            street_address="123 Foo St", 
            apartment_address="Foo Bar",
            country="US", 
            zip="12345", 
            address_type="S", 
            default=True
            )

    def test_address_str(self):
        self.assertEqual(str(self.address), "Test User")

class PaymentTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="Test User")
        cls.payment = Payment.objects.create(user=cls.user, amount=float(1), timestamp=datetime.now(timezone.utc))
        cls.payment.save()

    def test_payment_str(self):
        self.assertEqual(str(self.payment), "Test User")

class CouponTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.coupon = Coupon.objects.create(code="testcoupon", amount=float(1))
        cls.coupon.save()

    def test_coupon_str(self):
        self.assertEqual(str(self.coupon), "testcoupon")


class RefundTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="Test User")
        cls.item = Item(title="Test Item",
                        price=float(2),
                        discount_price=float(1),
                        category="S",
                        label="S",
                        slug="test-item",
                        description="Test item",
                        image=None)
        cls.item.save()
        cls.order_item = OrderItem.objects.create(item=cls.item, user=cls.user, quantity=2)
        cls.order = Order.objects.create(user=cls.user, ordered_date=datetime.now(timezone.utc))
        cls.order.items.add(cls.order_item)
        cls.order.save()
        cls.refund = Refund.objects.create(order=cls.order, reason="Test Reason", email="foo@bar.com")
        cls.refund.save()

    def test_refund_str(self):
        self.assertEqual(str(self.refund), "1")