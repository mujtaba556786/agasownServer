import requests
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from bson import ObjectId
from rest_framework.reverse import reverse
from Project.settings import GP_CLIENT_ID, GP_CLIENT_SECRET
from django.contrib.auth.hashers import make_password
from odata.utility.helpers import get_access_token
from django.forms.models import model_to_dict

from odata.models import (
    Payment,
    Product,
    Customer,
    Categories,
    ProductVariant,
    ProductImage,
    NewsletterSubscription,
    Order
)
from odata.serializers.serializers import (
    ProductSerializers,
    CustomerSerializers,
    CategorySerializers,
    PaymentSerializers,
    ProductImageSerializers,
    ProductVariantSerializers,
    NewsLetterSerializers,
    OrderSerializers
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

    queryset = NewsletterSubscription.objects.none()
    serializer_class = NewsLetterSerializers

    # permission_classes = [IsAuthenticated]

    def get_object(self):
        return NewsletterSubscription.objects.get(_id=ObjectId(self.kwargs.get('pk')))


class CustomerViewSet(viewsets.ModelViewSet):
    """This viewset is used for crud operations"""

    queryset = Customer.objects.none()
    serializer_class = CustomerSerializers

    permission_classes = [IsAuthenticated]

    def get_object(self):
        return Customer.objects.get(user_id=self.kwargs.get('pk'))


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


class OrderViewset(viewsets.ModelViewSet):
    """
    This viewset is used for crud operation
    """

    queryset = Order.objects.all()
    serializer_class = OrderSerializers
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return Order.objects.get(_id=ObjectId(self.kwargs.get('pk')))


class OrderCustomer(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = (request.__dict__.get('_auth')).__dict__.get('user_id')
        customer_id = (Customer.objects.get(user_id=user_id))._id
        if customer_id:
            if Customer.objects.filter(_id=customer_id):
                orders = Order.objects.filter(customer_id=customer_id)
                order_details = []
                for order in orders:
                    order_dict = model_to_dict(order)
                    order_dict['_id'] = str(order_dict['_id'])
                    order_dict['customer'] = str(order_dict['customer'])
                    order_dict['payment'] = str(order_dict['payment'])
                    order_details.append(order_dict)
                return JsonResponse({'order_details': order_details}, status=200)
            else:
                return JsonResponse({'message': "Customer Id does not exists"}, status=404)
        else:
            return JsonResponse({'message': "Please give Customer Id"}, status=404)


class Wishlist(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user_id = (request.__dict__.get('_auth')).__dict__.get('user_id')
        customer_id = (Customer.objects.get(user_id=user_id))._id
        if customer_id:
            data = request.data
            product_id = data.get("product_id", None)
            if Customer.objects.filter(_id=customer_id):
                customer = Customer.objects.get(_id=customer_id)
                if Product.objects.filter(_id=ObjectId(product_id)):
                    customer_wishlist = str(customer.wishlist).split(",")
                    if product_id in customer_wishlist:
                        return JsonResponse({"message": "Product already exists"},
                                            status=400)
                    else:
                        wishlist = customer.wishlist
                        wishlist = f"{wishlist},{product_id}" if wishlist else f"{product_id}"
                        customer.wishlist = wishlist
                        customer.save()
                        return JsonResponse({"message": "Added Successfully"},
                                            status=200)
                else:
                    return JsonResponse({"message": "Product doesn't exists"},
                                        status=400)
            else:
                return JsonResponse({"message": "Customer doesn't exists"},
                                    status=400)
        else:
            return JsonResponse({'message': "Please give Customer Id"}, status=404)


class DeleteWishlist(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user_id = (request.__dict__.get('_auth')).__dict__.get('user_id')
        customer_id = (Customer.objects.get(user_id=user_id))._id
        if customer_id:
            data = request.data
            product_id = data.get("product_id", None)

            if Customer.objects.filter(_id=customer_id):
                customer = Customer.objects.get(_id=customer_id)
                if Product.objects.filter(_id=ObjectId(product_id)):
                    if customer.wishlist:
                        customer_wishlist = customer.wishlist.split(',')
                        if product_id in customer_wishlist:
                            customer_wishlist.remove(product_id)
                            customer.wishlist = ",".join(customer_wishlist)
                            customer.save()
                            if customer.wishlist == "":
                                customer.wishlist = None
                                customer.save()
                            return JsonResponse({"message": "Deleted Successfully"},
                                                status=200)
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
        else:
            return JsonResponse({'message': "Please give Customer Id"}, status=404)


class ProductVariants(generics.GenericAPIView):
    def post(self, request):
        product_id = request.data["product_id"]
        if not product_id:
            return JsonResponse({"message": "Enter product id"}, status=400)
        else:
            product = Product.objects.get(_id=ObjectId(product_id))
            if not product:
                return JsonResponse({"message": "Product doesn't exists"}, status=400)

            else:
                data = request.data
                size = data.get("size", None)
                ean = data.get("ean", None)
                color = data.get("color", None)
                material = data.get("material", None)

                productVariant = ProductVariant(size=size, color=color, material=material, parent_product=product,
                                                ean=ean)
                productVariant.save()
                product.ean = ean
                product.save()

        return JsonResponse({"message": "Product Variant added successfully"},
                            status=200)


class Checkout(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user_id = (request.__dict__.get('_auth')).__dict__.get('user_id')
        customer_id = (Customer.objects.get(user_id=user_id))._id
        if customer_id:
            data = request.data
            product = data.get("product", {})
            if Customer.objects.filter(_id=customer_id):
                customer = Customer.objects.get(_id=customer_id)
                for product_id, qty in product.items():
                    if Product.objects.filter(_id=ObjectId(product_id)):
                        prd = Product.objects.get(_id=ObjectId(product_id))
                        product_quantity = prd.quantity
                        if qty > product_quantity:
                            return JsonResponse({"message": f"Quantity for Product {product_id} is not available"},
                                                status=400)
                        else:
                            customer_checkout = customer.checkout.split(",")
                            if product_id in customer_checkout:
                                customer_checkout_qtn = customer.checkout_quantity.split(",")
                                for i, p_id in enumerate(customer_checkout):
                                    if p_id == product_id:
                                        customer_checkout_qtn[i] = str(int(customer_checkout_qtn[i]) + qty)
                                customer_checkout_quantity = ",".join(customer_checkout_qtn)
                                customer.checkout_quantity = customer_checkout_quantity
                                customer.save()
                            else:
                                checkout = customer.checkout
                                checkout = f"{checkout},{product_id}" if checkout else f"{product_id}"
                                customer.checkout = checkout
                                checkout_qtn = customer.checkout_quantity
                                customer.checkout_quantity = f"{checkout_qtn},{qty}" if checkout_qtn else f"{qty}"
                                customer.save()
                    else:
                        return JsonResponse({"message": "Product doesn't exists"},
                                            status=400)
            else:
                return JsonResponse({"message": "Customer doesn't exists"},
                                    status=400)

            return JsonResponse({"message": "Added Successfully"},
                                status=200)
        else:
            return JsonResponse({'message': "Please give Customer Id"}, status=404)


class DeleteCheckout(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user_id = (request.__dict__.get('_auth')).__dict__.get('user_id')
        customer_id = (Customer.objects.get(user_id=user_id))._id
        if customer_id:
            data = request.data
            product_id = data.get("product_id", None)

            if Customer.objects.filter(_id=customer_id):
                customer = Customer.objects.get(_id=customer_id)
                if Product.objects.filter(_id=ObjectId(product_id)):
                    if customer.checkout:
                        customer_checkout = customer.checkout.split(',')
                        if product_id in customer_checkout:
                            customer_checkout_qtn = customer.checkout_quantity.split(',')
                            for i, p_id in enumerate(customer_checkout):
                                if p_id == product_id:
                                    customer_checkout_qtn[i] = str(int(customer_checkout_qtn[i]) - 1)
                                    customer_checkout_quantity = ",".join(customer_checkout_qtn)
                                    customer.checkout_quantity = customer_checkout_quantity
                                    customer.save()
                                    if p_id == product_id and customer_checkout_qtn[i] == "0":
                                        customer_checkout.remove(p_id)
                                        customer.checkout = ",".join(customer_checkout)
                                        customer_checkout_qtn.remove(customer_checkout_qtn[i])
                                        customer.checkout_quantity = ",".join(customer_checkout_qtn)
                                        customer.save()
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

            return JsonResponse({"message": "Deleted Successfully"},
                                status=200)
        else:
            return JsonResponse({'message': "Please give Customer Id"}, status=404)


class TotalAmount(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = (request.__dict__.get('_auth')).__dict__.get('user_id')
        customer_id = (Customer.objects.get(user_id=user_id))._id
        if customer_id:
            if Customer.objects.filter(_id=customer_id):
                data = request.data
                voucher = data.get("voucher", None)
                discount = data.get("discount", None)
                customer = Customer.objects.get(_id=ObjectId(customer_id))
                customer_checkout = customer.checkout.split(",")
                customer_checkout_qtn = customer.checkout_quantity.split(",")
                total_amount = 0
                amount = 0
                num = None
                if voucher == "" or discount:
                    for i in range(len(discount)):
                        if discount[i].isdigit():
                            num = discount[i:]
                            break
                    disc = int(num)
                    for i, product_id in enumerate(customer_checkout):
                        product = Product.objects.get(_id=ObjectId(product_id))
                        product_price = product.price
                        product_discount = int(float(product.discount))
                        price = product_price - (product_price * (product_discount / 100))
                        amount += price * int(customer_checkout_qtn[i])
                    total_amount = ("{:.2f}".format(amount - (amount * (disc / 100))))
                    customer.discount = "Expired"
                    customer.discount_value = False
                    customer.save()
                    return JsonResponse({"Total Amount": total_amount}, status=200)

                elif discount == "" or voucher:
                    if voucher == customer.voucher:
                        for i in range(len(voucher)):
                            if voucher[i].isdigit():
                                num = voucher[i:]
                                break
                        vouch = int(num)
                        for i, product_id in enumerate(customer_checkout):
                            product = Product.objects.get(_id=ObjectId(product_id))
                            product_price = product.price
                            product_discount = int(float(product.discount))
                            price = product_price - (product_price * (product_discount / 100))
                            amount += price * int(customer_checkout_qtn[i])
                        total_amount = ("{:.2f}".format(amount - (amount * (vouch / 100))))
                        customer.voucher = "Expired"
                        customer.voucher_value = False
                        customer.save()
                        return JsonResponse({"Total Amount": total_amount}, status=200)
                    else:
                        return JsonResponse({"message": "Voucher doesn't match"}, status=404)
                else:
                    for i, product_id in enumerate(customer_checkout):
                        product = Product.objects.get(_id=ObjectId(product_id))
                        product_price = product.price
                        product_discount = int(float(product.discount))
                        price = product_price - (product_price * (product_discount / 100))
                        amount += price * int(customer_checkout_qtn[i])
                    total_amount = ("{:.2f}".format(amount))
                return JsonResponse({"Total Amount": total_amount}, status=200)
            else:
                return JsonResponse({'message': "Customer Id does not exists"}, status=404)
        else:
            return JsonResponse({'message': "Please give Customer Id"}, status=404)


class GuestLogin(generics.GenericAPIView):
    def post(self, request):
        data = request.data
        first_name = data.get("first_name", None)
        last_name = data.get("last_name", None)
        email = data.get("email", None)

        if not first_name or not last_name or not email:
            return JsonResponse({"message": "Please provide full details"}, status=500)
        if first_name == "" or last_name == "" or email == "":
            return JsonResponse({"message": "Please enter correct details"},
                                status=200)
        else:
            user_email = User.objects.filter(email=email)

            if user_email:
                user = User.objects.get(email=user_email[0])
                customer_id = user.id
                email = User.objects.filter(email=email)[0]
                token = get_access_token(email)
                return JsonResponse({"message": "Email_Id already exists", "token": token, "customer_id": customer_id},
                                    status=200)
            else:
                try:
                    username = email
                    user = User.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        username=username,
                    )
                    token = get_access_token(user)
                    customer = Customer.objects.create(user=user, first_name=first_name, last_name=last_name,
                                                       email=email,
                                                       guest_login=True)
                    customer.save()
                    customer_id = str(customer.user_id)

                    return JsonResponse({"message": "Successfully Logged In", "token": token, "customer": customer_id},
                                        status=200)
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


class UserUpdatePassword(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user_id = (request.__dict__.get('_auth')).__dict__.get('user_id')
        customer_id = (Customer.objects.get(user_id=user_id))._id
        if customer_id:
            data = request.data
            password = data.get("password", None)
            confirm_password = data.get("confirm_password", None)

            if password != confirm_password:
                return JsonResponse({"message": "Password doesn't match"},
                                    status=406)
            else:
                if Customer.objects.filter(_id=customer_id):
                    customer = Customer.objects.get(_id=customer_id)
                    user_id = customer.user_id
                    user = User.objects.get(id=user_id)
                    if user.password:
                        return JsonResponse({"message": "Password already stored"},
                                            status=403)
                    else:
                        user.password = make_password(confirm_password)
                        user.save()
                        customer.guest_login = False
                        customer.save()
                        return JsonResponse({"message": "Password stored successfully"},
                                            status=200)
                else:
                    return JsonResponse({"message": "Customer doest not exists"},
                                        status=400)
        else:
            return JsonResponse({'message': "Please give Customer Id"}, status=404)
