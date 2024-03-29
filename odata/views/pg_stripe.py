"""Handle Stripe Payment Gateway"""
from distutils.log import error
from locale import currency
import os
import json
from webbrowser import get
# # Third Party import
import stripe
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect
from odata.models import Payment, Order
from rest_framework.views import APIView
from rest_framework import status, response
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from odata.utility.send_receipt_mail import send_mail_card, send_mail_sofort
from django.http.response import HttpResponse, JsonResponse
from rest_framework.permissions import IsAuthenticated
from odata.models import Product, Payment, Customer
from Project.settings import STRIPE_SECRET_KEY, STRIPE_PUBLISH_KEY, DOMAIN_URL
from bson import ObjectId
from datetime import datetime

stripe.api_key = STRIPE_SECRET_KEY


class StipeCheckoutSession(TemplateView):
    """Stripe Checkout View for stripe checkout payment"""

    template_name = "stripe.html"

    def get_context_data(self, **kwargs):
        context = super(StipeCheckoutSession, self).get_context_data(**kwargs)
        context["product_ids"] = self.request.GET.get("p_ids")
        context["quantity"] = self.request.GET.get("qty")
        context["STRIPE_PUBLISH_KEY"] = STRIPE_PUBLISH_KEY

        return context


# API for credit_cards payment
class StripeCard(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = (request.__dict__.get('_auth')).__dict__.get('user_id')
        customer_id = (Customer.objects.get(user_id=user_id))._id
        if customer_id:
            if Customer.objects.filter(_id=ObjectId(customer_id)):
                data = request.POST.dict()
                card_number = data.get("card_number")
                exp_month = data.get("exp_month")
                exp_year = data.get("exp_year")
                cvc = data.get("cvc")
                total_amount = data.get("amount")
                currency = data.get("currency")
                name = data.get("name", "")
                email = data.get("email", "")
                cus_add_line1 = data.get("cus_add_line1")
                cus_add_city = data.get("cus_add_city")
                cus_add_state = data.get("cus_add_state")
                postal_code = data.get("postal_code")
                country = data.get("country")
                description = data.get("description")
                customer = Customer.objects.get(_id=ObjectId(customer_id))

                if not customer:
                    return HttpResponse("Customer doesn't exists")
                else:
                    try:
                        amount = int(float(total_amount) * 100)
                        payment_method = stripe.PaymentMethod.create(
                            type="card",
                            card={
                                "number": card_number,
                                "exp_month": exp_month,
                                "exp_year": exp_year,
                                "cvc": cvc,
                            },
                            billing_details={
                                "name": "Agasown",
                                "address": {
                                    "line1": "Bergmannstraße 13",
                                    "city": "Berlin",
                                    "state": "Germany",
                                }
                            }
                        )
                        create_customer = stripe.Customer.create(
                            description=description,
                            name=name,
                            email=email,
                            address={
                                "line1": cus_add_line1,
                                "city": cus_add_city,
                                "state": cus_add_state,
                                "country": country,
                                "postal_code": postal_code,
                            },
                            payment_method=payment_method['id'],
                        )

                        intent_create = stripe.PaymentIntent.create(
                            customer=create_customer['id'],
                            description=description,
                            shipping={
                                "name": "Agasown",
                                "address": {
                                    "line1": "Bergmannstraße 13",
                                    "city": "Berlin",
                                    "state": "Germany",
                                }
                            },

                            amount=amount,
                            currency=currency,
                            payment_method_types=["card"],
                            payment_method=payment_method['id']
                        )

                        intent = stripe.PaymentIntent.confirm(
                            intent_create['id'],
                        )
                        retrieve = stripe.PaymentIntent.retrieve(
                            intent['id'],
                        )
                        payment_method_type = retrieve.charges.data[0].payment_method_details.type
                        card_brand = retrieve.charges.data[0].payment_method_details.card.brand
                        last_digits = retrieve.charges.data[0].payment_method_details.card.last4
                        card_type = retrieve.charges.data[0].payment_method_details.card.funding
                        receipt_url = retrieve.charges.data[0].receipt_url
                        date_of_payment = datetime.fromtimestamp(retrieve.charges.data[0].created).strftime("%Y-%m-%d")
                        date = datetime.fromtimestamp(retrieve.charges.data[0].created).strftime("%Y%m%d")
                        payment_status = retrieve.charges.data[0].status
                        invoice_count = Payment.objects.count()
                        order_count = str(Order.objects.count())
                        checkout = customer.checkout

                        if checkout:
                            customer_checkout = customer.checkout.split(",")
                            customer_checkout_qtn = customer.checkout_quantity.split(",")
                            for i, product_id in enumerate(customer_checkout):
                                product = Product.objects.get(_id=ObjectId(product_id))
                                product.quantity = product.quantity - int(customer_checkout_qtn[i])
                                product.save()
                            product_details = {}
                            for prd in customer_checkout:
                                for qty in customer_checkout_qtn:
                                    product_details[prd] = int(qty)
                                    customer_checkout_qtn.remove(qty)
                                    break

                            payment = Payment(invoice=f"AGASOWN_{date}_{invoice_count}", customer=customer,
                                              payment_type=payment_method_type, status=payment_status,
                                              date_of_payment=date_of_payment, amount=total_amount)
                            payment.save()

                            order = Order(customer=customer, order_number=order_count, order_date=date, paid=True,
                                          payment=payment, product_details=product_details)
                            order.save()
                            send_mail_card(
                                customer_email=email, retrieve_url=receipt_url, name=name,
                                payment_method_type=payment_method_type, card_brand=card_brand, last_digits=last_digits,
                                card_type=card_type
                            )
                            customer.checkout = ""
                            customer.checkout_quantity = ""
                            customer.save()
                        else:
                            return JsonResponse({'message': "Checkout is empty"}, status=404)
                    except stripe.error.CardError as e:
                        return response.Response(
                            {"msg": e.user_message},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    except stripe.error.RateLimitError as e:
                        return response.Response(
                            {"msg": e.user_message},
                            status=status.HTTP_409_CONFLICT,
                        )
                    except stripe.error.InvalidRequestError as e:
                        return response.Response(
                            {"msg": e.user_message},
                            status=status.HTTP_402_PAYMENT_REQUIRED,
                        )
                    except stripe.error.AuthenticationError as e:
                        return response.Response(
                            {"msg": e.user_message},
                            status=status.HTTP_401_UNAUTHORIZED,
                        )
                    except stripe.error.APIConnectionError as e:
                        return response.Response(
                            {"msg": e.user_message},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )
                    except stripe.error.StripeError as e:
                        return response.Response(
                            {"msg": e.user_message},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE,
                        )
                    except Exception as e:
                        return HttpResponse(e)

                    return HttpResponse("Payment Successful")
            else:
                return JsonResponse({'message': "Customer Id does not exists"}, status=404)
        else:
            return JsonResponse({'message': "Please give Customer Id"}, status=404)


class SofortGet(APIView):
    def get(self, request):
        payment_id = request.GET["payment_intent"]
        customer_id = request.GET['customer_id']
        customer_objectID = ObjectId(customer_id)
        retrieve_customer = stripe.PaymentIntent.retrieve(payment_id)
        bank_code = retrieve_customer.charges.data[0].payment_method_details.sofort.bank_code
        amount = retrieve_customer.charges.data[0].amount / 100
        bank_name = retrieve_customer.charges.data[0].payment_method_details.sofort.bank_name
        payment_type = retrieve_customer.charges.data[0].payment_method_details.type
        last_digits = retrieve_customer.charges.data[0].payment_method_details.sofort.iban_last4
        payment_status = retrieve_customer.charges.data[0].status
        customer_id = retrieve_customer.customer
        cus_detials = stripe.Customer.retrieve(customer_id)
        customer_name = cus_detials.name
        customer_email = cus_detials.email
        date_of_payment = datetime.fromtimestamp(cus_detials.created).strftime("%Y-%m-%d")
        date = datetime.fromtimestamp(cus_detials.created).strftime("%Y%m%d")
        invoice_count = Payment.objects.count()
        order_count = str(Order.objects.count())

        customer = Customer.objects.get(_id=customer_objectID)
        checkout = customer.checkout
        if customer:
            if checkout:
                customer_checkout = customer.checkout.split(",")
                customer_checkout_qtn = customer.checkout_quantity.split(",")
                for i, product_id in enumerate(customer_checkout):
                    product = Product.objects.get(_id=ObjectId(product_id))
                    product.quantity = product.quantity - int(customer_checkout_qtn[i])
                    product.save()
                product_details = {}
                for prd in customer_checkout:
                    for qty in customer_checkout_qtn:
                        product_details[prd] = int(qty)
                        customer_checkout_qtn.remove(qty)
                        break

                payment = Payment(invoice=f"AGASOWN_{date}_{invoice_count}", payment_type=payment_type,
                                  customer=customer,
                                  status=payment_status, date_of_payment=date_of_payment, amount=amount)
                payment.save()
                order = Order(customer=customer, order_number=order_count, order_date=date, paid=True,
                              payment=payment, product_details=product_details)
                order.save()
                send_mail_sofort(customer_email=customer_email, customer_name=customer_name,
                                 bank_name=bank_name, bank_code=bank_code, payment_type=payment_type,
                                 last_digits=last_digits)
                customer.checkout = ""
                customer.checkout_quantity = ""
                customer.save()

                return redirect("http://64.227.115.243/index.html#/payment",
                                status=200)
            else:
                return JsonResponse({'message': "Checkout is empty"}, status=404)
        else:
            return JsonResponse({'message': "Customer does not exists"}, status=404)


class StripSofort(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = (request.__dict__.get('_auth')).__dict__.get('user_id')
        customer_id = (Customer.objects.get(user_id=user_id))._id
        if customer_id:
            if Customer.objects.filter(_id=ObjectId(customer_id)):
                customer = Customer.objects.get(_id=ObjectId(customer_id))
                if customer.checkout:
                    data = request.POST.dict()
                    name = data.get("name")
                    email = data.get("email")
                    cus_add_line1 = data.get("cus_add_line1")
                    cus_add_city = data.get("cus_add_city")
                    cus_add_state = data.get("cus_add_state")
                    amount = float(data.get("amount"))
                    currency = data.get("currency")
                    country = data.get("country")
                    postal_code = data.get("postal_code")
                    description = data.get("description")

                    try:
                        amount = int(amount * 100)
                        payment_method = stripe.PaymentMethod.create(
                            type="sofort",
                            sofort={
                                "country": country,
                            },
                        )

                        customer = stripe.Customer.create(
                            description="My First Sofort Test Customer",
                            name=name,
                            email=email,
                            address={
                                "line1": cus_add_line1,
                                "city": cus_add_city,
                                "state": cus_add_state,
                                "country": country,
                                "postal_code": postal_code,
                            },
                            shipping={
                                "name": "Agasown",
                                "address": {
                                    "line1": "Bergmannstraße 13",
                                    "city": "Berlin",
                                    "state": "Germany",
                                }
                            }
                        )

                        payment_intent = stripe.PaymentIntent.create(
                            description=description,
                            amount=amount,
                            currency=currency,
                            customer=customer["id"],
                            payment_method=payment_method["id"],
                            payment_method_types=["sofort"],

                        )

                        confirm_payment = stripe.PaymentIntent.confirm(
                            payment_intent["id"],
                            payment_method=payment_intent["payment_method"],
                            return_url=f"http://64.227.115.243:8080/stripe/sofort_get/?customer_id={customer_id}",
                            receipt_email=email,
                        )
                        url = confirm_payment["next_action"]
                        check_url = url["redirect_to_url"]
                        authenticate_url = check_url["url"]

                    except stripe.error.InvalidRequestError as e:
                        return response.Response(
                            {"msg": e.user_message},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    except stripe.error.StripeError as e:
                        return response.Response(
                            {"msg": e.user_message},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE,
                        )
                    except Exception as e:
                        return response.Response(
                            {"msg": e},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    return HttpResponse(f"{authenticate_url}")
                else:
                    return JsonResponse({'message': "Checkout is empty"}, status=404)
            else:
                return JsonResponse({'message': "Customer Id does not exists"}, status=404)
        else:
            return JsonResponse({'message': "Please give Customer Id"}, status=404)


class CreateCheckoutSession(APIView):
    """Class to create CheckoutSession
    Args:
        APIView (class): ResT framework APIView class
    """

    def get(self, request):
        try:
            domain_url = DOMAIN_URL
            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [payment_intent_data] - capture the payment later
            # [customer_email] - prefill the email input in the form
            # For full details see https://stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
            product_ids = self.request.GET.get("p_ids")
            quantities = self.request.GET.get("qty")
            if product_ids:
                quantities = quantities.split(",")
                cart_items = []
                i = 0
                for product in product_ids.split(","):
                    single_pro = Product.get(product)
                    if single_pro:
                        cart_items.append(
                            {
                                "name": single_pro.product_name,
                                "quantity": quantities[i],
                                "currency": "currency",
                                "amount": single_pro.price * 100,
                            }
                        )
                        i = i + 1
            checkout_session = stripe.checkout.Session.create(
                success_url=domain_url
                            + "stripe/success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=domain_url + "stripe/cancelled",
                payment_method_types=["card", "sofort"],
                mode="payment",
                line_items=cart_items,
            )
            return response.Response({"sessionId": checkout_session["id"]})
        except Exception as e:
            return response.Response(error=str(e), status=status.HTTP_403_FORBIDDEN)


# class StripeWebhookView(APIView):
#     def post(self,request):
#         stripe.api_key = settings.STRIPE_SECRET_KEY
#         endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
#         payload = request.data
#         sig_header = request.META['HTTP_STRIPE_SIGNATURE']
#         # event = None
#         try:
#             event = stripe.Webhook.construct_event(
#                 payload, sig_header, endpoint_secret
#             )
#         except ValueError as e:
#             print(e)
#             # Invalid payload
#             return response.Response(
#                 {"msg": "Invalid payload", "status": status.HTTP_400_BAD_REQUEST},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         except stripe.error.SignatureVerificationError as e:
#             print(e)
#             # Invalid signature
#             return response.Response(
#                 {"msg": "Invalid payload", "status": status.HTTP_400_BAD_REQUEST},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # Handle the checkout.session.completed event
#         if event["type"] == "checkout.session.completed":
#             print("Payment was successful.")
#             # TODO: run some custom code here

#         return "Success", 200


def success(request):
    stripe_session = stripe.checkout.Session.retrieve(
        request.GET.get("session_id"))
    cust = stripe.Customer.retrieve(stripe_session.customer)
    customer = Customer.get(cust.email)
    import uuid
    import datetime

    if customer:
        data = {
            "customer": customer,
            "order": uuid.uuid4().hex[:6].upper(),
            "invoice": dict(stripe_session),
            "amount": stripe_session.amount_total / 100,
            "payment_type": "card/stripe",
            "date_of_payment": datetime.datetime.now(),
            "status": stripe_session.payment_status,
        }
        payment_data = Payment.objects.create(**data)

    return "/"
