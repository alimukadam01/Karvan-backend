from django.contrib import admin
from .models import (
    Buyer,
    Address, City,
    Batch, BatchImage,
    Product, ProductImage, ProductReview, ProductSize,
    Cart, CartItem,
    Order, OrderItem, Payment
)

# Register your models here.
admin.site.register(Buyer)
admin.site.register(Address)
admin.site.register(City)

admin.site.register(Batch)
admin.site.register(BatchImage)

admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(ProductSize)
admin.site.register(ProductReview)

admin.site.register(Cart)
admin.site.register(CartItem)

admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
