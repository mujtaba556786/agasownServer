
from .serializers import MyTokenObtainPairSerializer
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from .serializers import RegisterSerializer
from rest_framework.response import Response
from rest_framework import generics


class MyObtainTokenPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = MyTokenObtainPairSerializer
    
    http_method_names = ['get', 'head']
    def get(self, request, format=None):
            users = User.objects.all()
            serializer = MyTokenObtainPairSerializer(users, many=True)
            return Response(serializer.data)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all() 
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer