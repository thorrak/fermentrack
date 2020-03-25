from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import BreweryLogoForm
from .models import BreweryLogo

#The view that works http://ip/image
def display_brewery_images(request):

    if request.method == 'GET':

        # getting all the objects of image
        Images = BreweryLogo.objects.all()
        return render(request, 'display_brewery_images.html', {'brewery_images' : Images})
        
