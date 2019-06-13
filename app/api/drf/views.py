from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.decorators import api_view
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
    API endpoint that allows users to be viewed or edited.
    """
    permission_classes = [IsAuthenticated,]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class BeerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    permission_classes = [IsAuthenticated,]
    queryset = Beer.objects.all()
    serializer_class = BeerSerializer
    http_method_names = ['get','update', 'post']
    

    	#if request.method == 'POST':

    #@api_view(['GET', 'POST'])
    #def hello_world(request):
    #	if request.method == 'POST':
    #    	return Response({"message": "Got some data!", "data": request.data})
    #	return Response({"message": "Hello, world!"})


class BrewPiDeviceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows brewpidevices to be viewd and created.
    """
    permission_classes = [IsAuthenticated,]
    queryset = BrewPiDevice.objects.all()
    serializer_class = BrewPiDeviceSerializer
    http_method_names = ['get','update', 'put', 'post']
 
    #def post(self, request, format=None):
    #    serializer = BrewPiDeviceSerializer(data=request.data)
    #    if serializer.is_valid():
    #        serializer.save()
    #        return Response(serializer.data, status=status.HTTP_201_CREATED)
    #    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    #def update(self, request, *args, **kwargs):
    #    instance = self.get_object()
    #    instance.active_beer = request.data.get("active_beer")
    #    instance.save()

     #   serializer = self.get_serializer(instance)
      #  serializer.is_valid(raise_exception=True)
       # self.perform_update(serializer)

        #return Response(serializer.data)


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



