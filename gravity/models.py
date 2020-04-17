from __future__ import unicode_literals

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.core import serializers

import os.path, csv, logging, socket, typing, requests
import json, time, datetime, pytz
from constance import config
from fermentrack_django import settings
import re
import redis

# from lib.ftcircus.client import CircusMgr, CircusException

from app.models import BrewPiDevice

# if typing.TYPE_CHECKING:
from decimal import Decimal

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


class GravitySensor(models.Model):
    """GravitySensor is the base class for specific gravity sensors of all types

    Fermentrack supports a handful of types of specific gravity sensors, including Tilt Hydrometers, iSpindel devices,
    and manually entered readings. While each sensor type has its own specific class for sensor-specific configuration,
    the GravitySensor class is what Fermentrack itself interacts with, and contains all the data common to each
    controller type.

    Attributes:
        name: The name of the specific gravity sensor
        temp_format: The sensor's preferred temperature format
        sensor_type: The type of specific gravity sensor (for determining additional configuration information)
        status: The status for any daemon managing the device (Currently only used for Tilt hydrometers)
        active_log: (optional) The current log file (if any) to which readings are being recorded
        assigned_brewpi_device: (optional) The BrewPi temperature controller to which the gravity sensor is assigned
    """
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
        (SENSOR_ISPINDEL, 'iSpindel'),
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
    active_log = models.ForeignKey('GravityLog', null=True, blank=True, default=None, on_delete=models.SET_NULL,
                                   help_text='The currently active log of readings')

    # The assigned/linked BrewPi device (if applicable)
    assigned_brewpi_device = models.OneToOneField(BrewPiDevice, null=True, default=None, on_delete=models.SET_NULL,
                                                  related_name='gravity_sensor')

    def __str__(self) -> str:
        # TODO - Make this test if the name is unicode, and return a default name if that is the case
        return self.name

    def __unicode__(self) -> str:
        return self.name

    def is_gravity_sensor(self) -> bool:  # This is a hack used in the site template so we can display relevant functionality
        """Indicates that the object being examined is a gravity sensor

        This is a hack used in the site template so we can display relevant functionality. It currently has no purpose
        other than to return 'True' (whereas objects of other types - presumaby BrewPiDevices - would not return True).

        Returns:
            True
        """
        return True

    # retrieve_latest_point does just that - retrieves the latest (full) data point from redis
    def retrieve_latest_point(self) -> 'GravityLogPoint':
        return GravityLogPoint.load_from_redis(self.id)

    # Latest gravity & latest temp mean exactly that. Generally what we want is loggable - not latest.
    def retrieve_latest_gravity(self) -> float:
        point = self.retrieve_latest_point()
        return None if point is None else point.latest_gravity

    def retrieve_latest_temp(self) -> (float, str):
        point = self.retrieve_latest_point()
        if point is None:
            return None, None
        else:
            return point.latest_temp, point.temp_format

    # Loggable gravity & loggable temp are what we generally want. These can have smoothing/filtering applied.
    def retrieve_loggable_gravity(self) -> float:
        point = self.retrieve_latest_point()
        if point is None:
            return None
        else:
            return None if point.gravity is None else round(point.gravity, 3)

    def retrieve_loggable_temp(self) -> (float, str):
        # So temp needs units... we'll return a tuple (temp, temp_format)
        point = self.retrieve_latest_point()
        if point is None:
            return None, None
        else:
            # Changing to one degree of precision - more precise is nonsensical
            return None if point.temp is None else round(point.temp, 1), point.temp_format

    def create_log_and_start_logging(self, name: str):
        # First, create the new gravity log
        new_log = GravityLog(
            name=name,
            device=self,
            format=self.temp_format,
        )
        new_log.save()

        # Now that the log has been created, assign it to me so we can start logging
        self.active_log = new_log
        self.save()

    def convert_temp_to_sensor_format(self, temp: float, received_temp_format: str) -> (float, str):
        if self.temp_format == received_temp_format:
            return temp, self.temp_format
        elif self.temp_format == self.TEMP_FAHRENHEIT and received_temp_format == 'C':
            return (temp*9/5) + 32, self.temp_format
        elif self.temp_format == self.TEMP_CELSIUS and received_temp_format == 'F':
            return (temp-32) * 5 / 9, self.temp_format
        else:
            raise ValueError


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

    # model_version is the revision number of the "GravityLog" and "GravityLogPoint" models, designed to be iterated
    # when any change is made to the format/content of the flatfiles that would be written out. The idea is that a
    # separate converter could then be written moving between each iteration of model_version that could then be
    # sequentially applied to bring a beer log in line with what the model then expects.
    model_version = models.IntegerField(default=1)

    display_extra_data_as_annotation = models.BooleanField(default=False, help_text='Should any extra data be displayed as a graph annotation?')

    def __str__(self) -> str:
        return self.name

    def __unicode__(self) -> str:
        return self.__str__()

    @staticmethod
    def column_headers(which: str='base_csv', human_readable: bool=False) -> list or None:
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
    def column_headers_to_graph_string(which: str='base_csv') -> str:
        col_headers = GravityLog.column_headers(which, True)

        graph_string = ""

        for this_header in col_headers:
            graph_string += "'" + this_header + "', "

        if graph_string.__len__() > 2:
            return graph_string[:-2]
        else:
            return ""

    @staticmethod
    def name_is_valid(proposed_name: str) -> bool:
        # Since we're using self.name in a file path, want to make sure no injection-type attacks can occur.
        return True if re.match("^[a-zA-Z0-9 _-]*$", proposed_name) else False

    def base_filename(self) -> str:  # This is the "base" filename used in all the files saved out
        # Including the beer ID in the file name to ensure uniqueness (if the user duplicates the name, for example)
        if self.name_is_valid(self.name):
            return "Gravity Device " + str(self.device_id) + " - L" + str(self.id) + " - " + self.name
        else:
            return "Gravity Device " + str(self.device_id) + " - L" + str(self.id) + " - NAME ERROR - "

    def full_filename(self, which_file: str, extension_only: bool=False) -> str:
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

    def data_file_url(self, which_file: str) -> str:
        return settings.DATA_URL + self.full_filename(which_file, extension_only=False)

    def full_csv_url(self) -> str:
        return self.data_file_url('full_csv')

    def full_csv_exists(self) -> bool:
        # This is so that we can test if the log exists before presenting the user the option to download it
        file_name_base = os.path.join(settings.BASE_DIR, settings.DATA_ROOT, self.base_filename())
        full_csv_file = file_name_base + self.full_filename('full_csv', extension_only=True)
        return os.path.isfile(full_csv_file)

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

    def temp_to_f(self) -> float:
        if self.temp_format == 'F':
            return self.temp
        else:
            return (self.temp*9/5) + 32

    def temp_to_c(self) -> float:
        if self.temp_format == 'C':
            return self.temp
        else:
            return (self.temp-32) * 5 / 9

    def data_point(self, data_format: str='base_csv', set_defaults: bool=True) -> list:
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
                try:
                    if isinstance(self.extra_data, str):
                        shortText = self.extra_data[:1]
                    else:
                        # If the extra_data isn't a string (the angle that we're saving for iSpindels, for example) then
                        # we need to manually determine the shortText.
                        # That said, I could argue that we shouldn't be saving anything out at all (annotation wise) if
                        # this is the case. Question for later.
                        shortText = "f"
                except:
                    shortText = "f"
                retval.append({'series': 'temp', 'x': time_value, 'shortText': shortText,
                               'text': self.extra_data})
            return retval
        else:
            pass

    def save(self, *args, **kwargs):
        # Don't repeat yourself
        def check_and_write_headers(path, col_headers: list):
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    writer = csv.writer(f)
                    writer.writerow(col_headers)

        def write_data(path, row_data: list):
            with open(path, 'a') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)

        def check_and_write_annotation_json_head(path: str):
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    f.write("[\r\n")
                return False
            else:
                return True

        def write_annotation_json(path: str, annotation_data: list, write_comma: bool=True):
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

    def save_to_redis(self, device_id: int=None):
        # This saves the current (presumably complete) object as the 'current' point to redis
        r = redis.Redis(host=settings.REDIS_HOSTNAME, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD)
        if device_id is None:
            if self.associated_log is not None:
                r.set('grav_{}_full'.format(self.associated_log.device_id), serializers.serialize('json', [self, ]).encode(encoding="utf-8"))
            elif self.associated_device is not None:
                r.set('grav_{}_full'.format(self.associated_device_id), serializers.serialize('json', [self, ]).encode(encoding="utf-8"))
            else:
                raise ReferenceError  # Not sure if this is the right error type, but running with it
        else:
            r.set('grav_{}_full'.format(device_id), serializers.serialize('json', [self, ]).encode(encoding="utf-8"))

    @classmethod
    def load_from_redis(cls, sensor_id: int) -> 'GravityLogPoint' or None:
        r = redis.Redis(host=settings.REDIS_HOSTNAME, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD)
        try:
            # TODO - Redo this to remove overly greedy except
            redis_response = r.get('grav_{}_full'.format(sensor_id)).decode(encoding="utf-8")
            serializer = serializers.deserialize('json', redis_response)
            for obj2 in serializer:
                obj = obj2.object
                return obj
        except:
            return None


