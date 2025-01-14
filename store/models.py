from django.db import models
from uuid import uuid4
from django.conf import settings

# Create your models here.

class Buyer(models.Model):
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=256)


class City(models.Model):
    name = models.CharField(max_length=256)
    shipping_charges = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}"


class Address(models.Model):
    buyer = models.ForeignKey(Buyer, models.CASCADE, related_name="addresses")
    address = models.TextField()
    apt_suite = models.CharField(max_length=256)
    phone = models.CharField(max_length=256, null=True, blank=True)
    postal_code = models.CharField(max_length=256, null=True, blank=True)
    city = models.ForeignKey(City, models.CASCADE)


class Batch(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=256)
    desc = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.title}"


class BatchImage(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    batch = models.ForeignKey(Batch, models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="batch_images/")

    def __str__(self):
        return f"{self.id}: {self.batch.title}"


class Product(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=256)
    batch = models.ForeignKey(Batch, models.CASCADE, related_name="products")
    price = models.FloatField()
    desc = models.TextField(null=True, blank=True)
    rating = models.FloatField(default=2.5)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name}"


class ProductSize(models.Model):

    SIZE_CHOICES = [
        ("X-Small", "XS"),
        ("Small", "S"),
        ("Medium", "M"),
        ("Large", "L"),
        ("X-Large", "XL"),
        ("XX-Large", "XXL"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sizes")
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default=SIZE_CHOICES[0])
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name}: {self.size} x {self.quantity}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, models.CASCADE, related_name="images")
    date_created = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='product_images/')
    desc = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.id}: {self.product.name}"


class ProductReview(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(Product, models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    rating = models.FloatField(default=0)
    review = models.TextField()

    def __str__(self):
        return f"{self.product.name}: {self.user.email}"


class Cart(models.Model):
    id = models.CharField(max_length=256, default=uuid4, primary_key=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, models.CASCADE)
    size = models.CharField(max_length=256)
    quantity = models.IntegerField()


class Payment(models.Model):

    PAYMENT_STATUSES = [
        ("PENDING", "P"),
        ("SUCCESS", "S"),
        ("DENIED", "D"),
        ("CANCELLED", "C")
    ]

    date_created = models.DateTimeField(auto_now_add=True)
    amount = models.IntegerField()
    status = models.CharField(max_length=256, choices=PAYMENT_STATUSES, default=PAYMENT_STATUSES[0])


class Order(models.Model):

    ORDER_STATUSES = [
        ("NEW_ORDER", "N"),
        ("CONFIRMED", "OK"),
        ("DISPATCHED", "D"),
        ("ON_HOLD", "H"),
        ("COMPLETED", "C"),
        ("CANCELLED", "X")
    ]

    id = models.CharField(max_length=256, default=uuid4, primary_key=True)
    buyer = models.ForeignKey(
        Buyer, models.CASCADE,
        related_name='orders',
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    payment = models.OneToOneField(
        Payment, models.DO_NOTHING,
        null=True, blank=True,
    )
    status = models.CharField(
        max_length=256, choices=ORDER_STATUSES,
        default=ORDER_STATUSES[0], null=True, blank=True
    )
    address = models.ForeignKey(
        Address, on_delete=models.DO_NOTHING, 
        related_name='orders', null=True, blank=True
    )


class OrderItem(models.Model):
    order = models.ForeignKey(Order, models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, models.DO_NOTHING)
    size = models.CharField(max_length=256)
    quantity = models.IntegerField()
