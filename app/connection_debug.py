import socket
import telnetlib


# So here are the tests that I want to have (for WiFi controllers):
# 1. Test that we can resolve the hostname.
#    1a. If we are successful, test that it matches the IP address saved in the device cache
# 2. If 1 was successful, test if we can telnet to the resolved IP address
#    2a. If either #2 was unsuccessful and (there is a cached IP address or #1a was false) then attempt to telnet to
#        the cached IP address
# 3. If #2 was successful, read the version number from the controller

def dns_lookup(hostname):
  try:
    ip_list = []
    ais = socket.getaddrinfo(hostname, 0, 0, 0, 0)
    for result in ais:
      ip_list.append(result[-1][0])
    ip_list = list(set(ip_list))
    return ip_list[0]
  except:
    return None

def test_telnet(hostname):
  # This attempts to test the validity of a controller
  # It returns a tuple (probably not the best way to do this) which is in the format:
  # Initial Connection Test (bool), Version Response Test (bool), Version Response (str)
  try:
    tn = telnetlib.Telnet(host=hostname, timeout=3)
  except socket.timeout:
    return False, False, None
  try:
    tn.write("n\r\n")
    version_string = tn.read_until("}",3)
  except:
    return True, False, None
  return True, True, version_string


# The following was used for testing during development
if __name__ == "__main__":
  # dns_name = dns_lookup("legacy2.local")
  legacy_test_results = test_telnet("legacy2.local")
  yahoo_test_results = test_telnet("www.yahoo.com")
  pass