##### Tilt Hydrometer Specific Models
class TiltTempCalibrationPoint(models.Model):
    TEMP_FORMAT_CHOICES = (('F', 'Fahrenheit'), ('C', 'Celsius'))

    sensor = models.ForeignKey('TiltConfiguration', on_delete=models.CASCADE)
    orig_value = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="Original (Sensor) Temp Value",
                                     help_text="Original (Sensor) Temp Value")
    actual_value = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="Actual (Measured) Temp Value",
                                       help_text="Actual (Measured) Temp Value")

    temp_format = models.CharField(max_length=1, choices=TEMP_FORMAT_CHOICES, default='F')
    created = models.DateTimeField(default=timezone.now)  # So we can track when the configuration was current as of

    def temp_to_f(self, temp: Decimal) -> Decimal:
        if self.temp_format == 'F':
            return temp
        else:
            return (temp*9/5) + 32

    def temp_to_c(self, temp: Decimal) -> Decimal:
        if self.temp_format == 'C':
            return temp
        else:
            return (temp-32) * 5 / 9

    def orig_in_preferred_format(self) -> Decimal:
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

    def actual_in_preferred_format(self) -> Decimal:
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
    sensor = models.ForeignKey('TiltConfiguration', on_delete=models.CASCADE)
    actual_gravity = models.DecimalField(max_digits=5, decimal_places=3, verbose_name="Actual (Correct) Gravity value")
    tilt_measured_gravity = models.DecimalField(max_digits=5, decimal_places=3,
                                                verbose_name="Tilt Measured Gravity Value")
    created = models.DateTimeField(default=timezone.now)  # So we can track when the calibration was current as of


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

    CONNECTION_BRIDGE = "Bridge"
    CONNECTION_BLUETOOTH = "Bluetooth"

    CONNECTION_CHOICES = (
        (CONNECTION_BLUETOOTH, 'Bluetooth'),
        (CONNECTION_BRIDGE, 'TiltBridge'),
    )

    sensor = models.OneToOneField(GravitySensor, on_delete=models.CASCADE, primary_key=True,
                                  related_name="tilt_configuration")
    color = models.CharField(max_length=32, choices=COLOR_CHOICES, unique=True,
                             help_text="The color of Tilt Hydrometer being used")

    # As a result of the Tilt Hydrometer rewrite, some of the options that were previously available here have been
    # either eliminated or moved elsewhere:
    #   average_period_secs is no longer an option for smoothing data coming from the Tilt
    #   median_window_vals is now smoothing_window_vals and only provides a moving average function (not median filter)
    #   polling_frequency is explicitly how often Redis gets updated with the latest gravity readings
    #   bluetooth_device_id is no longer captured/used

    # Use a smoothing window that takes the moving average of the specified number of Tilt values
    # Generally the tilt hydrometer generates about 1.3 values every second. So for 300 seconds, you will end up with a
    # set of 360-380 values.
    smoothing_window_vals = models.IntegerField(default=70,
                                                help_text="Number of readings to include in the smoothing window.")

    # While average_period_secs and median_window_vals
    polling_frequency = models.IntegerField(default=15, help_text="How frequently Fermentrack should update the "
                                                                  "temp/gravity reading")

    connection_type = models.CharField(max_length=32, choices=CONNECTION_CHOICES, default=CONNECTION_BLUETOOTH,
                                       help_text="How should Fermentrack connect to this Tilt?")

    tiltbridge = models.ForeignKey('TiltBridge', on_delete=models.SET_NULL, null=True, blank=True, default=None,
                                   help_text="TiltBridge device to use (if any)")

    # Switching calibration to use the same equation-based approach as used on iSpindel. For now, going to start out
    # fairly basic - can revisit as things become more complex. The first degree coefficient defaults to 1 as we're
    # doing a gravity-to-gravity conversion. The default state should be to just keep whatever gravity was read off the
    # Tilt.
    grav_second_degree_coefficient = models.FloatField(default=0.0, help_text="The second degree coefficient in the "
                                                                              "gravity calibration equation")
    grav_first_degree_coefficient = models.FloatField(default=1.0, help_text="The first degree coefficient in the "
                                                                             "gravity calibration equation")
    grav_constant_term = models.FloatField(default=0.0, help_text="The constant term in the gravity calibration "
                                                                  "equation")
    # While coefficients_up_to_date is kept accurate, at the moment it doesn't really get used anywhere.
    # TODO - Do something useful with this
    coefficients_up_to_date = models.BooleanField(default=True, help_text="Have the calibration points changed since "
                                                                          "the coefficient calculator was run?")

    def tiltHydrometerName(self, uuid: str) -> str:
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

    def inFahrenheit(self) -> bool:
        if self.sensor.temp_format == 'F':
            return True
        elif self.sensor.temp_format == 'C':
            return False
        else:
            raise NotImplementedError

    def __str__(self) -> str:
        return self.color

    def __unicode__(self) -> str:
        return str(self)

    def circus_parameter(self) -> str:
        """Returns the parameter used by Circus to track this device's processes"""
        # TODO - Check if this is still used
        return self.color

    # TODO - Eliminate the xxx_redis_reload_flag functions
    def set_redis_reload_flag(self):
        r = redis.Redis(host=settings.REDIS_HOSTNAME, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD,
                        socket_timeout=5)
        r.set('tilt_reload_{}'.format(self.color), True)

    def clear_redis_reload_flag(self):
        r = redis.Redis(host=settings.REDIS_HOSTNAME, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD,
                        socket_timeout=5)
        r.set('tilt_reload_{}'.format(self.color), None)

    def check_redis_reload_flag(self) -> bool:
        r = redis.Redis(host=settings.REDIS_HOSTNAME, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD,
                        socket_timeout=5)
        reload_flag = r.get('tilt_reload_{}'.format(self.color))

        if reload_flag is None:
            return False
        else:
            return True

    # These two functions are explicitly so we have some way of saving/tracking RSSI for debugging and raw temp/gravity
    # later on.
    def save_extras_to_redis(self):
        # This saves the current (presumably complete) object as the 'current' point to redis
        r = redis.Redis(host=settings.REDIS_HOSTNAME, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD)

        datetime_string = datetime.datetime.strftime(timezone.now(), "%c")

        extras = {
            'rssi': getattr(self, 'rssi', None),
            'raw_gravity': getattr(self, 'raw_gravity', None),
            'raw_temp': getattr(self, 'raw_temp', None),
            'saved_at': datetime_string,
        }

        r.set('tilt_{}_extras'.format(self.color), json.dumps(extras).encode(encoding="utf-8"))

    def load_extras_from_redis(self) -> dict:
        try:
            r = redis.Redis(host=settings.REDIS_HOSTNAME, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD)
            redis_response = r.get('tilt_{}_extras'.format(self.color))
        except redis.exceptions.ConnectionError:
            # More than likely redis is offline (or we're in testing)
            return {}

        if redis_response is None:
            # If we didn't get anything back (i.e. no data has been saved to redis yet) then return None
            return {}

        redis_response = redis_response.decode(encoding="utf-8")
        extras = json.loads(redis_response)

        if 'rssi' in extras:
            self.rssi = extras['rssi']
        if 'raw_gravity' in extras:
            self.raw_gravity = extras['raw_gravity']
        if 'raw_temp' in extras:
            self.raw_gravity = extras['raw_temp']
        if 'saved_at' in extras:
            self.saved_at = datetime.datetime.strptime(extras['saved_at'], "%c")

        return extras

    def apply_gravity_calibration(self, uncalibrated_gravity: float) -> float:
        calibrated_gravity = self.grav_second_degree_coefficient * uncalibrated_gravity ** 2
        calibrated_gravity += self.grav_first_degree_coefficient * uncalibrated_gravity ** 1
        calibrated_gravity += self.grav_constant_term
        return calibrated_gravity


