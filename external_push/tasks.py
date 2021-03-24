# Create your tasks here
from __future__ import absolute_import, unicode_literals
from huey import crontab
from huey.contrib.djhuey import periodic_task, task, db_periodic_task, db_task
from external_push.models import GenericPushTarget, BrewersFriendPushTarget, BrewfatherPushTarget, ThingSpeakPushTarget, GrainfatherPushTarget
from django.core.exceptions import ObjectDoesNotExist
from requests import ConnectionError

import datetime, pytz, time
from django.utils import timezone

from requests.models import MissingSchema


def print_for_logs(log_string):
    print(f"[{str(datetime.datetime.now())}] {log_string}")


@db_task()
def generic_push_target_push(target_id):
    try:
        push_target = GenericPushTarget.objects.get(id=target_id)
    except ObjectDoesNotExist:
        print_for_logs("FAILED - Unable to load generic push_target object")
        return None

    try:
        if push_target.send_data():
            print_for_logs("SUCCESS - Logged data to generic push target")
        else:
            print_for_logs("FAILED - Unable to log data to generic push target")
    except MissingSchema:
        print_for_logs(f"FAILED - Missing schema from logging URL '{push_target.logging_url}'. Attempting update to logging URL")
        if push_target.check_target_host():
            print_for_logs(f"Updated schema - new logging URL '{push_target.logging_url}'")
        else:
            print_for_logs("Unable to update schema")

    return None


@db_task()
def brewers_friend_push_target_push(target_id):
    try:
        push_target = BrewersFriendPushTarget.objects.get(id=target_id)
    except ObjectDoesNotExist:
        print_for_logs("FAILED - Unable to load Brewer's Friend push_target object")
        return None

    if push_target.send_data():
        print_for_logs("SUCCESS - Logged data to Brewer's Friend")
    else:
        print_for_logs("FAILED - Unable to log data to Brewer's Friend")

    return None


@db_task()
def brewfather_push_target_push(target_id):
    try:
        push_target = BrewfatherPushTarget.objects.get(id=target_id)
    except ObjectDoesNotExist:
        print_for_logs("FAILED - Unable to load Brewfather push_target object")
        return None

    try:
        if push_target.send_data():
            print_for_logs("SUCCESS - Logged data to Brewfather")
        else:
            print_for_logs("FAILED - Unable to log data to Brewfather")
    except MissingSchema:
        print_for_logs(f"FAILED - Missing schema from logging URL '{push_target.logging_url}'. Attempting update to logging URL")
        if push_target.check_logging_url():
            print_for_logs(f"Updated schema - new logging URL '{push_target.logging_url}'")
        else:
            print_for_logs("Unable to update schema")
    except ConnectionError as err:
        print_for_logs("FAILED - Connection error")
        print_for_logs(str(err))

    return None


@db_task()
def thingspeak_push_target_push(target_id):
    try:
        push_target = ThingSpeakPushTarget.objects.get(id=target_id)
    except ObjectDoesNotExist:
        print_for_logs("FAILED - Unable to load Thingspeak push_target object")
        return None

    if push_target.send_data():
        print_for_logs("SUCCESS - Logged data to Thingspeak")
    else:
        print_for_logs("FAILED - Unable to log data to Thingspeak")

    return None


@db_task()
def grainfather_push_target_push(target_id):
    try:
        push_target = GrainfatherPushTarget.objects.get(id=target_id)
    except ObjectDoesNotExist:
        print_for_logs("FAILED - Unable to load Grainfather push_target object")
        return None

    try:
        if push_target.send_data():
            print_for_logs("SUCCESS - Logged data to Grainfather")
        else:
            print_for_logs("FAILED - Unable to log data to Grainfather")

    except MissingSchema:
        print_for_logs(f"FAILED - Missing schema from logging URL '{push_target.logging_url}'. Attempting update to logging URL")
        if push_target.check_logging_url():
            print_for_logs(f"Updated schema - new logging URL '{push_target.logging_url}'")
        else:
            print_for_logs("Unable to update schema")

    return None


# TODO - At some point write a validation function that will allow us to trigger more often than every minute
@db_periodic_task(crontab(minute="*"))
def dispatch_push_tasks():
    generic_push_targets = GenericPushTarget.objects.filter(status=GenericPushTarget.STATUS_ACTIVE).all()
    brewers_friend_push_targets = BrewersFriendPushTarget.objects.filter(status=BrewersFriendPushTarget.STATUS_ACTIVE).all()
    brewfather_push_targets = BrewfatherPushTarget.objects.filter(status=BrewfatherPushTarget.STATUS_ACTIVE).all()
    thingspeak_push_targets = ThingSpeakPushTarget.objects.filter(status=ThingSpeakPushTarget.STATUS_ACTIVE).all()
    grainfather_push_targets = GrainfatherPushTarget.objects.filter(status=GrainfatherPushTarget.STATUS_ACTIVE).all()

    # Run through the list of generic push targets and trigger a (future) data send for each
    for target in generic_push_targets:
        if timezone.now() >= (target.last_triggered + datetime.timedelta(seconds=target.push_frequency)):
            target.last_triggered = timezone.now()
            target.save()

            # Queue the generic_push_target_push task (going to do it asynchronously)
            generic_push_target_push(target.id)

    # Run through the list of Brewer's Friend push targets and trigger a (future) data send for each
    for target in brewers_friend_push_targets:
        if timezone.now() >= (target.last_triggered + datetime.timedelta(seconds=target.push_frequency)):
            target.last_triggered = timezone.now()
            target.save()

            # Queue the generic_push_target_push task (going to do it asynchronously)
            brewers_friend_push_target_push(target.id)

    # Run through the list of Brewfather push targets and trigger a (future) data send for each
    for target in brewfather_push_targets:
        if timezone.now() >= (target.last_triggered + datetime.timedelta(seconds=target.push_frequency)):
            target.last_triggered = timezone.now()
            target.save()

            # Queue the generic_push_target_push task (going to do it asynchronously)
            brewfather_push_target_push(target.id)

    # Run through the list of ThingSpeak push targets and trigger a (future) data send for each
    for target in thingspeak_push_targets:
        if timezone.now() >= (target.last_triggered + datetime.timedelta(seconds=target.push_frequency)):
            target.last_triggered = timezone.now()
            target.save()

            # Queue the thingspeak_push_target_push task (going to do it asynchronously)
            thingspeak_push_target_push(target.id)
    # Run through the list of Grainfather push targets and trigger a (future) data send for each
    for target in grainfather_push_targets:
        if timezone.now() >= (target.last_triggered + datetime.timedelta(seconds=target.push_frequency)):
            target.last_triggered = timezone.now()
            target.save()

            # Queue the generic_push_target_push task (going to do it asynchronously)
            grainfather_push_target_push(target.id)

    return None
