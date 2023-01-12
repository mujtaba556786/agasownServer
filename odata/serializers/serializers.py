from django.contrib.auth.models import User
from django.forms import fields
from rest_framework import request, serializers
from odata.models import (
    Product,
    Customer,
    Categories,
    ProductImage,
    ProductVariant,
    NewsletterSubscription,
    Payment,
)


class ProductImageSerializers(serializers.ModelSerializer):
    # image_url = serializers.SerializerMethodField("get_image_url")

    class Meta:
        model = ProductImage
        fields = ("image_order", "image", "product")

    # def get_image_url(self, obj):
    #     request = self.context.get("request")
    #     image_url = obj.image.url
    #     return request.build_absolute_uri(image_url)
    def to_representation(self, instance):
        rep = super(ProductImageSerializers, self).to_representation(instance)
        rep["product"] = str(rep["product"])
        return rep


class ProductVariantSerializers(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = "__all__"

    def to_representation(self, instance):
        rep = super(ProductVariantSerializers, self).to_representation(instance)
        rep["parent_product"] = str(rep["parent_product"])
        return rep


class ProductSerializers(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"

    def to_representation(self, instance):
        """
        Change in the response of api
        """
        rep = super(ProductSerializers, self).to_representation(instance)
        product_image = ProductImage.objects.filter(product=instance).order_by("-_id")
        product_variant = ProductVariant.objects.filter(
            parent_product=instance
        ).order_by("-_id")
        rep["product_image"] = ProductImageSerializers(
            product_image, many=True, context={"request": self.context.get("request")}
        ).data
        rep["product_variant"] = ProductVariantSerializers(
            product_variant, many=True
        ).data

        return rep


class NewsLetterSerializers(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscription
        fields = "__all__"


class CustomerSerializers(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False
    )
    username = serializers.CharField(max_length=100)
    email = serializers.EmailField()

    class Meta:
        model = Customer
        exclude = ("created_at", "updated_at")

    def create(self, validated_data):
        username = validated_data.pop("username")
        email = validated_data.pop("email")
        user = User.objects.create(
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            email=email,
            username=username,
        )
        customer = Customer.objects.create(user=user, first_name=validated_data["first_name"],
                                           last_name=validated_data["last_name"],
                                           email=email,
                                           address1=validated_data.get("address1"),
                                           address2=validated_data.get("address2"),
                                           city=validated_data.get("city"),
                                           state=validated_data.get("state"),
                                           postal_code=validated_data.get("postal_code"),
                                           country=validated_data.get("country"),
                                           phone=validated_data.get("phone"),
                                           salutation=validated_data.get("salutation"),
                                           credit_card=validated_data.get("credit_card"),
                                           credit_card_type_id=validated_data.get("credit_card_type_id"),
                                           mm_yy=validated_data.get("mm_yy"),
                                           billing_address=validated_data.get("billing_address"),
                                           billing_city=validated_data.get("billing_city"),
                                           billing_postal_code=validated_data.get("billing_postal_code"),
                                           billing_country=validated_data.get("billing_country"),
                                           ship_address=validated_data.get("ship_address"),
                                           ship_city=validated_data.get("ship_city"),
                                           ship_region=validated_data.get("ship_region"),
                                           ship_postal_code=validated_data.get("ship_postal_code"),
                                           ship_country=validated_data.get("ship_country"),
                                           marketing_code=validated_data.get("marketing_code"),
                                           source=validated_data.get("source"),
                                           wishlist=validated_data.get("wishlist"),
                                           checkout=validated_data.get("checkout"),
                                           medium=validated_data.get("medium"),
                                           gcustid=validated_data.get("gcustid"),
                                           gclid=validated_data.get("gclid"),
                                           fbclid=validated_data.get("fbclid"),
                                           date_entered=validated_data.get("date_entered"),
                                           terms_condition=validated_data.get("terms_condition"),
                                           data_privacy=validated_data.get("data_privacy"),
                                           voucher="welcome10",
                                           voucher_value=True,
                                           guest_login=False,
                                           )

        return Customer.objects.get(user=user)

    def validate(self, validated_data):
        if 'username' in validated_data or 'email' in validated_data:
            username = validated_data["username"]
            email = validated_data["email"]
            if User.objects.filter(username=username):
                if User.objects.filter(email=email):
                    raise serializers.ValidationError(
                        {"email": "Email is already registered with us"}
                    )
                raise serializers.ValidationError(
                    {"username": "Username is already registered with us"}
                )
            return validated_data
        else:
            return validated_data

    def to_representation(self, instance):
        instance.username = instance.user.username
        instance.email = instance.user.email
        rep = super(CustomerSerializers, self).to_representation(instance)
        rep["username"] = instance.user.username
        rep["email"] = instance.user.email
        return rep


class CategorySerializers(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = "__all__"

    def to_representation(self, instance):
        rep = super(CategorySerializers, self).to_representation(instance)
        rep["parent"] = str(rep["parent"])
        return rep


class PaymentSerializers(serializers.ModelSerializer):
    """
    Payment serializer
    """

    class Meta:
        """Paymet meta class"""

        model = Payment
        fields = "__all__"

    def to_representation(self, instance):
        rep = super(PaymentSerializers, self).to_representation(instance)
        rep["customer"] = str(rep["customer"])
        return rep
