from app.models import BrewPiDevice, Beer, FermentationProfile
from gravity.models import GravitySensor, GravityLog, TiltTempCalibrationPoint, TiltGravityCalibrationPoint, \
    TiltConfiguration, TiltBridge, IspindelConfiguration, IspindelGravityCalibrationPoint
from constance import config


def restore_brewpi_devices(obj_list:list, update:bool) -> list:
    """Loop through a list of BrewPiDevice object dicts, call each one's from_dict() method, and then save the object"""
    restore_status = []
    for obj_dict in obj_list:
        device = BrewPiDevice.from_dict(obj_dict, update=update)
        device.save()
        restore_status.append({'uuid': device.uuid, 'success': True})
    return restore_status

def restore_beers(obj_list:list, update:bool) -> list:
    """Loop through a list of Beer object dicts, call each one's from_dict() method, and then save the object"""
    restore_status = []
    for obj_dict in obj_list:
        beer = Beer.from_dict(obj_dict, update=update)
        beer.save()
        restore_status.append({'uuid': beer.uuid, 'success': True})
    return restore_status

def restore_fermentation_profiles(obj_list:list, update:bool) -> list:
    """Loop through a list of FermentationProfile object dicts, call each one's from_dict() method, and then save the
    object. This also implicitly restores all associated FermentationProfilePoint objects."""
    restore_status = []
    for obj_dict in obj_list:
        profile = FermentationProfile.load_from_dict(obj_dict, update=update)
        restore_status.append({'uuid': profile.uuid, 'success': True})
    return restore_status

# Gravity functions
def restore_gravity_sensors(obj_list:list, update:bool) -> list:
    """Loop through a list of GravitySensor object dicts, call each one's from_dict() method, and then save the object"""
    restore_status = []
    for obj_dict in obj_list:
        sensor = GravitySensor.from_dict(obj_dict, update=update)
        sensor.save()
        restore_status.append({'uuid': sensor.uuid, 'success': True})
    return restore_status

def restore_gravity_logs(obj_list:list, update:bool) -> list:
    """Loop through a list of GravityLog object dicts, call each one's from_dict() method, and then save the object"""
    restore_status = []
    for obj_dict in obj_list:
        log = GravityLog.from_dict(obj_dict, update=update)
        log.save()
        restore_status.append({'uuid': log.uuid, 'success': True})
    return restore_status

def restore_tilt_temp_calibration_points(obj_list:list, update:bool) -> list:
    """Loop through a list of TiltTempCalibrationPoint object dicts, call each one's from_dict() method, and then save
    the object"""
    restore_status = []
    for obj_dict in obj_list:
        point = TiltTempCalibrationPoint.from_dict(obj_dict, update=update)
        point.save()
        restore_status.append({'uuid': point.uuid, 'success': True})
    return restore_status

def restore_tilt_gravity_calibration_points(obj_list:list, update:bool) -> list:
    """Loop through a list of TiltGravityCalibrationPoint object dicts, call each one's from_dict() method, and then
    save the object"""
    restore_status = []
    for obj_dict in obj_list:
        point = TiltGravityCalibrationPoint.from_dict(obj_dict, update=update)
        point.save()
        restore_status.append({'uuid': point.uuid, 'success': True})
    return restore_status

def restore_tilt_configurations(obj_list:list, update:bool) -> list:
    """Loop through a list of TiltConfiguration object dicts, call each one's from_dict() method, and then save the
    object"""
    restore_status = []
    for obj_dict in obj_list:
        tilt_config = TiltConfiguration.from_dict(obj_dict, update=update)
        tilt_config.save()
        restore_status.append({'uuid': tilt_config.uuid, 'success': True})
    return restore_status

def restore_tiltbridges(obj_list:list, update:bool) -> list:
    """Loop through a list of TiltBridge object dicts, call each one's from_dict() method, and then save the object"""
    restore_status = []
    for obj_dict in obj_list:
        bridge = TiltBridge.from_dict(obj_dict, update=update)
        bridge.save()
        restore_status.append({'uuid': bridge.uuid, 'success': True})
    return restore_status

def restore_ispindel_configurations(obj_list:list, update:bool) -> list:
    """Loop through a list of IspindelConfiguration object dicts, call each one's from_dict() method, and then save the
    object"""
    restore_status = []
    for obj_dict in obj_list:
        ispindel_config = IspindelConfiguration.from_dict(obj_dict, update=update)
        ispindel_config.save()
        restore_status.append({'uuid': ispindel_config.uuid, 'success': True})
    return restore_status

