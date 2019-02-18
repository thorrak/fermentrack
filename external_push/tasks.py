# Create your tasks here
from __future__ import absolute_import, unicode_literals
from huey import crontab
from huey.contrib.djhuey import periodic_task, task, db_periodic_task, db_task
from external_push.models import GenericPushTarget

import datetime, pytz, time
from django.utils import timezone


@db_task()
def generic_push_target_push(target_id):
    try:
        push_target = GenericPushTarget.objects.get(id=target_id)
    except:
        # TODO - Replace with ObjNotFound
        return None

    push_target.send_data()

    return None


# TODO - At some point write a validation function that will allow us to trigger more often than every minute
@db_periodic_task(crontab(minute="*"))
def dispatch_push_tasks():
    generic_push_targets = GenericPushTarget.objects.filter(status=GenericPushTarget.STATUS_ACTIVE).all()

    for target in generic_push_targets:
        if timezone.now() >= (target.last_triggered + datetime.timedelta(seconds=target.push_frequency)):
            target.last_triggered = timezone.now()
            target.save()

            # Queue the generic_push_target_push task (going to do it asynchronously)
            generic_push_target_push(target.id)

    return None
