from app.models import BrewPiDevice, Beer, FermentationProfile
from gravity.models import GravitySensor, GravityLog, TiltTempCalibrationPoint, TiltGravityCalibrationPoint, \
    TiltConfiguration, TiltBridge, IspindelConfiguration, IspindelGravityCalibrationPoint
from constance import config


def dump_brewpi_devices() -> list:
    """Generates a list of BrewPiDevice object dicts by querying all BrewPiDevice objects and calling their
    to_dict() method"""
    return [device.to_dict() for device in BrewPiDevice.objects.all()]

def dump_beers() -> list:
    """Generates a list of Beer object dicts by querying all Beer objects and calling their
    to_dict() method"""
    return [beer.to_dict() for beer in Beer.objects.all()]

def dump_fermentation_profiles() -> list:
    """Generates a list of FermentationProfile object dicts by querying all FermentationProfile objects and calling
    their to_dict() method. This also implicitly dumps all associated FermentationProfilePoint objects."""
    return [profile.to_dict() for profile in FermentationProfile.objects.all()]


# Gravity functions
def dump_gravity_sensors() -> list:
    """Generates a list of GravitySensor object dicts by querying all GravitySensor objects and calling their
    to_dict() method"""
    return [sensor.to_dict() for sensor in GravitySensor.objects.all()]

def dump_gravity_logs() -> list:
    """Generates a list of GravityLog object dicts by querying all GravityLog objects and calling their
    to_dict() method"""
    return [log.to_dict() for log in GravityLog.objects.all()]

def dump_tilt_temp_calibration_points() -> list:
    """Generates a list of TiltTempCalibrationPoint object dicts by querying all TiltTempCalibrationPoint objects
    and calling their to_dict() method"""
    return [point.to_dict() for point in TiltTempCalibrationPoint.objects.all()]

def dump_tilt_gravity_calibration_points() -> list:
    """Generates a list of TiltGravityCalibrationPoint object dicts by querying all TiltGravityCalibrationPoint
    objects and calling their to_dict() method"""
    return [point.to_dict() for point in TiltGravityCalibrationPoint.objects.all()]

def dump_tilt_configurations() -> list:
    """Generates a list of TiltConfiguration object dicts by querying all TiltConfiguration objects and calling their
    to_dict() method"""
    return [config.to_dict() for config in TiltConfiguration.objects.all()]

def dump_tiltbridges() -> list:
    """Generates a list of TiltBridge object dicts by querying all TiltBridge objects and calling their
    to_dict() method"""
    return [bridge.to_dict() for bridge in TiltBridge.objects.all()]

def dump_ispindel_configurations() -> list:
    """Generates a list of IspindelConfiguration object dicts by querying all IspindelConfiguration objects and
    calling their to_dict() method"""
    return [config.to_dict() for config in IspindelConfiguration.objects.all()]

def dump_ispindel_gravity_calibration_points() -> list:
    """Generates a list of IspindelGravityCalibrationPoint object dicts by querying all
    IspindelGravityCalibrationPoint objects and calling their to_dict() method"""
    return [point.to_dict() for point in IspindelGravityCalibrationPoint.objects.all()]


def dump_fermentrack_configuration_options() -> dict:
    """Create a dict containing all the Constance options"""
    config_options = {
        'BREWERY_NAME': config.BREWERY_NAME,
        'DATE_TIME_FORMAT_DISPLAY': config.DATE_TIME_FORMAT_DISPLAY,
        'REQUIRE_LOGIN_FOR_DASHBOARD': config.REQUIRE_LOGIN_FOR_DASHBOARD,
        'TEMPERATURE_FORMAT': config.TEMPERATURE_FORMAT,
        'GRAVITY_DISPLAY_FORMAT': config.GRAVITY_DISPLAY_FORMAT,
        'USER_HAS_COMPLETED_CONFIGURATION': config.USER_HAS_COMPLETED_CONFIGURATION,
        'TEMP_CONTROL_SUPPORT_ENABLED': config.TEMP_CONTROL_SUPPORT_ENABLED,
        'GRAVITY_SUPPORT_ENABLED': config.GRAVITY_SUPPORT_ENABLED,
        # 'LAST_GIT_CHECK': config.LAST_GIT_CHECK,
        'GIT_UPDATE_TYPE': config.GIT_UPDATE_TYPE,
        'ALLOW_GIT_BRANCH_SWITCHING': config.ALLOW_GIT_BRANCH_SWITCHING,
        # 'FIRMWARE_LIST_LAST_REFRESHED': config.FIRMWARE_LIST_LAST_REFRESHED,
        'PREFERRED_TIMEZONE': config.PREFERRED_TIMEZONE,
        'GRAPH_BEER_TEMP_COLOR': config.GRAPH_BEER_TEMP_COLOR,
        'GRAPH_BEER_SET_COLOR': config.GRAPH_BEER_SET_COLOR,
        'GRAPH_FRIDGE_TEMP_COLOR': config.GRAPH_FRIDGE_TEMP_COLOR,
        'GRAPH_FRIDGE_SET_COLOR': config.GRAPH_FRIDGE_SET_COLOR,
        'GRAPH_ROOM_TEMP_COLOR': config.GRAPH_ROOM_TEMP_COLOR,
        'GRAPH_GRAVITY_COLOR': config.GRAPH_GRAVITY_COLOR,
        'GRAPH_GRAVITY_TEMP_COLOR': config.GRAPH_GRAVITY_TEMP_COLOR,
        'CUSTOM_THEME': config.CUSTOM_THEME,
    }
    return config_options
