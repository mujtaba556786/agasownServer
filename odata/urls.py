from django.conf.urls import url

from .sitemaps import *
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include

from rest_framework import routers
from rest_framework.routers import SimpleRouter, Route
from odata.views.apis import (
    ProductViewSet,
    CustomerViewSet,
    CategoryViewSet,
    PaymentViewset,
    NewsLetterViewSet,
    Wishlist,
    DeleteWishlist,
    ProductVariants,
    Checkout,
    DeleteCheckout,
)
from odata.views.accounts import (
    LoginViewSet,
    SignupViewSet,
    LogoutViewSet,
    UserForgotPassword,
    VerifyUserForgotPassword,
    ResetPassword,
)
from odata.views.pg_stripe import (
    CreateCheckoutSession,
    StipeCheckoutSession,
    StripeCard,
    StripSofort,
    # StripeWebHookView,
    success,

)
from odata.views.paypal import Paypal

# from odata.views.reset_password import PasswordTokenCheck

viewset_dict = {
    "get": "list",
    "post": "create",
    "get": "retrieve",
    "put": "update",
    "patch": "partial_update",
    "delete": "destroy",
}


class CustomSimpleRouter(SimpleRouter):
    routes = [
        # List route
        Route(
            url=r"^{prefix}{trailing_slash}$",
            mapping={
                "get": "list",
                "post": "create",
                "put": "bulk_update",
                # "delete": "destroy",
            },
            name="{basename}-list",
            detail=False,
            initkwargs={"suffix": "List"},
        ),
        # Detail route
        Route(
            url=r"^{prefix}/{lookup}{trailing_slash}$",
            mapping={
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            },
            name="{basename}-detail",
            detail=False,
            initkwargs={"suffix": "Instance"},
        ),
    ]


router = CustomSimpleRouter()
product_list = ProductViewSet.as_view(viewset_dict)
customer_list = CustomerViewSet.as_view(viewset_dict)
category_list = CategoryViewSet.as_view(viewset_dict)

router = routers.DefaultRouter()
# router.register(r'products', ProductViewSet, r"tool")

sitemaps_dict = {
    # 'category' : Category_Sitemap,
    "product": Product_Sitemap,
    # 'order' : Order_Sitemap,
}

router.register(r"products", ProductViewSet),
# router.register(r"payments", PaymentViewset),
# router.register(r"products/image", ProductImageViewSet),
# router.register(r"products/variant", ProductVariantViewSet),
router.register(r"newsletter", NewsLetterViewSet),
router.register(r"customers", CustomerViewSet),
router.register(r"category", CategoryViewSet),
router.register(r"login", LoginViewSet, basename="login")
router.register(r"logout", LogoutViewSet, basename="logout")
router.register(r"sign-up", SignupViewSet, basename="sign-up")
# router.register(
#     r"forgot-password", UserForgotPasswordViewSet, basename="request-reset-email"
# )
# router.register(
#     r"verify-forgot-password/<uidb64>/token",
#     VerifyUserForgotPasswordViewSet,
#     basename="password-reset-confirm",
# )
# router.register(r"reset-password", ResetPasswordViewSet, basename="reset-password")
urlpatterns = [
                  url(r'^api/', include(router.urls)),
                  path(
                      "sitemap.xml",
                      sitemap,
                      {"sitemaps": sitemaps_dict},
                      name="django.contrib.sitemaps.views.sitemap",
                  ),
                  path("", include(router.urls)),
                  path("stripe/", StripeCard.as_view()),
                  path("stripe/sofort/", StripSofort.as_view()),
                  path("stripe/check-out", StipeCheckoutSession.as_view()),
                  path("stripe/create-checkout", CreateCheckoutSession.as_view()),
                  # path("stripe/webhook", StripeWebHookView.as_view()),
                  path("stripe/success", success),
                  path("paypal/payment/", Paypal.as_view()),
                  path("request_reset_email/", UserForgotPassword.as_view(), name="request_reset_email"),
                  path("<uidb64>/<token>/", VerifyUserForgotPassword.as_view(),
                       name='password_reset_confirm'),
                  path("reset_password/", ResetPassword.as_view()),
                  path('wishlist/', Wishlist.as_view()),
                  path('wishlist/delete', DeleteWishlist.as_view()),
                  path('product/variant', ProductVariants.as_view()),
                  path('checkout/', Checkout.as_view()),
                  path('delete/checkout/', DeleteCheckout.as_view()),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
