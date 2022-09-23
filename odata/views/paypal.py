from rest_framework.views import APIView
from django.http import HttpResponse, JsonResponse
import paypalrestsdk
from django.core.mail import send_mail
from Project.settings import EMAIL_HOST_USER
from django.shortcuts import redirect
# import logging
from Project.settings import PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET

paypalrestsdk.configure({
    "mode": "sandbox",
    "client_id": PAYPAL_CLIENT_ID,
    "client_secret": PAYPAL_CLIENT_SECRET
})


class Paypal(APIView):
    def get(self, request):
        payment_id = request.GET["paymentId"]
        payer_id = request.GET["PayerID"]
        payment = paypalrestsdk.Payment.find(payment_id)

        if payment.execute({"payer_id": payer_id}):
            product_name = payment.transactions[0].item_list.items[0].name
            price = str(payment.transactions[0].item_list.items[0].price)
            quantity = str(payment.transactions[0].item_list.items[0].quantity)
            total_amount = str(payment.transactions[0].amount.total)
            email = payment.payer.payer_info.email

            email_body = "Hello ,\n Here is your Order Summary: \n Order Details\n Product Name:" + product_name + "\n Product Quantity:" + quantity + "\n Product Price:" + price + "\n Total Amount to Pay:" + total_amount + "\n Mode of payment: PayPal Payment Gateway \n Your order will be delivered within 3 working days.\n You will receive an email shortly after it's dispatched.\n Best wishes,\n AgasOwn Marketing Team \n "
            send_mail(
                subject='Payment Successful for PayPal',
                message=email_body,
                from_email=EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False)

            return redirect("http://localhost:8080/index.html#/payment",
                            status=200)

        else:
            return JsonResponse({"error": payment.error}, status=500)

    def post(self, request):
        data = request.POST.dict()
        product_name = data.get("product_name")
        price = int(data.get("price"))
        currency = data.get("currency")
        quantity = int(data.get("quantity"))
        total = price * quantity
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"},
            "redirect_urls": {
                "return_url": "http://localhost:8000/paypal/payment/",
                "cancel_url": "http://localhost:8000/"},
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": product_name,
                        "sku": "item",
                        "price": price,
                        "currency": currency,
                        "quantity": quantity}]},
                "amount": {
                    "total": total,
                    "currency": currency},
                "description": "This is the payment transaction description."}]})

        if payment.create():  # Authorizing payment
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = str(link.href)
                    return HttpResponse({approval_url})
        else:
            return JsonResponse({"error": payment.error}, status=400)
