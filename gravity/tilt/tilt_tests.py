import os, subprocess, sys
import pkg_resources
from packaging import version


# This function is used ot check if an apt package is installed on Raspbian, Ubuntu, Debian, etc.
def apt_package_installed(package_name: str) -> bool:
    devnull = open(os.devnull,"w")
    retval = subprocess.call(["dpkg", "-s", package_name],stdout=devnull,stderr=subprocess.STDOUT)
    devnull.close()
    if retval != 0:
        return False
    return True



# This is just a means to check if apt (dpkg) is installed at all
def has_apt() -> bool:
    try:
        devnull = open(os.devnull,"w")
        retval = subprocess.call(["dpkg", "--version"],stdout=devnull,stderr=subprocess.STDOUT)
        devnull.close()
        if retval != 0:
            return False
        return True
    except:
        # dpkg doesn't exist
        return False


def check_apt_packages() -> (bool, list):
    package_list = ["bluez", "libcap2-bin", "libbluetooth3", "libbluetooth-dev", "redis-server", "python3-dev"]
    test_results = []
    all_packages_ok = True

    for package in package_list:
        result = {'package': package, 'result': True}
        if apt_package_installed(package):
            result['result'] = True
        else:
            result ['result'] = False
            all_packages_ok = False
        test_results.append(result)

    return all_packages_ok, test_results


def check_python_packages() -> (bool, list):
    if sys.platform == "darwin":
        # The MacOS support uses different packages from the support for Linux
        package_list = [
            {'name': 'PyObjc', 'version': version.parse("6.2")},
            {'name': 'redis', 'version': version.parse("3.4.1")},
        ]
    else:
        package_list = [
            {'name': 'PyBluez', 'version': version.parse("0.23")},
            {'name': 'aioblescan', 'version': version.parse("0.2.6")},
            {'name': 'redis', 'version': version.parse("3.4.1")},
        ]

    test_results = []
    all_packages_ok = True

    for package_to_find in package_list:
        result_stub = {
            'package': package_to_find['name'],
            'required_version': package_to_find['version'],
            'installed_version': None,
            'ok': False,
        }

        for package in pkg_resources.working_set:
            if package.project_name == package_to_find['name']:
                result_stub['installed_version'] = package.parsed_version
                if result_stub['installed_version'] == result_stub['required_version']:
                    result_stub['ok'] = True

        if result_stub['ok'] is False:
            all_packages_ok = False
        test_results.append(result_stub)

    return all_packages_ok, test_results


# The following was used for testing during development
if __name__ == "__main__":
    if has_apt():
        apt_ok, apt_test_results = check_apt_packages()

        if apt_ok:
            print("All apt packages found. Package status:")
        else:
            print("Missing apt packages. Package status:")

        for this_test in apt_test_results:
            print("Package {}: {}".format(this_test['package'],
                                          ("Installed" if this_test['result'] else "Not Installed")))
    else:
        print("dpkg not installed - not checking to see if system packages are installed")
    print("")


    # Next, check the python packages
    python_ok, python_test_results = check_python_packages()

    if python_ok:
        print("All required python packages found. Package status:")
    else:
        print("Missing/incorrect python packages. Package status:")

    for this_test in python_test_results:
        print("Package {} - Required Version {} - Installed Version {} - OK? {}".format(
            this_test['package'], this_test['required_version'], this_test['installed_version'], this_test['ok']))
    print("")


