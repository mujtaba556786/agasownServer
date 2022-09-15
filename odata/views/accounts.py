"""Accounts auth API"""

# third party import
from django.contrib.auth.models import User
from rest_framework import mixins, generics
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, JsonResponse

# local import
from odata.utility.helpers import ApiResponse, get_message, logout
from odata.utility.messages import ERROR_CODE, SUCCESS_CODE
from odata.serializers.auth_serializer import (
    LoginSerializer,
    CustomerRegistrationSerializer,
    UserForgotPasswordSerializer,
    # VerifyUserForgotPasswordSerializer,
    SetNewResetPasswordSerializer
)

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.core.mail import send_mail
from Project.settings import EMAIL_HOST_USER
from odata.serializers.auth_serializer import SetNewResetPasswordSerializer


class LoginViewSet(viewsets.ModelViewSet, ApiResponse):
    """
    Login Model View-set
    """

    serializer_class = LoginSerializer
    queryset = User.objects.all()
    http_method_names = ["post"]

    def get_serializer_context(self):
        """
        Serializer Context
        :return: context
        """
        return {"request": self.request}


class LogoutViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, ApiResponse):
    """
    Logout view is used for user logout.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = None
    http_method_names = ("post",)

    def create(self, request, *args, **kwargs):
        """
        :param request: request user
        :param args: argument list
        :param kwargs: keyword argument object
        :return: logout a user
        """
        logout(request.user.id, request.META["HTTP_AUTHORIZATION"].split(" ")[1])
        return self.custom_response(
            message=SUCCESS_CODE["user"]["log_out"],
            data=None,
            response_status=status.HTTP_200_OK,
        )


class SignupViewSet(viewsets.ModelViewSet, ApiResponse):
    """
    Signup ViewSet for customers
    """

    queryset = User.objects.all()
    serializer_class = CustomerRegistrationSerializer
    http_method_names = ("post",)

    def create(self, request, **kwargs):
        """
            Creating a customer
        :param request: wsgi request
        :param kwargs: allows for any number of keyword arguments (parameters) which will be dict named keyword
        :return: Created user instance

        signup request body
        {
        "first_name" : "test",
        "last_name" : "test",
        "email" : "test@yopmail.com",
        "password" : "Qwerty@1",
        }

        """

        user_create_serializer_instance = self.serializer_class(
            data=request.data,
            context={"confirm_password": request.data.get("confirm_password")},
        )
        if user_create_serializer_instance.is_valid():
            user_create_serializer_instance.save()
            return self.custom_response(
                SUCCESS_CODE["user"]["registration_done"],
                user_create_serializer_instance.data,
                response_status=status.HTTP_201_CREATED,
            )

        return self.custom_error(
            get_message(user_create_serializer_instance.errors),
            response_status=status.HTTP_400_BAD_REQUEST,
        )


class UserForgotPassword(generics.GenericAPIView):
    """
    forgot password
    """

    serializer_class = UserForgotPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        email = request.data['email']

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            current_site = get_current_site(request=request).domain
            relativeLink = reverse('password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})
            absurl = 'http://' + current_site + relativeLink
            email_body = 'Hi \n Use this link to reset your password \n' + absurl
            send_mail(subject='Reset your Password',
                      message=email_body,
                      from_email=EMAIL_HOST_USER,
                      recipient_list=[email],
                      fail_silently=False)
            return JsonResponse({'success': 'We have have a  sent a link to reset password on your e-mail'},
                                status=200)
        else:
            return JsonResponse({'message': 'User does not exists'},
                                status=400)


class VerifyUserForgotPassword(generics.GenericAPIView, ApiResponse):
    def get(self, request, uidb64, token):

        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return JsonResponse({'error': 'Token expired, request a new one'},
                                    status=401)

            return JsonResponse({'success': True, 'message': 'Credentials valid', 'uidb64': uidb64, 'token': token},
                                status=200)

        except DjangoUnicodeDecodeError as identifier:
            if not PasswordResetTokenGenerator():
                return HttpResponse({'error': 'Token is not valid'},
                                    status=401)


class ResetPassword(generics.GenericAPIView, ApiResponse):
    """
    Class to reset password
    """
    serializer_class = SetNewResetPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return JsonResponse({'success': True,
                             'message': 'Password reset successfully'},
                            status=200)
