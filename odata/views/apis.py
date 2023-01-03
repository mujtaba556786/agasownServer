import requests
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from bson import ObjectId
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from django.db import connection
from Project.settings import GP_CLIENT_ID, GP_CLIENT_SECRET
from datetime import datetime
from urllib.parse import urlencode
from django.conf import settings
from django.contrib import messages

from odata.models import (
    Payment,
    Product,
    Customer,
    Categories,
    ProductVariant,
    ProductImage,
    NewsletterSubscription,
)
from odata.serializers.serializers import (
    ProductSerializers,
    CustomerSerializers,
    CategorySerializers,
    PaymentSerializers,
    ProductImageSerializers,
    ProductVariantSerializers,
    NewsLetterSerializers,
)


# Create your views here.
class ProductViewSet(viewsets.ModelViewSet):
    """This viewset is used for crud operations"""

    model = Product
    queryset = Product.objects.all()
    serializer_class = ProductSerializers

    def get_object(self):
        return Product.objects.get(_id=ObjectId(self.kwargs.get('pk')))

    def get_serializer_context(self):
        context = super(ProductViewSet, self).get_serializer_context()
        context.update({"request": self.request})
        return context

    @action(
        detail=True,
        name="product-images",
        url_name="product_images",
        url_path="product-images",
        methods=["get"],
        serializer_class=ProductImageSerializers,
    )
    def get_product_images(self, request, pk=None):
        product = self.get_object()
        product_image = ProductImage.objects.filter(product=product)
        product_image_serialize = ProductImageSerializers(product_image, many=True)
        return Response(
            {"data": product_image_serialize.data}, status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        name="product-variants",
        url_name="product_variants",
        url_path="product-variants",
        methods=["get"],
        serializer_class=ProductVariantSerializers,
    )
    def get_product_variant(self, request, pk=None):
        product = self.get_object()
        product_variant = ProductVariant.objects.filter(product=product)
        product_variant_serialize = ProductVariantSerializers(
            product_variant, many=True
        )
        return Response(
            {"data": product_variant_serialize.data}, status=status.HTTP_200_OK
        )


class ProductImageViewSet(viewsets.ModelViewSet):
    """This viewset is used for crud operations"""

    model = ProductImage
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializers

    def get_object(self):
        return ProductImage.objects.get(_id=ObjectId(self.kwargs.get('pk')))


# class ProductVariantViewSet(generics.GenericAPIView):
#     """This viewset is used for crud operations"""
#
#     serializer_class = ProductVariantSerializers


class NewsLetterViewSet(viewsets.ModelViewSet):
    """This viewset is used for crud operations"""

    queryset = NewsletterSubscription.objects.all()
    serializer_class = NewsLetterSerializers

    # permission_classes = [IsAuthenticated]

    def get_object(self):
        return NewsletterSubscription.objects.get(_id=ObjectId(self.kwargs.get('pk')))


class CustomerViewSet(viewsets.ModelViewSet):
    """This viewset is used for crud operations"""

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializers

    # permission_classes = [IsAuthenticated]

    def get_object(self):
        return Customer.objects.get(_id=ObjectId(self.kwargs.get('pk')))


class CategoryViewSet(viewsets.ModelViewSet):
    """This viewset is used for crud operations"""

    queryset = Categories.objects.all()
    serializer_class = CategorySerializers

    def get_object(self):
        return Categories.objects.get(_id=ObjectId(self.kwargs.get('pk')))


class PaymentViewset(viewsets.ModelViewSet):
    """
    This viewset is used for crud operation
    """

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializers
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return Payment.objects.get(_id=ObjectId(self.kwargs.get('pk')))


class Wishlist(generics.GenericAPIView):
    def patch(self, request):
        customer_id = request.data["customer_id"]
        product_id = request.data["product_id"]
        cus_objInstance = ObjectId(customer_id)
        product_objInstance = ObjectId(product_id)
        if Customer.objects.filter(_id=cus_objInstance):
            customer = Customer.objects.get(_id=cus_objInstance)
            if Product.objects.filter(_id=product_objInstance):
                customer_wishlist = str(customer.wishlist).split(",")
                if product_id in customer_wishlist:
                    return JsonResponse({"message": "Product already exists"},
                                        status=400)
                else:
                    wishlist = customer.wishlist
                    wishlist = f"{wishlist},{product_id}" if wishlist else f"{product_id}"
                    customer.wishlist = wishlist
                    customer.save()
            else:
                return JsonResponse({"message": "Product doesn't exists"},
                                    status=400)
        else:
            return JsonResponse({"message": "Customer doesn't exists"},
                                status=400)

        return JsonResponse({"message": "Added Successfully"},
                            status=200)


