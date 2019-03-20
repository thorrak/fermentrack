from django.contrib.auth.models import User, Group
from rest_framework import serializers
from app.models import Beer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class BeerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Beer
        fields = ('name', 'device')
