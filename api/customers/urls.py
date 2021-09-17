
from django.urls import path
from api.customers.views import ProfileView

app_name = 'customer'

urlpatterns = [
    path('profile/<id>', ProfileView , name='api_customers_profiles'),
]