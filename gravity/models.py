from __future__ import unicode_literals

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.core import serializers

import os.path, csv, logging, socket
import json, time, datetime, pytz
from constance import config
from fermentrack_django import settings
import re
import redis


from lib.ftcircus.client import CircusMgr, CircusException

from app.models import BrewPiDevice

logger = logging.getLogger(__name__)

# GravitySensor
# |
# |--GravityLog
# |  |
# |  |- GravityLogPoint,GravityLogPoint...
# |
# |<-->TiltConfiguration
# |    |
# |    |- TiltTempCalibrationPoint, TiltTempCalibrationPoint...
# |    |
# |    |- TiltGravityCalibrationPoint, TiltGravityCalibrationPoint...


# Specific gravity sensors are expected to log 4 (optionally 5) data points per reading:
#  Specific Gravity
#  Temperature
#  Temp Format
#  If the temp was an estimate
#  Any extra data (optional)
#
# In addition to these 5 fields, we track when the data point was saved (but this isn't expected to be passed in)


# Due to the fact that - unlike temp controllers - we aren't assuming a single manufacturer/type of specific gravity
# sensor, we use the GravitySensor model to tie together the fields that don't require differentiation between sensor
# types

class GravitySensor(models.Model):
    class Meta:
        verbose_name = "Gravity Sensor"
        verbose_name_plural = "Gravity Sensors"

    # TEMP_FORMAT_CHOICES is used to track what the temperature readings are coming off the sensor
    TEMP_CELSIUS = 'C'
    TEMP_FAHRENHEIT = 'F'
    TEMP_FORMAT_CHOICES = ((TEMP_FAHRENHEIT, 'Fahrenheit'), (TEMP_CELSIUS, 'Celsius'))

    TEMP_ALWAYS_ESTIMATE = 'estimate (automatic)'
    TEMP_SOMETIMES_ESTIMATE = 'unknown (manual)'
    TEMP_NEVER_ESTIMATE = 'exact (automatic)'

    TEMP_ESTIMATE_CHOICES = (
        (TEMP_ALWAYS_ESTIMATE, 'Temp is always estimate'),
        (TEMP_SOMETIMES_ESTIMATE, 'Temp is sometimes estimate'),
        (TEMP_NEVER_ESTIMATE, 'Temp is never estimate'),
    )


    SENSOR_TILT = 'tilt'
    SENSOR_MANUAL = 'manual'
    SENSOR_ISPINDEL = 'ispindel'
    SENSOR_TYPE_CHOICES = (
        (SENSOR_TILT, 'Tilt Hydrometer'),
        # (SENSOR_ISPINDEL, 'iSpindel'),
        (SENSOR_MANUAL, 'Manual'),
    )


    STATUS_ACTIVE = 'active'
    STATUS_UNMANAGED = 'unmanaged'
    STATUS_DISABLED = 'disabled'
    STATUS_UPDATING = 'updating'

    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Active, Managed by Circus'),
        (STATUS_UNMANAGED, 'Active, NOT managed by Circus'),  # STATUS_UNMANAGED also applies for manual sensors /w no agent
        (STATUS_DISABLED, 'Explicitly disabled, cannot be launched'),
        (STATUS_UPDATING, 'Disabled, pending an update'),
    )

    name = models.CharField(max_length=48, help_text="Unique name for this device", unique=True)

    temp_format = models.CharField(max_length=1, choices=TEMP_FORMAT_CHOICES, default='F',
                                   help_text="Temperature units")

    sensor_type = models.CharField(max_length=10, default=SENSOR_MANUAL, choices=SENSOR_TYPE_CHOICES,
                                   help_text="Type of gravity sensor used")

    status = models.CharField(max_length=15, default=STATUS_ACTIVE, choices=STATUS_CHOICES,
                              help_text='Status of the gravity sensor (used by scripts that interact with it)')

    # The beer that is currently active & being logged
    active_log = models.ForeignKey('GravityLog', null=True, blank=True, default=None,
                                   help_text='The currently active log of readings')

    # The assigned/linked BrewPi device (if applicable)
    assigned_brewpi_device = models.OneToOneField(BrewPiDevice, null=True, default=None, on_delete=models.SET_NULL,
                                                  related_name='gravity_sensor')


    def __str__(self):
        # TODO - Make this test if the name is unicode, and return a default name if that is the case
        return self.name

    def __unicode__(self):
        return self.name

    def is_gravity_sensor(self):  # This is a hack used in the site template so we can display relevant functionality
        return True

    # retrieve_latest_point does just that - retrieves the latest (full) data point from redis
    def retrieve_latest_point(self):
        return GravityLogPoint.load_from_redis(self.id)

    # Latest gravity & latest temp mean exactly that. Generally what we want is loggable - not latest.
    def retrieve_latest_gravity(self):
        point = self.retrieve_latest_point()
        return None if point is None else point.latest_gravity

    def retrieve_latest_temp(self):
        # So temp needs units... we'll return a tuple (temp, temp_format)
        point = self.retrieve_latest_point()
        if point is None:
            return None, None
        else:
            return point.latest_temp, point.temp_format

    # Loggable gravity & loggable temp are what we generally want. These can have smoothing/filtering applied.
    def retrieve_loggable_gravity(self):
        point = self.retrieve_latest_point()
        return None if point is None else point.gravity

    def retrieve_loggable_temp(self):
        # So temp needs units... we'll return a tuple (temp, temp_format)
        point = self.retrieve_latest_point()
        if point is None:
            return None, None
        else:
            return point.temp, point.temp_format


    def create_log_and_start_logging(self, name):
        # First, create the new gravity log
        new_log = GravityLog(
            name= name,
            device=self,
            format=self.temp_format,
        )
        new_log.save()

        # Now that the log has been created, assign it to me so we can start logging
        self.active_log = new_log
        self.save()





class GravityLog(models.Model):
    # Gravity logs are unique based on the combination of their name & the original device
    name = models.CharField(max_length=255, db_index=True)
    device = models.ForeignKey(GravitySensor, db_index=True, on_delete=models.SET_NULL, null=True)
    created = models.DateTimeField(default=timezone.now)

    # format generally should be equal to device.temp_format. We're caching it here specifically so that if the user
    # updates the device temp format somehow we will continue to log in the OLD format. We'll need to make a giant
    # button that allows the user to convert the log files to the new format if they're different.
    TEMP_FORMAT_CHOICES = (('C', 'Celsius'), ('F', 'Fahrenheit'))
    format = models.CharField(max_length=1, choices=TEMP_FORMAT_CHOICES, default='F')

    # model_version is the revision number of the "GravityLog" and "GravityLogPoint" models, designed to be iterated when any
    # change is made to the format/content of the flatfiles that would be written out. The idea is that a separate
    # converter could then be written moving between each iteration of model_version that could then be sequentially
    # applied to bring a beer log in line with what the model then expects.
    model_version = models.IntegerField(default=1)

    display_extra_data_as_annotation = models.BooleanField(default=False, help_text='Should any extra data be displayed as a graph annotation?')

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.__str__()

    @staticmethod
    def column_headers(which='base_csv', human_readable=False):
        if which == 'base_csv':
            if human_readable:
                return ['Log Time', 'Specific Gravity', 'Temp']
            else:
                return ['log_time', 'gravity', 'temp']
        elif which == 'full_csv':
            if human_readable:
                return ['log_time', 'gravity', 'temp', 'temp_format', 'temp_is_estimate', 'gravity_latest',
                        'temp_latest', 'extra_data', 'log_id']
            else:
                return ['log_time', 'gravity', 'temp', 'temp_format', 'temp_is_estimate', 'gravity_latest',
                        'temp_latest', 'extra_data', 'log_id']
        else:
            return None

    @staticmethod
    def column_headers_to_graph_string(which='base_csv'):
        col_headers = GravityLog.column_headers(which, True)

        graph_string = ""

        for this_header in col_headers:
            graph_string += "'" + this_header + "', "

        if graph_string.__len__() > 2:
            return graph_string[:-2]
        else:
            return ""

    @staticmethod
    def name_is_valid(proposed_name):
        # Since we're using self.name in a file path, want to make sure no injection-type attacks can occur.
        return True if re.match("^[a-zA-Z0-9 _-]*$", proposed_name) else False

    def base_filename(self):  # This is the "base" filename used in all the files saved out
        # Including the beer ID in the file name to ensure uniqueness (if the user duplicates the name, for example)
        if self.name_is_valid(self.name):
            return "Gravity Device " + str(self.device_id) + " - L" + str(self.id) + " - " + self.name
        else:
            return "Gravity Device " + str(self.device_id) + " - L" + str(self.id) + " - NAME ERROR - "

    def full_filename(self, which_file, extension_only=False):
        if extension_only:
            base_name = ""
        else:
            base_name = self.base_filename()

        if which_file == 'base_csv':
            return base_name + "_graph.csv"
        elif which_file == 'full_csv':
            return base_name + "_full.csv"
        elif which_file == 'annotation_json':
            return base_name + "_annotations.almost_json"
        else:
            return None

    def data_file_url(self, which_file):
        return settings.DATA_URL + self.full_filename(which_file, extension_only=False)

    def full_csv_url(self):
        return self.data_file_url('full_csv')

        # def base_csv_url(self):
        #     return self.data_file_url('base_csv')

    # TODO - Add function to allow conversion of log files between temp formats


# When the user attempts to delete a gravity log, also delete the log files associated with it.
@receiver(pre_delete, sender=GravityLog)
def delete_gravity_log(sender, instance, **kwargs):
    file_name_base = os.path.join(settings.BASE_DIR, settings.DATA_ROOT, instance.base_filename())

    base_csv_file = file_name_base + instance.full_filename('base_csv', extension_only=True)
    full_csv_file = file_name_base + instance.full_filename('full_csv', extension_only=True)
    annotation_json = file_name_base + instance.full_filename('annotation_json', extension_only=True)

    for this_filepath in [base_csv_file, full_csv_file, annotation_json]:
        try:
            os.remove(this_filepath)
        except OSError:
            pass


class GravityLogPoint(models.Model):
    """
    GravityLogPoint contains the individual temperature log points we're saving
    """

    class Meta:
        managed = False  # Since we're using flatfiles rather than a database
        verbose_name = "Gravity Log Point"
        verbose_name_plural = "Gravity Log Points"
        ordering = ['log_time']

    TEMP_FORMAT_CHOICES = (('C', 'Celsius'), ('F', 'Fahrenheit'))

    gravity = models.DecimalField(max_digits=13, decimal_places=11, help_text="The current (loggable) sensor gravity")
    temp = models.DecimalField(max_digits=13, decimal_places=10, null=True, help_text="The current (loggable) temperature")
    temp_format = models.CharField(max_length=1, choices=TEMP_FORMAT_CHOICES, default='F')
    temp_is_estimate = models.BooleanField(default=True, help_text='Is this temperature an estimate?')
    extra_data = models.CharField(max_length=255, null=True, blank=True, help_text='Extra data/notes about this point')
    log_time = models.DateTimeField(default=timezone.now, db_index=True)

    # To support sensors that require some type of data smoothing/filtering, we'll also allow for logging the exact
    # reading we pulled off the sensor rather than just the smoothed/filtered one
    gravity_latest = models.DecimalField(max_digits=13, decimal_places=11, null=True, default=None,
                                         help_text="The latest gravity (without smoothing/filtering if applicable)")
    temp_latest = models.DecimalField(max_digits=13, decimal_places=10, null=True, default=None,
                                      help_text="The latest temperature (without smoothing/filtering if applicable)")

    # Associated log is intended to be the collection of log points associated with the gravity sensor's latest
    # logging efforts. That said, we're also using the model to store the latest gravity info in the absence of an
    # active logging effort, hence the null=True.
    associated_log = models.ForeignKey(GravityLog, db_index=True, on_delete=models.DO_NOTHING, null=True)

    # Associated device is so we can save to redis even without an associated log
    associated_device = models.ForeignKey(GravitySensor, db_index=True, on_delete=models.DO_NOTHING, null=True)


    def temp_to_f(self):
        if self.temp_format == 'F':
            return self.temp
        else:
            return (self.temp*9/5) + 32

    def temp_to_c(self):
        if self.temp_format == 'C':
            return self.temp
        else:
            return (self.temp-32) * 5 / 9


    def data_point(self, data_format='base_csv', set_defaults=True):
        # Everything gets stored in UTC and then converted back on the fly

        utc_tz = pytz.timezone("UTC")
        time_value = self.log_time.astimezone(utc_tz).strftime('%Y/%m/%d %H:%M:%SZ')  # Adding 'Zulu' designation


        if set_defaults:
            temp = self.temp or 0
            temp_format = self.temp_format or ''
            extra_data = self.extra_data or 0  # Not sure how we should proceed on this one
            gravity_latest = self.gravity_latest or 0
            temp_latest = self.temp_latest or 0
        else:
            temp = self.temp or None
            temp_format = self.temp_format or None
            extra_data = self.extra_data or None
            gravity_latest = self.gravity_latest or None
            temp_latest = self.temp_latest or None


        if data_format == 'base_csv':
            return [time_value, self.gravity, temp]
        elif data_format == 'full_csv':
            return [time_value, self.gravity, temp, temp_format, self.temp_is_estimate, gravity_latest,
                    temp_latest, extra_data, self.associated_log]
        elif data_format == 'annotation_json':
            # Annotations are just the extra data (for now)
            retval = []
            if self.extra_data is not None:
                retval.append({'series': 'temp', 'x': time_value, 'shortText': self.extra_data[:1],
                               'text': self.extra_data})
            return retval
        else:
            pass

    def save(self, *args, **kwargs):
        # Don't repeat yourself
        def check_and_write_headers(path, col_headers):
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    writer = csv.writer(f)
                    writer.writerow(col_headers)

        def write_data(path, row_data):
            with open(path, 'a') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)

        def check_and_write_annotation_json_head(path):
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    f.write("[\r\n")
                return False
            else:
                return True

        def write_annotation_json(path, annotation_data, write_comma=True):
            # annotation_data is actually an array of potential annotations. We'll loop through them & write them out
            with open(path, 'a') as f:
                for this_annotation in annotation_data:
                    if write_comma:  # We only want to do this once per run, regardless of the size of annotation_data
                        f.write(',\r\n')
                        write_comma = False
                    f.write('  {')
                    f.write('"series": "{}", "x": "{}",'.format(this_annotation['series'], this_annotation['x']))
                    f.write(' "shortText": "{}", "text": "{}"'.format(this_annotation['shortText'],
                                                                      this_annotation['text']))
                    f.write('}')

        # If we have a currently valid _gravity_ log, then write the data out. Otherwise, assume that we're just
        # collecting data to display on the dashboard.
        if self.associated_log is not None:
            # If we have an associated log, we always want to save the temperature in the format of the associated log
            # Convert the temp & then save in the appropriate format
            if self.associated_log.format != self.temp_format:
                if self.associated_log.format == 'F':
                    self.temp = self.temp_to_f()
                else:
                    self.temp = self.temp_to_c()
                self.temp_format = self.associated_log.format

            file_name_base = os.path.join(settings.BASE_DIR, settings.DATA_ROOT, self.associated_log.base_filename())

            base_csv_file = file_name_base + self.associated_log.full_filename('base_csv', extension_only=True)
            full_csv_file = file_name_base + self.associated_log.full_filename('full_csv', extension_only=True)
            annotation_json = file_name_base + self.associated_log.full_filename('annotation_json', extension_only=True)

            # Write out headers (if the files don't exist)
            check_and_write_headers(base_csv_file, self.associated_log.column_headers('base_csv'))
            check_and_write_headers(full_csv_file, self.associated_log.column_headers('full_csv'))

            # And then write out the data
            write_data(base_csv_file, self.data_point('base_csv'))
            write_data(full_csv_file, self.data_point('full_csv'))

            # Next, do the json file
            annotation_data = self.data_point('annotation_json')
            if len(annotation_data) > 0:  # Not all log points come with annotation data
                json_existed = check_and_write_annotation_json_head(annotation_json)
                write_annotation_json(annotation_json, annotation_data, json_existed)

            # super(BeerLogPoint, self).save(*args, **kwargs)

        # Once everything is written out, also write to redis as the cached current point
        self.save_to_redis()

    def save_to_redis(self, device_id=None):
        # This saves the current (presumably complete) object as the 'current' point to redis
        r = redis.Redis(host=settings.REDIS_HOSTNAME, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD)
        if device_id is None:
            if self.associated_log is not None:
                r.set('grav_{}_full'.format(self.associated_log.device_id), serializers.serialize('json', [self, ]))
            elif self.associated_device is not None:
                r.set('grav_{}_full'.format(self.associated_device_id), serializers.serialize('json', [self, ]))
            else:
                raise ReferenceError  # Not sure if this is the right error type, but running with it
        else:
            r.set('grav_{}_full'.format(device_id), serializers.serialize('json', [self, ]))


    @classmethod
    def load_from_redis(cls, sensor_id):
        r = redis.Redis(host=settings.REDIS_HOSTNAME, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD)
        try:
            redis_response = r.get('grav_{}_full'.format(sensor_id))
            serializer = serializers.deserialize('json', redis_response)
            for obj2 in serializer:
                obj = obj2.object
                return obj
        except:
            return None


