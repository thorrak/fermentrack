# Create your tasks here
from __future__ import absolute_import, unicode_literals
from huey.contrib.djhuey import periodic_task, task, db_periodic_task, db_task

# Note - Huey is being installed/set up, but the functionality will remain latent for the time being. The plan is to
# use it to create tasks later that run independent from user input (such as controller montioring, etc.)

@task
def add(x, y):
    return x + y


@task
def mul(x, y):
    return x * y


@task
def xsum(numbers):
    return sum(numbers)