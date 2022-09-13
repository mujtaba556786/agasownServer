from rest_framework.views import APIView
from django.http import HttpResponse,JsonResponse
import paypalrestsdk

# import logging
# from paypal_intigration.paypal_intigration.settings import PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET

paypalrestsdk.configure({
    "mode": "sandbox",
    "client_id": "Aa176Af9rSh-7gDZELoNnJoGTjOpXfo0ECrNw6HjD4633ArdVOw59D4rafyywX887C-N9k_albOUlBiE",
    "client_secret": "EGyQfM4tLnJTszmQcnIF185Br3YUUt2VEyaj9yQrLZeiLqwKUxB5wWeHomsrwSnqJEahIC1TuMbggpse"
})


class Paypal(APIView):
    def get(self, request):
        payment_id = request.GET["paymentId"]
        payer_id = request.GET["PayerID"]
        payment = paypalrestsdk.Payment.find(payment_id)

        if payment.execute({"payer_id": payer_id}):
            return JsonResponse({"payment_id": payment.id})
            # payment_history = paypalrestsdk.Payment.all({"count": 10})
            # print(payment_history)

        else:
            return HttpResponse(payment.error)

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
                "return_url": "http://localhost:8000/paypal",
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
                    return HttpResponse(approval_url)
        else:
            return HttpResponse(payment.error)
