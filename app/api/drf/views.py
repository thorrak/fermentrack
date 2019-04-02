from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from app.api.drf.serializers import CreateUserSerializer, UserSerializer, BeerSerializer, BrewPiDeviceSerializer, FermentationProfileSerializer, FermentationProfilePointSerializer, BeerLogPointSerializer
from app.models import Beer, BrewPiDevice, FermentationProfile, FermentationProfilePoint, BeerLogPoint
from rest_framework import generics

class CreateUserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be created
    """
    permission_classes = [AllowAny,]
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = CreateUserSerializer
    http_method_names = ['post']

    def post(self, request, format=None):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed 
    """
    
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class BeerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    permission_classes = [IsAuthenticated,]
    queryset = Beer.objects.all()
    serializer_class = BeerSerializer

class BrewPiDeviceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    permission_classes = [IsAuthenticated,]
    queryset = BrewPiDevice.objects.all()
    serializer_class = BrewPiDeviceSerializer

class FermentationProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    permission_classes = [IsAuthenticated,]
    queryset = FermentationProfile.objects.all()
    serializer_class = FermentationProfileSerializer

class FermentationProfilePointViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    permission_classes = [IsAuthenticated,]
    queryset = FermentationProfilePoint.objects.all()
    serializer_class = FermentationProfilePointSerializer

class BeerLogPointViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    permission_classes = [IsAuthenticated,]
    queryset = BeerLogPoint.objects.all()
    serializer_class = BeerLogPointSerializer



