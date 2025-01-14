from rest_framework.viewsets import ReadOnlyModelViewSet, GenericViewSet, ModelViewSet
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser

from .serializers import (
    BatchSerializer,
    BuyerSerializer,
    CartItemSerializer, CartItemUpdateSerializer, CartSerializer,
    FetchBuyerSerializer,
    OrderFinalizeSerializer,
    OrderInitSerializer,
    OrderSerializer,
    ProductDetailSerializer, ProductListSerializer
)
from .models import Batch, Buyer, Cart, CartItem, Order, Product

# Create your views here.

class BatchViewSet(ReadOnlyModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer


class BuyerViewSet(
    GenericViewSet
):

    queryset = Buyer.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):

        if self.action == 'search':
            return FetchBuyerSerializer


    @action(methods=['POST'], detail=False)
    def search(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                "detail": "email is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            buyer = Buyer.objects.get(email = email)
        except Buyer.DoesNotExist:
            return Response({
                "detail": "Not found."
            }, status=status.HTTP_204_NO_CONTENT)

        serializer = BuyerSerializer(buyer)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductViewSet(ReadOnlyModelViewSet):

    def get_queryset(self):
        return Product.objects.filter(batch_id = self.kwargs['batch_pk'])

    def get_serializer_class(self):
        action = self.action

        if action == "list":
            return ProductListSerializer
        elif action == "add_to_cart":
            return CartItemSerializer
        return ProductDetailSerializer

    @action(methods=['POST'], detail=True)
    def add_to_cart(self, request, batch_pk=None, pk=None):
        if self.request.method == 'POST':
            if "cart_id" in request.data.keys():
                cart = Cart.objects.get(id = request.data['cart_id'])
            else:
                cart = Cart.objects.create()

            try:

                serializer = CartItemSerializer(
                    data = request.data,
                    context = {
                        'cart_id': cart.id,
                        'product_id': pk,
                    }
                )
                serializer.is_valid()
                serializer.save()

                return Response({
                    "cart_id": cart.id
                }, status=status.HTTP_200_OK)

            except Exception as err:
                print(err)
                return Response({
                    'detail': 'Internal Server Error.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartViewSet(ModelViewSet):
    queryset = Cart.objects.all()

    def get_serializer_class(self):
        if self.action == 'initiate_order':
            return OrderInitSerializer

        return CartSerializer

    @action(methods=['POST'], detail=True)
    def initiate_order(self, request, pk=None):

        serializer = OrderInitSerializer(
            data={}, context = {
                "cart_id": self.kwargs['pk']
            }
        )

        print(self.kwargs['pk'])

        try:
            serializer.is_valid()
            order = serializer.save()
            serializer = OrderSerializer(order)

        except Exception as error:
            print(error)
            return Response({
                "detail": "Internal Server Error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.data, status=status.HTTP_200_OK)

class CartItemViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet
):

    def get_queryset(self):
        return CartItem.objects.filter(cart_id=self.kwargs['cart_pk'])

    def get_serializer_class(self):
        method = self.request.method

        if method in ("PATCH", "PUT"):
            return CartItemUpdateSerializer
        return CartItemSerializer

    def get_serializer_context(self):

        return {
            'cart_id': self.kwargs['cart_pk'],
        }


class OrderViewSet(
        RetrieveModelMixin,
        GenericViewSet
    ):

    def get_queryset(self, pk=None):
        order_id = self.kwargs.get('pk')

        if order_id:
            return Order.objects.filter(id = order_id)
        return []


    def get_serializer_class(self):

        if self.request.method in ('POST'):
            return OrderFinalizeSerializer
        return OrderSerializer


    @action(methods=['POST'], detail=True)
    def finalize_order(self, request, pk=None):
        serializer = OrderFinalizeSerializer(
            data=request.data, context={
                "order_id": self.kwargs['pk']
            })

        try:
            serializer.is_valid(raise_exception=True)
            order = serializer.save()

            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as error:
            print(error)
            return Response({
                "detail": "Internal Server Error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
