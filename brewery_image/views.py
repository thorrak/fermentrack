from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import BreweryLogoForm
from .models import BreweryLogo

#This isn't working right
def brewery_image(request):

    if request.method == 'POST':
        form = BreweryLogoForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect('success')

        else:
            form = BreweryLogoForm()
        return render(request, 'brewery_image_form.html', {'form' : form})

def index(request):
        return HttpResponse ('successfully uploaded')

#The only view that works http://ip/brewery_image
def display_brewery_images(request):

    if request.method == 'GET':

        # getting all the objects of image
        Images = BreweryLogo.objects.all()
        return render(request, 'display_brewery_images.html', {'brewery_images' : Images})
