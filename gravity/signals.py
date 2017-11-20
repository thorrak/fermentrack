from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete

from .models import GravitySensor, TiltConfiguration, TiltGravityCalibrationPoint, TiltTempCalibrationPoint

# The main purpose of these signals at the moment is to trigger reloading of the TiltConfiguration object within the
# tilt_manager.py script whenever there are changes to objects that could alter the Tilt's (or the Tilt manager's)
# behavior


@receiver(post_save, sender=GravitySensor)
def handle_gravitysensor_post_save(sender, **kwargs):
    """
    Trigger anything that should happen on update of GravitySensor
    """

    sensor = kwargs.get('instance')

    if 'tilt_configuration' in sensor:
        # Every time we update a GravitySensor we want to trigger a reload of the Tilt configuration in case logging
        # is enabled/disabled. Otherwise, no data will get logged (or data will erroneously continue to be logged)
        sensor.tilt_configuration.set_redis_reload_flag()


@receiver(post_save, sender=TiltConfiguration)
def handle_tiltconfiguration_post_save(sender, **kwargs):
    """
    Trigger anything that should happen on update of TiltConfiguration
    """

    tilt = kwargs.get('instance')
    tilt.set_redis_reload_flag()


@receiver(post_save, sender=TiltGravityCalibrationPoint)
def handle_TiltGravityCalibrationPoint_post_save(sender, **kwargs):
    """
    Trigger anything that should happen on update of TiltGravityCalibrationPoint
    """

    calibration_point = kwargs.get('instance')
    calibration_point.sensor.set_redis_reload_flag()


@receiver(post_save, sender=TiltTempCalibrationPoint)
def handle_TiltTempCalibrationPoint_post_save(sender, **kwargs):
    """
    Trigger anything that should happen on update of TiltTempCalibrationPoint
    """

    calibration_point = kwargs.get('instance')
    calibration_point.sensor.set_redis_reload_flag()

# TODO - Add a pre_delete signal to trigger cessation of the relevant tilt_manager process