from django.core.mail import send_mail
from django.conf import settings
from django.db.transaction import atomic
from datetime import datetime, timezone, timedelta
from rest_framework import serializers
from .models import (
    Batch, Product,
    Buyer, Address, City,
    Cart, CartItem,
    Order, OrderItem, Payment, ProductReview,
)

class EmailUserSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    message = serializers.CharField()


class ImageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    date_created = serializers.DateTimeField()
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        return f"http://127.0.0.1:8000{obj.image.url}" 


class CitySerializer(serializers.ModelSerializer):

    class Meta:
        model = City
        fields = ['id', 'name', 'shipping_charges']


class AddressSerializer(serializers.ModelSerializer):

    city = CitySerializer()

    class Meta:
        model = Address
        fields = [
            'id', 'address', 'apt_suite', 
            'phone', 'postal_code', 'city'
        ]


class BuyerSerializer(serializers.ModelSerializer):

    addresses = AddressSerializer(read_only=True, many=True)

    class Meta:
        model = Buyer
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'addresses']


class SimpleBuyerSerializer(serializers.ModelSerializer):

    addresses = AddressSerializer(read_only=True, many=True)

    class Meta:
        model = Buyer
        fields = ['id', 'email', 'addresses']


class BasicBuyerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Buyer
        fields = ['id', 'email', 'first_name', 'last_name']


class FetchBuyerSerializer(serializers.Serializer):
    email = serializers.EmailField()


class BatchSerializer(serializers.ModelSerializer):

    images = ImageSerializer(many=True)

    class Meta:
        model = Batch
        fields = ['id', 'batch_no', 'title', 'desc', 'images']


class ProductReviewSerializer(serializers.ModelSerializer):

    buyer = BasicBuyerSerializer(read_only = True)

    class Meta: 
        model = ProductReview
        fields = ['id', 'buyer', 'rating', 'review']


class ProductSizeSerializer(serializers.Serializer):
    size = serializers.CharField()


class ProductListSerializer(serializers.ModelSerializer):

    images = ImageSerializer(many=True)
    sizes = ProductSizeSerializer(many=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'batch', 'price', 'sizes', 'images']


class ProductDetailSerializer(serializers.ModelSerializer):

    images = ImageSerializer(many=True)
    sizes = ProductSizeSerializer(many=True)
    reviews = ProductReviewSerializer(many=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'batch' ,'price', 'rating', 'desc', 
            'sizes', 'images', 'is_available', 'reviews'
        ]


class SimpleProductSerializer(serializers.ModelSerializer):

    images = ImageSerializer(read_only=True, many=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'images'
        ]


class CartItemSerializer(serializers.ModelSerializer):

    id = serializers.CharField(max_length=256, required=False)
    product = SimpleProductSerializer(read_only=True)

    def save(self, **kwargs):
        try:
            cart_item = CartItem.objects.get(
                cart_id = self.validated_data['id'], 
                product_id = self.context['product_id'], 
                size = self.validated_data['size']
            )
            cart_item.quantity += self.validated_data['quantity']
            cart_item.save()
            return cart_item
          
        except CartItem.DoesNotExist:

            return CartItem.objects.create(
                cart_id=self.validated_data['id'],
                product_id = self.context['product_id'],
                quantity = self.validated_data['quantity'],
                size = self.validated_data['size']
            )

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'size']


class CartItemUpdateSerializer(serializers.ModelSerializer):

    def save(self, **kwargs):
        instance = self.instance
        instance.quantity = self.validated_data['quantity']
        instance.save()

        return instance

    class Meta:
        model = CartItem
        fields = ['id', 'quantity']


class CartSerializer(serializers.ModelSerializer):

    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items']


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = [
            'id',
            'amount',
            'status'
        ]


class OrderItemSerializer(serializers.ModelSerializer):

    product = SimpleProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'size', 'quantity',]


class OrderSerializer(serializers.ModelSerializer):

    buyer = SimpleBuyerSerializer()
    items = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer()
    address = AddressSerializer()

    class Meta:
        model = Order
        fields = [
            'id', 'buyer', 'created_at', 'status',
            'payment', 'items', 'address', 'notes'
        ]


