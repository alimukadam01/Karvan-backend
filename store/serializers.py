from rest_framework import serializers
from .models import (
    Batch, Product,
    Buyer, Address, City,
    Cart, CartItem,
    Order, OrderItem, Payment,
)

class ImageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    date_created = serializers.DateTimeField()
    image = serializers.ImageField()


class CitySerializer(serializers.ModelSerializer):

    class Meta:
        model = City
        fields = ['name', 'shipping_charges']


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


class FetchBuyerSerializer(serializers.Serializer):
    email = serializers.EmailField()


class BatchSerializer(serializers.ModelSerializer):

    images = ImageSerializer(many=True)

    class Meta:
        model = Batch
        fields = ['id', 'title', 'desc', 'images']


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

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'batch' ,'price', 'rating', 'desc', 
            'sizes', 'images', 'is_available'
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
        return  CartItem.objects.create(
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
            'payment', 'items', 'address'
        ]


class OrderInitSerializer(serializers.Serializer):

    def save(self, **kwargs):
        order = Order.objects.create(status='N')
        cart_items = CartItem.objects.filter(cart_id = self.context['cart_id'])
        print(f"Length of cart_items: {len(cart_items)}")

        order_items = [
            OrderItem(
                order_id = order.id,
                product_id = item.product.id,
                quantity = item.quantity,
                size = item.size
            )
        for item in cart_items]
        OrderItem.objects.bulk_create(order_items)

        amount=0.0
        for item in order_items:
            amount+=(item.product.price*item.quantity)

        payment = Payment.objects.create(
            amount = amount,
            status = "P"
        )
        order.payment = payment
        order.save()

        Cart.objects.get(id=self.context['cart_id']).delete()
        return order


class OrderFinalizeSerializer(serializers.Serializer):

    first_name = serializers.CharField(max_length=256)
    last_name = serializers.CharField(max_length=256)
    email = serializers.EmailField(max_length=256)
    phone = serializers.CharField(max_length=256)

    address = serializers.CharField(max_length=256)
    apt_suite = serializers.CharField(max_length=256)
    city = serializers.CharField(max_length=256)
    alt_phone = serializers.CharField(max_length=256)
    postal_code = serializers.CharField(max_length=256)


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
            "city_id": 1,
            "phone": self.validated_data['phone'],
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
            address = Address.objects.create(buyer_id = buyer.id, city_id = 1)

        address.address = address_data["address"]
        address.apt_suite = address_data["apt_suite"]
        address.phone = address_data["phone"]
        address.postal_code = address_data["postal_code"]
        address.save()

        order = Order.objects.get(id = self.context["order_id"])
        order.buyer = buyer
        order.status = "OK"
        order.address = address
        order.payment.status = "S"
        order.save()

        return order
