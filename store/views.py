from django.conf import settings
from django.core.mail import send_mail
from rest_framework.viewsets import ReadOnlyModelViewSet, GenericViewSet, ModelViewSet
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAdminUser

from .models import Batch, Buyer, Cart, CartItem, City, Order, Product
from .serializers import (
    BatchSerializer,
    BuyOrderCreateSerializer,
    BuyerSerializer,
    CartItemSerializer, CartItemUpdateSerializer,
    CartOrderCreateSerializer, CartSerializer,
    CitySerializer,
    EmailUserSerializer,
    FetchBuyerSerializer,
    OrderFinalizeSerializer,
    OrderSerializer,
    ProductDetailSerializer, ProductListSerializer,
    ProductReviewCreateSerializer,
)

# Create your views here.

@api_view(['POST'])
def email_user(request):

    serializer = EmailUserSerializer(data=request.data)

    try:
        if serializer.is_valid(raise_exception=True):

            message = f"Feedback from: {serializer.validated_data['name']} @ {serializer.validated_data['email']}\nMessage: {serializer.validated_data['message']}" 

            send_mail(
                subject="Feedback Form Response",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["admin@shopkarvan.pk"],
                fail_silently=False
            )

            return Response({
                "detail": "OK"
            }, status=status.HTTP_200_OK)
        
        return Response({
            "detail": "Bad Request."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as error:
        print(error)
        return Response({
            "detail": "Internal Server Error."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BatchViewSet(ReadOnlyModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer


class CityViewSet(ReadOnlyModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer


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
        elif action == "buy":
            return BuyOrderCreateSerializer

        return ProductDetailSerializer

    @action(methods=['POST'], detail=True)
    def add_to_cart(self, request, batch_pk=None, pk=None):
        if self.request.method == 'POST':

            try:
                cart = Cart.objects.get(id = request.data['id'])
            except Cart.DoesNotExist:
                return Response({
                    "detail": {
                        "Bad Request"
                    }
                }, status = status.HTTP_400_BAD_REQUEST)

            try:

                serializer = CartItemSerializer(
                    data = request.data,
                    context = {
                        'cart_id': cart.id,
                        'product_id': pk,
                    }
                )
                serializer.is_valid()
                order = serializer.save()
                serializer = OrderSerializer(order)

                return Response({
                    "cart_id": cart.id
                }, status=status.HTTP_200_OK)

            except Exception as err:
                print(err)
                return Response({
                    'detail': 'Internal Server Error.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['POST'], detail=True)
    def buy(self, request, batch_pk=None, pk=None):

        serializer = BuyOrderCreateSerializer(data = request.data, context={
            "product_id": self.kwargs['pk']
        })

        try:
            serializer.is_valid()
            order = serializer.save()
            serializer = OrderSerializer(order)

        except Exception as error:
            print(error)
            return Response({
                "detail": "Internal Server Error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.data, status = status.HTTP_200_OK)



class CartViewSet(ModelViewSet):
    queryset = Cart.objects.all()

    def get_serializer_class(self):
        if self.action == 'initiate_order':
            return CartOrderCreateSerializer

        return CartSerializer

    @action(methods=['POST'], detail=True)
    def initiate_order(self, request, pk=None):

        serializer = CartOrderCreateSerializer(
            data={}, context = {
                "cart_id": self.kwargs['pk']
            }
        )

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
            if self.action == 'review':
                return ProductReviewCreateSerializer
            
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

    @action(methods=['POST'], detail=True)
    def review(self, request, pk=None):
        
        try:
            order = Order.objects.get(id=self.kwargs['pk'])
            print(order.is_reviewed)
            
            if order.is_reviewed: return Response({
                "detail": "Forbidden"
            }, status= status.HTTP_403_FORBIDDEN)
            
            serializer = ProductReviewCreateSerializer(data=request.data, context={
                "order": order
            })
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response({
                    "detail": "OK"
                }, status=status.HTTP_200_OK)
            
            return Response({
                "detail": "Bad Request"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Order.DoesNotExist:
            print("Order does not exist.")
            return Response({
                "detail": "Not Found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as error:
            print(f"Error in adding review: {error}")
            return Response({
                "detail": "Internal Server Error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
