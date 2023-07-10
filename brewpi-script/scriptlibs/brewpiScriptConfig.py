import socket
import datetime

from . import udev_integration


class BrewPiScriptConfig:
    DATA_LOGGING_ACTIVE = 'active'
    DATA_LOGGING_PAUSED = 'paused'
    DATA_LOGGING_STOPPED = 'stopped'

    STATUS_ACTIVE = 'active'
    STATUS_UNMANAGED = 'unmanaged'
    STATUS_DISABLED = 'disabled'
    STATUS_UPDATING = 'updating'

    CONNECTION_TYPE_SERIAL = "serial"
    CONNECTION_TYPE_AUTO = "auto"
    CONNECTION_TYPE_WIFI = "wifi"

    TEMP_FORMAT_FAHRENHEIT = "F"
    TEMP_FORMAT_CELSIUS = "C"

    def __init__(self):
        self.status = self.STATUS_ACTIVE
        self.logging_status = self.DATA_LOGGING_ACTIVE
        self.temp_format = self.TEMP_FORMAT_FAHRENHEIT
        self.active_beer_name = ""
        self.data_point_log_interval = 30

        # Interface to Script Connection Options
        self.use_inet_socket = False
        self.socket_host = ""
        self.socket_port = ""
        self.socket_name = ""

        # Script to Controller Connection Options
        self.connection_type = self.CONNECTION_TYPE_AUTO
        self.prefer_connecting_via_udev = True

        # Serial Port Configuration Options
        self.serial_port = ""
        self.serial_alt_port = ""
        self.udev_serial_number = ""

        # WiFi Configuration Options
        self.wifi_host = ""     # Hostname (or IP address, if no hostname lookup should take place)
        self.wifi_host_ip = ""  # Cached IP address from hostname lookup (optional)
        self.wifi_port = 23

        # Log File Path Configuration
        self.stderr_path = ""  # If left as an empty string, will log to stderr
        self.stdout_path = ""  # If left as an empty string, will log to stdout
        self.last_profile_temp_check = datetime.datetime.now() - datetime.timedelta(days=1)  # Initialize in the past to immediately trigger an update
        self.error_count = 0
        self.name = ""

    def get_profile_temp(self) -> float or None:
        raise NotImplementedError("Must implement in subclass!")

    def is_past_end_of_profile(self) -> bool:
        raise NotImplementedError("Must implement in subclass!")

    def reset_profile(self):
        raise NotImplementedError("Must implement in subclass!")

    def refresh(self) -> bool:
        # This function should reload the various configuration options from the file/database/etc.
        # If it returns false, then BrewPiScript will terminate
        raise NotImplementedError("Must implement in subclass!")

    def save_host_ip(self, ip_to_save):
        # Can be optionally overridden to save an IP address resolved from a DNS address to a cache
        self.wifi_host_ip = ip_to_save
        # upstream_config.wifi_host_ip = ip_to_save
        # upstream_config.save()

    def save_serial_port(self, serial_port_to_save):
        # Can be optionally overridden to save a serial port derived from a udev serial number to a cache
        self.serial_port = serial_port_to_save
        # upstream_config.serial_port = serial_port_to_save
        # upstream_config.save()

    def save_udev_serial_number(self, udev_serial_number):
        # Can be optionally overridden to save a udev serial number derived from a serial port to a cache
        self.udev_serial_number = udev_serial_number
        # upstream_config.udev_serial_number = udev_serial_number
        # upstream_config.save()

    def get_cached_ip(self):
        # This only gets called from within BrewPi-script

        # I really hate the name of the function, but I can't think of anything else. This basically does three things:
        # 1. Looks up the mDNS hostname (if any) set as self.wifi_host and gets the IP address
        # 2. Saves that IP address to self.wifi_host_ip (if we were successful in step 1)
        # 3. Returns the found IP address (if step 1 was successful), the cached (self.wifi_host_ip) address if it
        #    wasn't, or 'None' if we don't have a cached address and we weren't able to resolve the hostname
        if len(self.wifi_host) > 4:
            try:
                ip_list = []
                ipv6_list = []
                ais = socket.getaddrinfo(self.wifi_host, 0, 0, 0, 0)
                for result in ais:
                    if result[0] == socket.AddressFamily.AF_INET:
                        # IPv4 only
                        ip_list.append(result[-1][0])
                    elif result[0] == socket.AddressFamily.AF_INET6:
                        ipv6_list.append(result[-1][0])
                ip_list = list(set(ip_list))
                ipv6_list = list(set(ip_list))
                if len(ip_list) > 0:
                    resolved_address = ip_list[0]
                else:
                    resolved_address = ipv6_list[0]
                # If we were able to find an IP address, save it to the cache
                self.save_host_ip(resolved_address)
                return resolved_address
            except:
                # TODO - Add an error message here
                if len(self.wifi_host_ip) > 6:
                    # We weren't able to resolve the hostname (self.wifi_host) but we DID have a cached IP address.
                    # Return that.
                    return self.wifi_host_ip
                else:
                    return None
        # In case of error (or we have no wifi_host)
        return None

    def get_port_from_udev(self):
        # get_port_from_udev() looks for a USB device connected which matches self.udev_serial_number. If one is found,
        # it returns the associated device port. If one isn't found, it returns None (to prevent the cached port from
        # being used, and potentially pointing to another, unrelated device)

        if self.connection_type != self.CONNECTION_TYPE_SERIAL:
            return self.serial_port  # If we're connecting via WiFi, don't attempt autodetection

        # If the user elected to not use udev to get the port, just return self.serial_port
        if not self.prefer_connecting_via_udev:
            return self.serial_port

        # If the platform doesn't support udev (isn't Linux) then return self.serial_port as well.
        if not udev_integration.valid_platform_for_udev():
            return self.serial_port

        # If the udev_serial_number isn't yet set, try setting it
        if self.udev_serial_number == "":
            udev_serial_number = udev_integration.get_serial_from_node(self.serial_port)

            if udev_serial_number is not None:
                self.save_udev_serial_number(udev_serial_number)
                return self.serial_port
            else:
                # We failed to look up the udev serial number.
                return None
        else:
            # udev serial number is set -- Use it to look up the serial port
            udev_node = udev_integration.get_node_from_serial(self.udev_serial_number)

            if udev_node is not None:
                # The udev lookup found a device! Return the appropriate serial port.
                if self.serial_port != udev_node:
                    # If the serial port changed, cache it.
                    self.save_serial_port(udev_node)
                return udev_node
            else:
                # The udev lookup failed - return None
                return None

    def save_beer_log_point(self, beer_row):
        raise NotImplementedError("Must implement in subclass!")

