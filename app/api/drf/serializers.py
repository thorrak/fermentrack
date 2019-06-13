from django.contrib.auth.models import User, Group
from rest_framework import serializers
from app.models import Beer, BrewPiDevice, FermentationProfile, FermentationProfilePoint, BeerLogPoint
from rest_framework.fields import CurrentUserDefault
from datetime import datetime
from rest_framework_jwt.settings import api_settings
from calendar import timegm

import json

class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'id', 'username', 'first_name', 'last_name', 'email', 'password')

    def create(self, validated_data):
        # create user 
        user = User.objects.create_user(
            username = validated_data['username'],
            password = validated_data['password'],
            first_name = validated_data['first_name'],
            email = validated_data['email'],
	    last_name = validated_data['last_name'], 
        )
        return user
        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'id', 'username', 'first_name', 'last_name', 'email')


class BeerSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = Beer
        fields = '__all__'



class BrewPiDeviceSerializer(serializers.ModelSerializer):

    active_beer_name = serializers.SerializerMethodField()
    #controller_beer_data = serializers.SerializerMethodField()
    controller_fridge_temp = serializers.SerializerMethodField() 
    controller_beer_temp = serializers.SerializerMethodField() # get from live LCD data, 
    active_beer_temp = serializers.SerializerMethodField()  
    active_fridge_temp = serializers.SerializerMethodField() 
    active_beer_set = serializers.SerializerMethodField()  
    active_fridge_set = serializers.SerializerMethodField() 
    controller_mode = serializers.SerializerMethodField() 

    #start_new_brew = serializers.SerializerMethodField()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'request' in self.context and self.context['request'].method == 'POST':
            start_new_brew = serializers.SerializerMethodField()

    class Meta:
        model = BrewPiDevice
        fields = ('id', 'device_name', 'logging_status', 'active_beer', 'active_beer_name', 'controller_fridge_temp', 'controller_beer_temp', 'active_beer_temp', 'active_fridge_temp', 'active_beer_set', 'active_fridge_set', 'controller_mode')
   
    # Update Device active_beer and start logging tha same beer

    def update(self, instance, validated_data):
        # Update the Foo instance
        instance.active_beer = validated_data['active_beer']
        #beer_name = instance.active_beer.name
        instance.save()
        #instance.send_message("startNewBrew", message_extended=beer_name, read_response=True)
        return instance 

    def get_active_beer_name(self, obj):
        if obj.active_beer:   
            return obj.active_beer.name
        else:
            return ""
    
    def start_new_brew(self, obj):
        try:
            beer_name = obj.active_beer.name
            data = obj.send_message("startNewBrew", extended_message=beer_name, read_response=True)
            return data
	#else 
	 #   return False
        except TypeError:
            return None 
    
    def get_controller_fridge_temp(self, obj):
        try:  
            data = json.loads(obj.send_message("lcd", read_response=True))
            return data[2]
        except TypeError:
            return None 
     
    def get_controller_beer_temp(self, obj):
        try:  
            data = json.loads(obj.send_message("lcd", read_response=True))
            return data[1]
        except TypeError:
            return None  
    
 #   def get_controller_beer_data(self, obj):
  #      try:  
   #         return json.loads(obj.send_message("getDashInfo", read_response=True))
    #    except TypeError:
     #       return None 

    def get_active_beer_temp(self, obj):
        try:  
            data = json.loads(obj.send_message("getDashInfo", read_response=True))
            return data['BeerTemp'] 
        except TypeError:
            return None 

    def get_active_fridge_temp(self, obj):
        try:  
            data = json.loads(obj.send_message("getDashInfo", read_response=True))
            return data['FridgeTemp'] 
        except TypeError:
            return None 

    def get_active_beer_set(self, obj):
        try:  
            data = json.loads(obj.send_message("getDashInfo", read_response=True))
            return data['BeerSet'] 
        except TypeError:
            return None 

    def get_active_fridge_set(self, obj):
        try:  
            data = json.loads(obj.send_message("getDashInfo", read_response=True))
            return data['FridgeSet'] 
        except TypeError:
            return None 

    def get_controller_mode(self, obj):
        try:  
            data = json.loads(obj.send_message("getDashInfo", read_response=True))
            return data['Mode'] 
        except TypeError:
            return None 



class BeerLogPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeerLogPoint
        fields = '__all__'

class FermentationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FermentationProfile
        fields = '__all__'

class FermentationProfilePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = FermentationProfilePoint
        fields = '__all__'

# custom payload for JWT token response 

#def jwt_response_payload_handler(token, user=None, request=None):
#    return {
#        'user': UserSerializer(user, context={'request': request}).data),
#        'token' : token
#    }


def jwt_payload_handler(user):
    """ Custom payload handler
    Token encrypts the dictionary returned by this function, and can be decoded by rest_framework_jwt.utils.jwt_decode_handler
    """
    return {
        'user_id': user.pk,
        'email': user.email,
        'first_name' : user.first_name,
        'last_name' : user.last_name,
        'is_superuser': user.is_superuser,
        'exp': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA,
        'orig_iat': timegm(
            datetime.utcnow().utctimetuple()
        )
    }

def jwt_response_payload_handler(token, user=None, request=None):
    """ Custom response payload handler.

    This function controlls the custom payload after login or token refresh. This data is returned through the web API.
    """
    return {
        'token' : token,
        'first_name' : user.first_name,
        'id' : user.id,
        'email': user.email,
        'last_name' : user.last_name
    }    