class OrderInitSerializer(serializers.Serializer):

    def save(self, cart_items, **kwargs):
        order = Order(status='N')

        order_items = []
        if cart_items:
            order_items = [
                OrderItem(
                    order_id = order.id,
                    product_id = item.product.id,
                    quantity = item.quantity,
                    size = item.size
                )
            for item in cart_items]

        else:
            order_items.append(OrderItem(
                order_id = order.id,
                product_id = self.context["product_id"],
                quantity = self.validated_data["quantity"],
                size = self.validated_data["size"]
            ))


        amount=0.0
        for item in order_items:
            amount+=(item.product.price*item.quantity)

        payment = Payment(
            amount = amount,
            status = "P"
        )

        try:
            with atomic():
                payment.save()
                order.payment = payment
                order.save()
                OrderItem.objects.bulk_create(order_items)
                
        except Exception as error:
            print(error)

        return order


class CartOrderCreateSerializer(OrderInitSerializer):

    def save(self, **kwargs):

        cart_items = CartItem.objects.filter(cart_id = self.context['cart_id'])
        if not cart_items:
            raise Exception("cart_items are needed for this operation")

        order = super().save(cart_items, **kwargs)

        Cart.objects.get(id=self.context['cart_id']).delete()
        return order


class BuyOrderCreateSerializer(OrderInitSerializer):

    size = serializers.CharField(max_length = 10)
    quantity = serializers.IntegerField()

    def save(self, **kwargs):
        return super().save([], **kwargs)


class OrderFinalizeSerializer(serializers.Serializer):

    first_name = serializers.CharField(max_length=256)
    last_name = serializers.CharField(max_length=256)
    email = serializers.EmailField(max_length=256)
    phone = serializers.CharField(max_length=256)

    address = serializers.CharField(max_length=256)
    apt_suite = serializers.CharField(max_length=256)
    city_id = serializers.IntegerField()
    alt_phone = serializers.CharField(max_length=256, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=256)
    notes = serializers.CharField(required=False, allow_blank=True)


    def save(self, **kwargs):

        buyer_data = {
            "first_name": self.validated_data['first_name'],
            "last_name": self.validated_data['last_name'],
            "email": self.validated_data['email'],
            "phone": self.validated_data['phone'],
        }

        address_data = {
            "address": self.validated_data['address'],
            "apt_suite": self.validated_data['apt_suite'],
            "city": City.objects.get(id=self.validated_data["city_id"]),
            "phone": self.validated_data['alt_phone'],
            "postal_code": self.validated_data['postal_code']
        }

        try:
            buyer = Buyer.objects.get(email=buyer_data["email"])

        except Buyer.DoesNotExist:
            buyer = Buyer.objects.create(**buyer_data)

        try:
            address = Address.objects.get(
                buyer_id = buyer.id,
            )
        except Address.DoesNotExist:
            address = Address.objects.create(buyer_id = buyer.id, city=address_data["city"])

        address.address = address_data["address"]
        address.apt_suite = address_data["apt_suite"]
        address.city = address_data["city"]
        address.phone = address_data["phone"]
        address.postal_code = address_data["postal_code"]

        order = Order.objects.get(id = self.context["order_id"])
        order.buyer = buyer
        order.address = address
        order.payment.shipping_charges =  address_data['city'].shipping_charges
        order.payment.status = "S"
        if self.validated_data.get("notes"):
            order.notes = self.validated_data["notes"]
        
        order.status = "OK"

        try:
            with atomic(): 
                address.save()
                order.payment.save()
                order.save()
        except Exception as error:
            print("Error saving order details: ", error)
  
        order_items = order.items.all()
        num_items = 0

        for item in order_items:
            num_items += item.quantity

        send_mail(
            'Your Order with Karvan Has Been Finalized!',
            f"""
            Dear {buyer_data['first_name']},

            We're excited to let you know that your order #{order.id} has been successfully finalized! 🚀

            Order Details:
            Order Number: {order.id}
            Items Ordered: {num_items}
            Total Amount: PKR {order.payment.amount + address_data['city'].shipping_charges}
            Payment Method: Cash On Delivery
            Estimated Delivery: {(datetime.now(timezone(timedelta(hours=5))).date() + timedelta(days=5)).strftime("%d-%m-%Y")}
            You'll receive another email with tracking details once your order is shipped. 
            If you have any questions or need assistance, feel free to reach out to us at support@karvan.pk.

            Thank you for choosing Karvan! We appreciate your support. 💙

            Best regards,
            The Karvan Team
            shopkarvan.pk
            """,
            settings.ORDER_CONFIRM_EMAIL,
            [buyer_data['email']],
            True
        )

        return order