class DeleteWishlist(generics.GenericAPIView):
    def delete(self, request):
        customer_id = request.data["customer_id"]
        product_id = request.data["product_id"]

        cus_objInstance = ObjectId(customer_id)
        product_objInstance = ObjectId(product_id)

        if Customer.objects.filter(_id=cus_objInstance):
            customer = Customer.objects.get(_id=cus_objInstance)
            if Product.objects.filter(_id=product_objInstance):
                if customer.wishlist:
                    customer_wishlist = customer.wishlist.split(',')
                    if product_id in customer_wishlist:
                        customer_wishlist.remove(product_id)
                        customer.wishlist = ",".join(customer_wishlist)
                    else:
                        return JsonResponse({"message": "Product_id doesn't exists in wishlist"},
                                            status=400)
                else:
                    return JsonResponse({"message": "Wishlist is empty"}, status=200)
            else:
                return JsonResponse({"message": "Product_id doesn't exists"},
                                    status=400)
        else:
            return JsonResponse({"message": "Customer doesn't exists"},
                                status=400)
        customer.save()
        return JsonResponse({"message": "Deleted Successfully"},
                            status=200)


class ProductVariants(generics.GenericAPIView):
    def post(self, request):
        product_id = request.data["product_id"]
        if not product_id:
            return JsonResponse({"message": "Enter product id"}, status=400)
        else:
            product_objInstance = ObjectId(product_id)

            product = Product.objects.get(_id=product_objInstance)
            if not product:
                return JsonResponse({"message": "Product doesn't exists"}, status=400)

            else:
                size = request.data["size"]
                ean = request.data["ean"]
                color = request.data["color"]
                material = request.data["material"]

                productVariant = ProductVariant(size=size, color=color, material=material, parent_product=product,
                                                ean=ean)
                productVariant.save()
                product.ean = ean
                product.save()

        return JsonResponse({"message": "Product Variant added successfully"},
                            status=200)


class Checkout(generics.GenericAPIView):
    def patch(self, request):
        customer_id = request.data["customer_id"]
        product_id = request.data["product_id"]
        cus_objInstance = ObjectId(customer_id)
        product_objInstance = ObjectId(product_id)
        if Customer.objects.filter(_id=cus_objInstance):
            customer = Customer.objects.get(_id=cus_objInstance)
            if Product.objects.filter(_id=product_objInstance):
                customer_checkout = str(customer.checkout).split(",")
                if product_id in customer_checkout:
                    checkout = customer.checkout
                    checkout = f"{checkout},{product_id}" if checkout else f"{product_id}"
                    customer.checkout = checkout
                    customer.save()
            else:
                return JsonResponse({"message": "Product doesn't exists"},
                                    status=400)
        else:
            return JsonResponse({"message": "Customer doesn't exists"},
                                status=400)

        return JsonResponse({"message": "Added Successfully"},
                            status=200)


class DeleteCheckout(generics.GenericAPIView):
    def delete(self, request):
        customer_id = request.data["customer_id"]
        product_id = request.data["product_id"]

        cus_objInstance = ObjectId(customer_id)
        product_objInstance = ObjectId(product_id)

        if Customer.objects.filter(_id=cus_objInstance):
            customer = Customer.objects.get(_id=cus_objInstance)
            if Product.objects.filter(_id=product_objInstance):
                if customer.checkout:
                    customer_checkout = customer.checkout.split(',')
                    if product_id in customer_checkout:
                        customer_checkout.remove(product_id)
                        customer.checkout = ",".join(customer_checkout)
                    else:
                        return JsonResponse({"message": "Product_id doesn't exists in checkout_session"},
                                            status=400)
                else:
                    return JsonResponse({"message": "Checkout is empty"}, status=200)
            else:
                return JsonResponse({"message": "Product_id doesn't exists"},
                                    status=400)
        else:
            return JsonResponse({"message": "Customer doesn't exists"},
                                status=400)
        customer.save()
        return JsonResponse({"message": "Deleted Successfully"},
                            status=200)


