from rest_framework.views import APIView
from django.http import HttpResponse, JsonResponse
import paypalrestsdk
from django.core.mail import send_mail
from Project.settings import EMAIL_HOST_USER
from django.shortcuts import redirect
# import logging
from odata.utility.send_receipt_mail import send_mail_paypal
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
            first_name = payment.payer.payer_info.first_name
            last_name = payment.payer.payer_info.last_name

            send_mail_paypal(first_name=first_name, last_name=last_name, price=price, quantity=quantity,
                             total_amount=total_amount, email=email, product_name=product_name)

            return redirect("http://64.227.115.243/index.html#/payment",
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
                "return_url": "http://64.227.115.243:8080/paypal/payment/",
                "cancel_url": "http://64.227.115.243/"},
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
