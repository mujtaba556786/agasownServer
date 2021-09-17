from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view  , permission_classes

from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework import generics
from django.shortcuts import render
from rest_framework import viewsets
from django.http import HttpResponse , JsonResponse
from django.views.generic import ListView
from odata.models import ( Customer )

from api.customers.serializers import CustomerSerializer

from odata.serializers import (
    CustomerSerializers
)
# Create your views here.

@api_view(['GET', ])
@permission_classes((IsAuthenticated, ))
def ProfileView(request, id):
    """ Get Customer By User """
    try:
        customer = Customer.objects.get(id=id)
    except Customer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CustomerSerializer(customer)
        return Response(serializer.data)