class TiltBridge(models.Model):
    """TiltBridge objects allow a single TiltBridge device to manage multiple individual Tilt hydrometers

    TiltBridge (http://www.tiltbridge.com/) is a project by one of the creators of Fermentrack to allow monitoring
    of Tilt Hydrometers using ESP32-based controllers. The TiltBridge controller then forwards the reading to an
    external web service (such as Fermentrack).

    TiltBridge controllers provide raw (unadjusted) temperature & gravity readings from the Tilt as well as the Tilt's
    color and the mDNS ID identifying the TiltBridge itself.

    Attributes:
        name: The internal identifier used to identify the TiltBridge within Fermentrack
        mdns_id: The mDNS ID which is provided by the TiltBridge to identify the device
    """

    class Meta:
        verbose_name = "TiltBridge"
        verbose_name_plural = "TiltBridges"

    name = models.CharField(max_length=64, help_text="Name to identify this TiltBridge")
    mdns_id = models.CharField(max_length=64, primary_key=True, validators=[RegexValidator(regex="^[a-zA-Z0-9]+$")],
                               help_text="mDNS ID used by the TiltBridge to identify itself both on your network " +
                                         "and to Fermentrack. NOTE - Prefix only - do not include '.local'")

    def __str__(self) -> str:
        return self.name

    def __unicode__(self) -> str:
        return self.name

    def update_fermentrack_url_on_tiltbridge(self, fermentrack_host) -> bool:
        # fermentrack_host = request.META['HTTP_HOST']
        try:
            if ":" in fermentrack_host:
                fermentrack_host = fermentrack_host[:fermentrack_host.find(":")]
            ais = socket.getaddrinfo(fermentrack_host, 0, 0, 0, 0)
            ip_list = [result[-1][0] for result in ais]
            ip_list = list(set(ip_list))
            resolved_address = ip_list[0]
            fermentrack_url = "http://{}/tiltbridge/".format(resolved_address)
            tiltbridge_url = "http://{}.local/settings/update/".format(self.mdns_id)

            r = requests.post(tiltbridge_url, data={'fermentrackURL': fermentrack_url})

            if r.status_code == 200:
                return True
            else:
                return False

        except:
            # For some reason we failed to resolve the IP address of Fermentrack. Return False.
            return False



