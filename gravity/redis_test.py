import redis
import json
# import gravity.models
# from django.core import serializers

if __name__ == "__main__":
    r = redis.Redis(host="127.0.0.1", port=6379, password='')

    r.set('test_key', 'value'.encode(encoding="utf-8"))

    print r.get('test_key'.decode(encoding="utf-8"))
