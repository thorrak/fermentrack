# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task


# Note - Celery is being installed/set up, but the functionality will remain latent for the time being. The plan is to
# use it to create tasks later that run independent from user input (such as controller montioring, etc.)

@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)