### iSpindel specific models
class IspindelGravityCalibrationPoint(models.Model):
    sensor = models.ForeignKey('IspindelConfiguration', on_delete=models.CASCADE)
    angle = models.DecimalField(max_digits=10, decimal_places=7, verbose_name="Angle (Measured by Device)")
    gravity = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="Gravity Value (Measured Manually)")
    created = models.DateTimeField(default=timezone.now)  # So we can track when the calibration was current as of


class IspindelConfiguration(models.Model):
    sensor = models.OneToOneField(GravitySensor, on_delete=models.CASCADE, primary_key=True,
                                  related_name="ispindel_configuration")

    name_on_device = models.CharField(max_length=64, unique=True,
                                      help_text="The name configured on the iSpindel device itself")

    # Although iSpindel devices do gravity conversion on the device itself, to make future calibration easier we'll
    # re-convert inside Fermentrack. The conversion equation takes the form of gravity = a*x^3 + b*x^2 + c*x + d
    # where x is the angle, a is the third degree coefficient, b is the second degree coefficient, c is the first
    # degree coefficient, and d is the constant term.
    third_degree_coefficient = models.FloatField(default=0.0, help_text="The third degree coefficient in the gravity "
                                                                        "conversion equation")
    second_degree_coefficient = models.FloatField(default=0.0, help_text="The second degree coefficient in the gravity "
                                                                         "conversion equation")
    first_degree_coefficient = models.FloatField(default=0.0, help_text="The first degree coefficient in the gravity "
                                                                        "conversion equation")
    constant_term = models.FloatField(default=0.0, help_text="The constant term in the gravity conversion equation")

    # While coefficients_up_to_date is kept accurate, at the moment it doesn't really get used anywhere.
    # TODO - Do something useful with this
    coefficients_up_to_date = models.BooleanField(default=False, help_text="Have the calibration points changed since "
                                                                           "the coefficient calculator was run?")

    def __str__(self) -> str:
        return self.name_on_device

    def __unicode__(self) -> str:
        return str(self)

    def save_extras_to_redis(self):
        # This saves the current (presumably complete) object as the 'current' point to redis
        r = redis.Redis(host=settings.REDIS_HOSTNAME, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD)

        extras = {
            'ispindel_id': getattr(self, 'ispindel_id', None),
            'angle': getattr(self, 'angle', None),
            'battery': getattr(self, 'battery', None),
            'ispindel_gravity': getattr(self, 'ispindel_gravity', None),
            'token': getattr(self, 'token', None)
        }

        r.set('ispindel_{}_extras'.format(self.sensor_id), json.dumps(extras).encode(encoding="utf-8"))

    def load_extras_from_redis(self) -> dict:
        r = redis.Redis(host=settings.REDIS_HOSTNAME, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD)
        redis_response = r.get('ispindel_{}_extras'.format(self.sensor_id))

        if redis_response is None:
            # If we didn't get anything back (i.e. no data has been saved to redis yet) then return None
            return {}

        redis_response = redis_response.decode(encoding="utf-8")
        extras = json.loads(redis_response)

        if 'ispindel_id' in extras:
            self.ispindel_id = extras['ispindel_id']
        if 'angle' in extras:
            self.angle = extras['angle']
        if 'battery' in extras:
            self.battery = extras['battery']
        if 'ispindel_gravity' in extras:
            self.ispindel_gravity = extras['ispindel_gravity']
        if 'token' in extras:
            self.token = extras['token']

        return extras
