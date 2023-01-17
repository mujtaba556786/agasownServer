from datetime import datetime

from bson import ObjectId
from rest_framework.views import APIView
from django.http import HttpResponse, JsonResponse
import paypalrestsdk
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import redirect
from odata.utility.send_receipt_mail import send_mail_paypal
from Project.settings import PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET
from odata.models import Customer, Payment, Order
import datetime

paypalrestsdk.configure({
    "mode": "sandbox",
    "client_id": PAYPAL_CLIENT_ID,
    "client_secret": PAYPAL_CLIENT_SECRET
})


class PaypalGet(APIView):
    def get(self, request):
        payment_id = request.GET["paymentId"]
        payer_id = request.GET["PayerID"]
        customer_id = request.GET["customer_id"]
        customer_objectID = ObjectId(customer_id)
        payment = paypalrestsdk.Payment.find(payment_id)

        if payment.execute({"payer_id": payer_id}):

            total_amount = str(payment.transactions[0].related_resources[0].sale.amount.total)
            email = payment.payer.payer_info.email
            first_name = payment.payer.payer_info.first_name
            last_name = payment.payer.payer_info.last_name
            date_of_payment = datetime.datetime.strptime(payment.create_time, "%Y-%m-%dT%H:%M:%SZ")
            date = date_of_payment.strftime("%Y-%m-%d")
            invoice_date = date_of_payment.strftime("%Y%m%d")
            payment_status = payment.transactions[0].related_resources[0].sale.state
            payment_amount = payment.transactions[0].related_resources[0].sale.amount.total
            invoice_count = Payment.objects.count()
            order_count = str(Order.objects.count())

            customer = Customer.objects.get(_id=customer_objectID)
            checkout = customer.checkout
            if customer:
                if checkout:
                    payment = Payment(invoice=f"AGASOWN_{invoice_date}_{invoice_count}",
                                      payment_type="PAYPAL", customer=customer,
                                      status=payment_status, date_of_payment=date, amount=payment_amount)

                    payment.save()

                    order = Order(customer=customer, order_number=order_count, order_date=date, paid=True,
                                  payment=payment, product_id=checkout)
                    order.save()
                    customer.checkout = None
                    customer.save()
                    send_mail_paypal(first_name=first_name, last_name=last_name,
                                     total_amount=total_amount, email=email)

                    return redirect("http://64.227.115.243/index.html#/payment",
                                    status=200)
                else:
                    return JsonResponse({'message': "Checkout is empty"}, status=404)
            else:
                return JsonResponse({'message': "Customer does not exists"}, status=404)
        else:
            return JsonResponse({"error": payment.error}, status=500)


class Paypal(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        access_token = request.__dict__.get('_auth')
        user_id = (request.__dict__.get('_auth')).__dict__.get('user_id')
        customer_id = (Customer.objects.get(user_id=user_id))._id
        if customer_id:
            if Customer.objects.filter(_id=ObjectId(customer_id)):
                customer = Customer.objects.get(_id=ObjectId(customer_id))
                if customer.checkout:
                    data = request.POST.dict()
                    currency = data.get("currency")
                    total = data.get("total_amount")
                    payment = paypalrestsdk.Payment({
                        "intent": "sale",
                        "payer": {
                            "payment_method": "paypal"
                        },
                        "redirect_urls": {
                            "return_url": f"http://127.0.0.1:8000/paypal/payment_get/?customer_id={customer_id}",
                            "cancel_url": "http://127.0.0.1:8000/"},
                        "transactions": [
                            {
                                "amount": {
                                    "total": float(total),
                                    "currency": currency
                                },
                                "description": "This is the payment transaction description."}]})

                    if payment.create():  # Authorizing payment
                        for link in payment.links:
                            if link.rel == "approval_url":
                                approval_url = str(link.href)
                                return HttpResponse({approval_url})
                    else:
                        return JsonResponse({"error": payment.error}, status=400)
                else:
                    return JsonResponse({"message": "Checkout is empty"}, status=404)
            else:
                return JsonResponse({'message': "Customer Id does not exists"}, status=404)
        else:
            return JsonResponse({'message': "Please give Customer Id"}, status=404)
