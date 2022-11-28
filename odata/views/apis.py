from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from bson import ObjectId
from rest_framework.views import APIView
from django.db import connection

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
        return self.model.objects.get(pk=ObjectId(self.kwargs.get('pk')))

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
        return self.model.objects.get(pk=ObjectId(self.kwargs.get('pk')))


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
        
        return self.model.objects.get(pk=ObjectId(self.kwargs.get('pk')))


class CustomerViewSet(viewsets.ModelViewSet):
    """This viewset is used for crud operations"""

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializers

    # permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.model.objects.get(pk=ObjectId(self.kwargs.get('pk')))


class CategoryViewSet(viewsets.ModelViewSet):
    """This viewset is used for crud operations"""

    queryset = Categories.objects.all()
    serializer_class = CategorySerializers

    def get_object(self):
        return self.model.objects.get(pk=ObjectId(self.kwargs.get('pk')))


class PaymentViewset(viewsets.ModelViewSet):
    """
    This viewset is used for crud operation
    """

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializers
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.model.objects.get(pk=ObjectId(self.kwargs.get('pk')))


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