##### Tilt Hydrometer Specific Models
class TiltTempCalibrationPoint(models.Model):
    TEMP_FORMAT_CHOICES = (('F', 'Fahrenheit'), ('C', 'Celsius'))

    sensor = models.ForeignKey('TiltConfiguration')
    orig_value = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="Original (Sensor) Temp Value", help_text="Original (Sensor) Temp Value")
    actual_value = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="Actual (Measured) Temp Value", help_text="Actual (Measured) Temp Value")

    temp_format = models.CharField(max_length=1, choices=TEMP_FORMAT_CHOICES, default='F')
    created = models.DateTimeField(default=timezone.now)  # So we can track when the configuration was current as of

    def temp_to_f(self, temp):
        if self.temp_format == 'F':
            return temp
        else:
            return (temp*9/5) + 32

    def temp_to_c(self, temp):
        if self.temp_format == 'C':
            return temp
        else:
            return (temp-32) * 5 / 9

    def orig_in_preferred_format(self):
        # Converts the temperature format of the configuration point to the currently active format assigned to the
        # sensor
        preferred_format = self.sensor.sensor.temp_format

        if preferred_format == self.temp_format:
            return self.orig_value
        elif preferred_format == 'F' and self.temp_format == 'C':
            return self.temp_to_f(self.orig_value)
        elif preferred_format == 'C' and self.temp_format == 'F':
            return self.temp_to_c(self.orig_value)
        else:
            raise NotImplementedError

    def actual_in_preferred_format(self):
        # Converts the temperature format of the configuration point to the currently active format assigned to the
        # sensor
        preferred_format = self.sensor.sensor.temp_format

        if preferred_format == self.temp_format:
            return self.actual_value
        elif preferred_format == 'F' and self.temp_format == 'C':
            return self.temp_to_f(self.actual_value)
        elif preferred_format == 'C' and self.temp_format == 'F':
            return self.temp_to_c(self.actual_value)
        else:
            raise NotImplementedError


