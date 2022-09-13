"""Handle Stripe Payment Gateway"""

# python imports
from distutils.log import error
from locale import currency
import os
import json
from webbrowser import get
# from responses import Response

# # Third Party import
import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework import status, response
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
# import sofort

# local import
from odata.models import Product, Payment, Customer
from Project.settings import STRIPE_SECRET_KEY, STRIPE_PUBLISH_KEY, DOMAIN_URL

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


def create_payment_method(card_data):
    payment_method = stripe.PaymentMethod.create(
        type="card",
        card=card_data
    )
    return payment_method


# API for credit_cards payment


class StripeCard(APIView):
    def post(self, request, format=None):
        data = request.POST.dict()
        card_number = data.get("card_number")
        exp_month = data.get("exp_month")
        exp_year = data.get("exp_year")
        cvc = data.get("cvc")
        # descript = data.get("descript")

        card = {
            "number": card_number,
            "exp_month": exp_month,
            "exp_year": exp_year,
            "cvc": cvc,
        }
        try:
            payment_method = create_payment_method(card)
            create_customer = stripe.Customer.create(
                description=data.get(
                    "customer_description", "Customer Default Description"),
                name=data.get("name", ""),
                email=data.get("email", ""),
                # address=data.get("address", ""),
                payment_method=payment_method['id']
            )

            intent_create = stripe.PaymentIntent.create(
                customer=create_customer['id'],
                # description = descript,
                description=data.get(
                    "description", "Payment Intent Default Description"),
                # shipping={
                #     "name": data.get("shipping_name", create_customer["name"]),
                #     "address": data.get("shipping_address", create_customer["address"])
                # },

                amount=data.get("amount"),
                currency=data.get("currency"),
                payment_method_types=["card"],
                payment_method=payment_method['id']
            )

            intent = stripe.PaymentIntent.confirm(
                intent_create['id']
            )
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

        retrieve = stripe.PaymentIntent.retrieve(
            intent_create['id'],
        )

        return HttpResponse("payment Successful")


class StripSofort(APIView):
    def get(self, request):
        payment_id = request.GET["payment_intent"]
        customer_id = request.GET["payment_intent_client_secret"]

        return JsonResponse({"payment_id": payment_id})

    def post(self, request):
        data = request.POST.dict()
        name = data.get("name")
        email = data.get("email")
        cus_add_line1 = data.get("cus_add_line1")
        cus_add_city = data.get("cus_add_city")
        cus_add_state = data.get("cus_add_state")
        amount = data.get("amount")
        currency = data.get("currency")
        country = data.get("country")

        try:
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
                description="Payment with sofort",
                amount=amount,
                currency=currency,
                customer=customer["id"],
                payment_method=payment_method["id"],
                payment_method_types=["sofort"],
            )

            confirm_payment = stripe.PaymentIntent.confirm(
                payment_intent["id"],
                payment_method=payment_intent["payment_method"],
                return_url="http://localhost:8000/stripe/sofort"
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
