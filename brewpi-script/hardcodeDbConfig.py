from scriptlibs.brewpiScriptConfig import BrewPiScriptConfig, CannotRefreshConfigError
from pprint import pprint


class HardcodedDBConfig(BrewPiScriptConfig):

    def __init__(self, socket_port, wifiHost):
        super(HardcodedDBConfig, self).__init__()

        self.status = self.STATUS_ACTIVE
        self.logging_status = self.DATA_LOGGING_STOPPED

        # Interface to Script Connection Options
        self.use_inet_socket = True
        self.socket_host = "127.0.0.1"
        self.socket_port = socket_port
        # self.socket_name = ""

        # Script to Controller Connection Options
        self.connection_type = self.CONNECTION_TYPE_WIFI

        # WiFi Configuration Options
        self.wifi_host = wifiHost    # Hostname (or IP address, if no hostname lookup should take place)
        self.wifi_host_ip = ""  # Cached IP address from hostname lookup (optional)
        self.wifi_port = 23

    def get_profile_temp(self) -> float or None:
        return 20.0

    def is_past_end_of_profile(self) -> bool:
        return False

    def reset_profile(self):
        pass

    def refresh(self):
        pass

    def save_beer_log_point(self, beer_row):
        pprint(beer_row)