class TotalAmount(generics.GenericAPIView):
    def post(self, request):
        import pdb;
        pdb.set_trace()
        data = request.data
        customer_id = data.get("customer_id", None)
        quantity = int(data.get("quantity", 0))
        voucher = data.get("voucher", None)
        discount = data.get("discount", None)

        customer = Customer.objects.get(_id=ObjectId(customer_id))
        customer_checkout = str(customer.checkout).split(",")
        total_amount = 0
        amount = 0
        num = None
        if voucher == "" or discount:
            for i in range(len(discount)):
                if discount[i].isdigit():
                    num = discount[i:]
                    break
            disc = int(num)
            for product_id in customer_checkout:
                product = Product.objects.get(_id=ObjectId(product_id))
                product_price = product.price
                amount += product_price * quantity
                total_amount = ("{:.2f}".format(amount - (amount * (disc / 100))))
            return JsonResponse({"Total Amount": total_amount}, status=200)

        elif discount == "" or voucher:
            for i in range(len(voucher)):
                if voucher[i].isdigit():
                    num = voucher[i:]
                    break
            vouch = int(num)
            for product_id in customer_checkout:
                product = Product.objects.get(_id=ObjectId(product_id))
                product_price = product.price
                amount += product_price * quantity
                total_amount = ("{:.2f}".format(amount - (amount * (vouch / 100))))
            customer.voucher = "expired"
            customer.save()

            return JsonResponse({"Total Amount": total_amount}, status=200)

        else:
            for product_id in customer_checkout:
                product = Product.objects.get(_id=ObjectId(product_id))
                product_price = product.price
                amount += product_price * quantity
                total_amount = ("{:.2f}".format(amount))
            return JsonResponse({"Total Amount": total_amount}, status=200)


class GuestLogin(generics.GenericAPIView):
    def post(self, request):
        first_name = request.data["first_name"]
        last_name = request.data["last_name"]
        email = request.data["email"]

        user_email = User.objects.filter(email=email)
        if user_email:
            return JsonResponse({"message": "Email_Id already exists"},
                                status=200)
        else:
            try:
                user_count = User.objects.count()
                username = f"GUEST_{first_name}{last_name}_{user_count}"
                user = User.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    username=username,
                )
                customer = Customer.objects.create(user=user, first_name=first_name, last_name=last_name, email=email,
                                                   guest_login=True)
                customer.save()
                return JsonResponse({"message": "Successfully Logged"}, status=200)
            except Exception as e:
                return JsonResponse({"message": str(e)}, status=500)


def google_login(request):
    redirect_uri = "%s://%s%s" % (
        request.scheme, request.get_host(), reverse('google_login')
    )

    if 'code' in request.GET:
        params = {
            'grant_type': 'authorization_code',
            'code': request.GET.get('code'),
            'redirect_uri': redirect_uri,
            'client_id': GP_CLIENT_ID,
            'client_secret': GP_CLIENT_SECRET
        }
        url = 'https://accounts.google.com/o/oauth2/token'
        response = requests.post(url, data=params)

        url = 'https://www.googleapis.com/oauth2/v1/userinfo'
        access_token = response.json().get('access_token')
        response = requests.get(url, params={'access_token': access_token})
        user_data = response.json()
        email = user_data.get('email')
        first_name = user_data.get('given_name')
        last_name = user_data.get("family_name")
        try:
            user_count = User.objects.count()
            username = f"GOOGLE_{first_name}{last_name}_{user_count}"
            user = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
            )
            customer = Customer.objects.create(user=user)
            customer.save()
            return redirect('/')
        except Exception as e:
            return JsonResponse({"message": e}, status=400)
    else:
        url = "https://accounts.google.com/o/oauth2/auth?client_id=%s&response_type=code&scope=%s&redirect_uri=%s&state=google"
        scope = [
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email"
        ]
        scope = " ".join(scope)
        url = url % (GP_CLIENT_ID, scope, redirect_uri)
        return redirect(url)
