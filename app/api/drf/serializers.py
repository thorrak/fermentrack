from django.contrib.auth.models import User, Group
from rest_framework import serializers
from app.models import Beer
from rest_framework.fields import CurrentUserDefault
from datetime import datetime
from rest_framework_jwt.settings import api_settings
from calendar import timegm


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'id', 'username', 'first_name', 'last_name', 'email')


class BeerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Beer
        fields = ('name', 'device')


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