class TiltGravityCalibrationPoint(models.Model):
    sensor = models.ForeignKey('TiltConfiguration')
    orig_value = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="Original (Sensor) Gravity Value")
    actual_value = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="Actual (Measured) Gravity Value")
    created = models.DateTimeField(default=timezone.now)  # So we can track when the configuration was current as of


class TiltConfiguration(models.Model):
    COLOR_BLACK = "Black"
    COLOR_ORANGE = "Orange"
    COLOR_GREEN = "Green"
    COLOR_BLUE = "Blue"
    COLOR_PURPLE = "Purple"
    COLOR_RED = "Red"
    COLOR_YELLOW = "Yellow"
    COLOR_PINK = "Pink"

    COLOR_CHOICES = (
        (COLOR_BLACK, 'Black'),
        (COLOR_ORANGE, 'Orange'),
        (COLOR_GREEN, 'Green'),
        (COLOR_BLUE, 'Blue'),
        (COLOR_PURPLE, 'Purple'),
        (COLOR_RED, 'Red'),
        (COLOR_YELLOW, 'Yellow'),
        (COLOR_PINK, 'Pink'),
    )


    sensor = models.OneToOneField(GravitySensor, on_delete=models.CASCADE, primary_key=True,
                                  related_name="tilt_configuration")
    color = models.CharField(max_length=32, choices=COLOR_CHOICES, unique=True,
                             help_text="The color of Tilt Hydrometer being used")

    # The following two options are migrated from the Tilt manager configuration file

    # Record values over a period in order to average/median the numbers. This is used to smooth noise.
    # Note - If we poll during this window, we'll get the same value returned as long as median_window_vals set below
    # is sufficiently high.
    # Default: Originally 5 mins, now 2 mins
    average_period_secs = models.IntegerField(default=2*60, help_text="Number of seconds over which to average readings")

    # Use a median filter over the average period. The window will be applied multiple times.
    # Generally the tilt hydrometer generates about 1.3 values every second. So for 300 seconds, you will end up with aset of 360-380 values.
    # Setting the window to < 360, will then give you a moving average like function.
    # Setting the window to >380 will disable this and use a median filter across the whole set. This means that changes in temp/gravity will take ~2.5 mins to be observed.
    median_window_vals = models.IntegerField(default=10000,
                                             help_text="Number of readings to include in the average window. If set to "
                                                       "less than ~1.3*average_period_secs, you will get a moving "
                                                       "average. If set to greater, you'll get the median value.")

    # While average_period_secs and median_window_vals
    polling_frequency = models.IntegerField(default=15, help_text="How frequently Fermentrack should update the "
                                                                  "temp/gravity reading from the sensor")

    # This is almost always 0, but adding it here in case someone needs to configure it later on
    bluetooth_device_id = models.IntegerField(default=0, help_text="Almost always 0 - Change if you have Bluetooth issues")

    def tiltHydrometerName(self, uuid):
        return {
                'a495bb10c5b14b44b5121370f02d74de': self.COLOR_RED,
                'a495bb20c5b14b44b5121370f02d74de': self.COLOR_GREEN,
                'a495bb30c5b14b44b5121370f02d74de': self.COLOR_BLACK,
                'a495bb40c5b14b44b5121370f02d74de': self.COLOR_PURPLE,
                'a495bb50c5b14b44b5121370f02d74de': self.COLOR_ORANGE,
                'a495bb60c5b14b44b5121370f02d74de': self.COLOR_BLUE,
                'a495bb70c5b14b44b5121370f02d74de': self.COLOR_YELLOW,
                'a495bb80c5b14b44b5121370f02d74de': self.COLOR_PINK,
        }.get(uuid)

    def inFahrenheit(self):
        if self.sensor.temp_format == 'F':
            return True
        elif self.sensor.temp_format == 'C':
            return False
        else:
            raise NotImplementedError

    def dev_id(self):
        return self.bluetooth_device_id

    def __str__(self):
        return self.color

    def __unicode__(self):
        return str(self)

