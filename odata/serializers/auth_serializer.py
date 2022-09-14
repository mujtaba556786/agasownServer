"""Auth Serializer"""

# third party imports
import re, random
from datetime import datetime

from django.db.models import Q
from django.conf import settings
from django.db import transaction
from django.core.mail import send_mail
from django.contrib.auth.models import User

from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

# local imports
from odata.models import UserForgotPassword, Customer
from odata.utility.constant import SPECIAL_CHARACTERS
from odata.utility.validator import USER_UNIQUE_FIELD_VALIDATOR
from odata.utility.messages import ERROR_CODE, ErrorManager, SUCCESS_CODE
from odata.utility.helpers import (
    ApiResponse,
    get_access_token,
    validate_password,
    validate_name,
)
from django.core.mail import EmailMessage
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


class LoginSerializer(serializers.ModelSerializer, ApiResponse):
    """
    Serializer for login process.
    """

    email = serializers.EmailField(
        required=True,
        error_messages={"blank": ErrorManager().get_blank_field_message("email")},
    )
    password = serializers.CharField(
        max_length=100,
        required=True,
        trim_whitespace=False,
        error_messages={"blank": ErrorManager().get_blank_field_message("password")},
    )
    token = serializers.SerializerMethodField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    class Meta:
        """
        Meta class for serializer
        """

        model = User
        fields = ("id", "email", "password", "token", "first_name", "last_name")

    def validate_data(self, validated_data):
        """

        :param validated_data:
        :return:
        """
        email = validated_data.get("email", None)
        password = validated_data.get("password", None)

        try:
            user = User.objects.get(Q(email__iexact=email) | Q(username__iexact=email))
        except User.DoesNotExist:
            self.custom_validate_error(message=ERROR_CODE["user"]["not_exist"])

        if not user.is_active:
            self.custom_validate_error(message=ERROR_CODE["login"]["deactive"])

        if not user.check_password(password):
            self.custom_validate_error(
                message=ERROR_CODE["login"]["invalid_credential"]
            )

        return user

    def create(self, validated_data):
        """

        :param validated_data:
        :return:
        """
        user = self.validate_data(validated_data)
        return user

    @staticmethod
    def get_token(obj):
        """
        Get token
        :return:
        """
        return get_access_token(obj)

    def to_representation(self, obj):
        """
        get the original representation
        :param obj: account instance
        :return: modified account instance
        """
        attr = super(LoginSerializer, self).to_representation(obj)
        attr.pop("password")
        return attr


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """

    first_name = serializers.CharField(
        required=True,
        max_length=50,
        error_messages={
            "blank": ErrorManager().get_blank_field_message("first_name"),
            "max_length": ErrorManager().get_maximum_limit_message("first_name", "50"),
        },
    )
    last_name = serializers.CharField(
        required=True,
        max_length=50,
        error_messages={
            "blank": ErrorManager().get_blank_field_message("last_name"),
            "max_length": ErrorManager().get_maximum_limit_message("first_name", "50"),
        },
    )
    email = serializers.EmailField(
        required=True,
        max_length=150,
        min_length=5,
        error_messages={
            "blank": ErrorManager().get_blank_field_message("Email"),
            "max_length": ErrorManager().get_maximum_limit_message("Email", "150"),
            "min_length": ErrorManager().get_minimum_limit_message("Email", "5"),
            "invalid": ERROR_CODE["sign_up"]["invalid_email"],
        },
    )
    password = serializers.CharField(
        required=True,
        max_length=15,
        min_length=8,
        error_messages={
            "blank": ErrorManager().get_blank_field_message("password"),
            "min_length": ErrorManager().get_minimum_limit_message("password", "8"),
            "max_length": ErrorManager().get_maximum_limit_message("password", "15"),
        },
    )
    confirm_password = serializers.CharField(
        max_length=15,
        min_length=8,
        error_messages={
            "blank": ErrorManager().get_blank_field_message("password"),
            "min_length": ErrorManager().get_minimum_limit_message("password", "8"),
            "max_length": ErrorManager().get_maximum_limit_message("password", "15"),
        },
        read_only=True,
    )

    class Meta:
        """
        Meta class for serializer
        """

        model = User
        fields = ("first_name", "last_name", "email", "password", "confirm_password")
        validators = USER_UNIQUE_FIELD_VALIDATOR

    @staticmethod
    def validate_email(value):
        """
        validate email
        :param value: email
        :return: validated email
        """
        return value.lower()

    @staticmethod
    def validate_password(password):
        """
        Method to validate user password
        """
        return validate_password(password)

    def validate(self, data):
        """

        :param data: obj
        :return: data
        """
        if data.get("password") != self.context.get("confirm_password"):
            raise serializers.ValidationError(
                ERROR_CODE["password"]["confirm_password_invalid"]
            )
        regex = re.compile(SPECIAL_CHARACTERS)
        validate_name([data.get("first_name"), data.get("last_name")])

        return data

    @staticmethod
    def create(validated_data):
        """
            Method to create user
        :param validated_data: ordered dict that has key - value pair of account attribute
        :return: create account instance
        """
        with transaction.atomic():
            validated_data["is_active"] = True
            validated_data["username"] = validated_data["email"]
            instance = User.objects.create(**validated_data)
            instance.set_password(validated_data["password"])
            instance.save()
            Customer.objects.create(
                user=instance,
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
            )

        return instance

    def to_representation(self, instance):
        rep = super(CustomerRegistrationSerializer, self).to_representation(instance)
        rep.pop("password")
        return rep


class UserForgotPasswordSerializer(serializers.Serializer):
    """
    forgot password serializer.
    """

    email = serializers.EmailField(min_length=2)

    class Meta:
        fields = ['email']


class SetNewResetPasswordSerializer(serializers.Serializer):
    """
    Reset password serializer.
    """
    password = serializers.CharField(min_length=6, max_length=20, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)
    uidb64 = serializers.CharField(min_length=1, write_only=True)

    class Meta:
        fields = ['password', 'token', 'uidb64']

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('The reset link is invalid', 401)

            user.set_password(password)
            user.save()

        except Exception as e:
            raise AuthenticationFailed('The reset link is invalid', 401)

        return super().validate(attrs)
