"""Project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.views.generic import TemplateView
from rest_framework import permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from django.contrib import admin
from django.urls import path, include, re_path

from rest_framework import routers
from rest_framework.routers import DefaultRouter
from odata.views import ProductViewSet
from django.conf import settings
from django.conf.urls.static import static
router = routers.DefaultRouter()
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions


from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from users import views as user_views
from payments import views as payment_views
from django.contrib.auth import views as auth_views


schema_view = get_schema_view(
   openapi.Info(
      title="O-DATA API",
      default_version='v1',
      description="O-DATA Api docs confidentails",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="odata@mongodb.api.com"),
      license=openapi.License(name="O-Data License"),
   ),
   public=True,   
   permission_classes=(permissions.AllowAny,)
)
   

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html')),


    path('register/', user_views.register, name='register'),
    path('welcome/', user_views.welcome, name='welcome'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    
    path('payments/', payment_views.checkout, name='payments'),
    path('charge/', payment_views.charge, name='charge'),

    path('auth/', include('auth.urls')),
    path('api/customers/', include('api.customers.urls')),
    #path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    #path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include('odata.urls')),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
