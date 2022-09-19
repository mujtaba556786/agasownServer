from django.http import HttpResponse
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from bson import ObjectId

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


class ProductVariantViewSet(viewsets.ModelViewSet):
    """This viewset is used for crud operations"""

    model = ProductVariant
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializers

    def get_object(self):
        return self.model.objects.get(pk=ObjectId(self.kwargs.get('pk')))


class NewsLetterViewSet(viewsets.ModelViewSet):
    """This viewset is used for crud operations"""

    queryset = NewsletterSubscription.objects.all()
    serializer_class = NewsLetterSerializers
    permission_classes = [IsAuthenticated]

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
        print(customer_id)
        print(product_id)

        cus_objInstance = ObjectId(customer_id)
        product_objInstance = ObjectId(product_id)

        if Customer.objects.filter(_id=cus_objInstance):
            customer = Customer.objects.get(_id=cus_objInstance)
            print(customer.first_name)
            if Product.objects.filter(_id=product_objInstance):
                product = Product.objects.get(_id=product_objInstance)
                print(product._id)
                print(type(customer.wishlist))
                # customer.wishlist.append(product._id)
                customer.wishlist = product._id
                print("*** reached here")
                # customer.wishlist = [product._id]
                # print(customer.wishlist)
                # Customer(wishlist=product)
                customer.save()

        else:
            return HttpResponse("Else", 500)
        return HttpResponse("success", 200)
