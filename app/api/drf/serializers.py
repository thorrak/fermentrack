from django.contrib.auth.models import User, Group
from rest_framework import serializers
from app.models import Beer, BrewPiDevice, FermentationProfile, FermentationProfilePoint, BeerLogPoint
from rest_framework.fields import CurrentUserDefault
from datetime import datetime
from rest_framework_jwt.settings import api_settings
from calendar import timegm


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
    class Meta:
        model = BrewPiDevice
        fields = '__all__'

class FermentationProfilePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = FermentationProfilePoint
        fields = '__all__'

class BeerLogPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeerLogPoint
        fields = '__all__'

class FermentationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FermentationProfile
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
