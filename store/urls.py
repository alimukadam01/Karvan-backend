from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from .views import BatchViewSet, BuyerViewSet, CartItemViewSet, CityViewSet, OrderViewSet, ProductViewSet, CartViewSet, email_user

router = DefaultRouter()
router.register('batches', BatchViewSet)
router.register('cart', CartViewSet)
router.register('orders', OrderViewSet, basename='order')
router.register('buyers', BuyerViewSet)
router.register('cities', CityViewSet)

batch_router = NestedDefaultRouter(router, 'batches', lookup='batch')
batch_router.register('products', ProductViewSet, basename='products')

cart_router = NestedDefaultRouter(router, 'cart',  lookup='cart')
cart_router.register('items', CartItemViewSet, 'cart-items')

urlpatterns = [
    path('email-user/', email_user, name="email-user")
] + router.urls + batch_router.urls + cart_router.urls