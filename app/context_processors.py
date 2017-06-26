import pytz
from constance import config
from app.models import BrewPiDevice  #, OldControlConstants, NewControlConstants, PinDevice, SensorDevice, BeerLogPoint, FermentationProfile, Beer


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

    all_devices = BrewPiDevice.objects.all()

    return {'all_devices': all_devices}