def restore_ispindel_gravity_calibration_points(obj_list:list, update:bool) -> list:
    """Loop through a list of IspindelGravityCalibrationPoint object dicts, call each one's from_dict() method, and
    then save the object"""
    restore_status = []
    for obj_dict in obj_list:
        point = IspindelGravityCalibrationPoint.from_dict(obj_dict, update=update)
        point.save()
        restore_status.append({'uuid': point.uuid, 'success': True})
    return restore_status

def restore_fermentrack_configuration_options(obj_dict:dict):
    """Work through a dict containing all the Constance options, updating each setting to match what we were passed"""
    if 'BREWERY_NAME' in obj_dict:
        config.BREWERY_NAME = obj_dict['BREWERY_NAME']
    if 'DATE_TIME_FORMAT_DISPLAY' in obj_dict:
        config.DATE_TIME_FORMAT_DISPLAY = obj_dict['DATE_TIME_FORMAT_DISPLAY']
    if 'REQUIRE_LOGIN_FOR_DASHBOARD' in obj_dict:
        config.REQUIRE_LOGIN_FOR_DASHBOARD = obj_dict['REQUIRE_LOGIN_FOR_DASHBOARD']
    if 'TEMPERATURE_FORMAT' in obj_dict:
        config.TEMPERATURE_FORMAT = obj_dict['TEMPERATURE_FORMAT']
    if 'GRAVITY_DISPLAY_FORMAT' in obj_dict:
        config.GRAVITY_DISPLAY_FORMAT = obj_dict['GRAVITY_DISPLAY_FORMAT']
    if 'USER_HAS_COMPLETED_CONFIGURATION' in obj_dict:
        config.USER_HAS_COMPLETED_CONFIGURATION = obj_dict['USER_HAS_COMPLETED_CONFIGURATION']
    if 'TEMP_CONTROL_SUPPORT_ENABLED' in obj_dict:
        config.TEMP_CONTROL_SUPPORT_ENABLED = obj_dict['TEMP_CONTROL_SUPPORT_ENABLED']
    if 'GRAVITY_SUPPORT_ENABLED' in obj_dict:
        config.GRAVITY_SUPPORT_ENABLED = obj_dict['GRAVITY_SUPPORT_ENABLED']
    # if 'LAST_GIT_CHECK' in obj_dict:
    #     config.LAST_GIT_CHECK = obj_dict['LAST_GIT_CHECK']
    # if 'GIT_UPDATE_TYPE' in obj_dict:
    #     config.GIT_UPDATE_TYPE = obj_dict['GIT_UPDATE_TYPE']
    if 'ALLOW_GIT_BRANCH_SWITCHING' in obj_dict:
        config.ALLOW_GIT_BRANCH_SWITCHING = obj_dict['ALLOW_GIT_BRANCH_SWITCHING']
    if 'PREFERRED_TIMEZONE' in obj_dict:
        config.PREFERRED_TIMEZONE = obj_dict['PREFERRED_TIMEZONE']
    if 'GRAPH_BEER_TEMP_COLOR' in obj_dict:
        config.GRAPH_BEER_TEMP_COLOR = obj_dict['GRAPH_BEER_TEMP_COLOR']
    if 'GRAPH_BEER_SET_COLOR' in obj_dict:
        config.GRAPH_BEER_SET_COLOR = obj_dict['GRAPH_BEER_SET_COLOR']
    if 'GRAPH_FRIDGE_TEMP_COLOR' in obj_dict:
        config.GRAPH_FRIDGE_TEMP_COLOR = obj_dict['GRAPH_FRIDGE_TEMP_COLOR']
    if 'GRAPH_FRIDGE_SET_COLOR' in obj_dict:
        config.GRAPH_FRIDGE_SET_COLOR = obj_dict['GRAPH_FRIDGE_SET_COLOR']
    if 'GRAPH_ROOM_TEMP_COLOR' in obj_dict:
        config.GRAPH_ROOM_TEMP_COLOR = obj_dict['GRAPH_ROOM_TEMP_COLOR']
    if 'GRAPH_GRAVITY_COLOR' in obj_dict:
        config.GRAPH_GRAVITY_COLOR = obj_dict['GRAPH_GRAVITY_COLOR']
    if 'GRAPH_GRAVITY_TEMP_COLOR' in obj_dict:
        config.GRAPH_GRAVITY_TEMP_COLOR = obj_dict['GRAPH_GRAVITY_TEMP_COLOR']
    if 'CUSTOM_THEME' in obj_dict:
        config.CUSTOM_THEME = obj_dict['CUSTOM_THEME']
