from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from .views import BatchViewSet, BuyerViewSet, CartItemViewSet, OrderViewSet, ProductViewSet, CartViewSet

router = DefaultRouter()
router.register('batches', BatchViewSet)
router.register('cart', CartViewSet)
router.register('orders', OrderViewSet, basename='order')
router.register('buyers', BuyerViewSet)

batch_router = NestedDefaultRouter(router, 'batches', lookup='batch')
batch_router.register('products', ProductViewSet, basename='products')

cart_router = NestedDefaultRouter(router, 'cart',  lookup='cart')
cart_router.register('items', CartItemViewSet, 'cart-items')

urlpatterns = router.urls + batch_router.urls + cart_router.urls