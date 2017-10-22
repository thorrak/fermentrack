import redis
import json
# import gravity.models
# from django.core import serializers


r = redis.Redis(host="127.0.0.1", port=6379, password='')





r.set('test_key', 'value')




print r.get('test_key')
