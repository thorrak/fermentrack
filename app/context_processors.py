import pytz
from constance import config
from app.models import BrewPiDevice  #, OldControlConstants, NewControlConstants, PinDevice, SensorDevice, BeerLogPoint, FermentationProfile, Beer
from gravity.models import GravitySensor
from brewery_image.models import BreweryLogo


def preferred_tz(request):
    """
    Simple context processor that puts a timezone object into every request containing the "PREFERRED_TIMEZONE"
    """

    preferred_tz = pytz.timezone(config.PREFERRED_TIMEZONE)

    return {"preferred_tz": preferred_tz, "preferred_tz_name": config.PREFERRED_TIMEZONE}


def devices(request):
    """
    Simple context processor that puts all BrewPiDevice objects into every request as "all_devices"
    """

    if config.TEMP_CONTROL_SUPPORT_ENABLED:
        all_devices = BrewPiDevice.objects.all()  # TODO - Rename all_devices to all_temp_controllers
    else:
        all_devices = None

    if config.GRAVITY_SUPPORT_ENABLED:
        all_gravity_sensors = GravitySensor.objects.all()
        unassigned_gravity_sensors = GravitySensor.objects.filter(assigned_brewpi_device=None)
    else:
        all_gravity_sensors = None
        unassigned_gravity_sensors = None

    return {'all_devices': all_devices, 'all_gravity_sensors': all_gravity_sensors,
            'unassigned_gravity_sensors': unassigned_gravity_sensors}


def logo(request):
        """
        Simple context processor that displays the last User Uploaded Image into Fermentrack
        """
        logo = BreweryLogo.objects.all()
        return {'logo': logo}
