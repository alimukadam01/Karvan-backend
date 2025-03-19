from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Order

@receiver(post_save, sender=Order)
def send_admin_email_on_order_confirmation(sender, **kwargs):
    order = kwargs['instance']
    
    if not kwargs['created'] and order and not order._state.adding:
        if order.status == "OK":
            message =  f"""
                Dear Karvan Team,

                A new order has been placed on Karvan. Below are the order details:

                Order Details:
                Order ID: {order.id}
                Customer Name: {order.buyer.first_name} {order.buyer.last_name}  
                Email: {order.buyer.email}
                Phone: {order.buyer.phone}
                Shipping Address: {order.address.address}
                Payment Method: Cash On Delivery
                Total Amount: PKR {order.payment.amount}\n
                Ordered Items:
            """
            order_items = order.items.all()
            items = "".join([
                f"""
                { item.product.name } ({item.size} x {item.quantity})\n
                """
                for item in order_items 
            ])

            message +=  items
            message += """
                Next Steps:
                    ✅ Update Order Status: Mark as Processing in the system.
                    ✅ Process the Order: Ensure timely dispatch.

                    For more details, please log in to the Karvan Admin Panel.

                    Best Regards,
                    Karvan Order System
            """

            send_mail(
                f"📦 New Order Received - Order #{ order.id }",
                message,
                settings.ORDER_CONFIRM_EMAIL,
                ["admin@shopkarvan.pk"],
                False                
            )
    
    return

@receiver(post_save, sender=Order)
def send_review_email_upon_order_delivery(sender, **kwargs):

    order = kwargs["instance"]

    if not kwargs['created'] and order and not order._state.adding and not order.is_reviewed:
        if order.status == "C":
            send_mail(
                "Your Order's Here! Now, Tell Us What You Think 👀",
                f"""
                Hey {order.buyer.first_name},

                Hope you're loving your new Karvan goodies! We'd love to hear your thoughts — your feedback helps us improve and also guides fellow shoppers.
                Hit the link below and drop a quick review:

                "https://shopkarvan.pk/review/{order.id}/"

                Takes just a sec, and who knows? It might get you some exclusive perks in the future. 😉

                Thanks for being part of the Karvan fam! 💜

                Cheers,
                The Karvan Team
                support@shopkarvan.pk
                shopkarvan.pk
                """,
                settings.ORDER_CONFIRM_EMAIL,
                [order.buyer.email],
                True
            )

            return