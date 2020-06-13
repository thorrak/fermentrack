Preparing a Raspberry Pi for Fermentrack
============================================

Prior to installing Fermentrack, you need to install Raspbian and set everything up. Click the link below
to watch a video showing how to prepare the Raspberry Pi using a Mac, or read the linked instructions below for your operating system.


Prepare the Raspberry Pi - `[Video] <https://youtu.be/TdSnJOUgS3k>`__
--------------------------------------------------------------------------


1. Download the latest version of Raspbian from `here <https://www.raspberrypi.org/downloads/raspbian/>`__. I recommend the Lite version as I prefer headless installations, but the full version works as well.
2. Burn Raspbian to your SD card using `these instructions <https://www.raspberrypi.org/documentation/installation/installing-images/>`__.
3. `Enable SSH <https://www.raspberrypi.org/documentation/remote-access/ssh/>`__ on your Raspberry Pi by writing an empty file named "ssh" to the root of the SD card.
4. *Optional* - Configure WiFi - See the note below if you want to configure WiFi now, thus preventing having to find an ethernet cable
5. Plug the SD card into your Raspberry Pi, connect the Pi to ethernet (if you did not configure WiFi), and plug in power.
6. Locate the IP address for your Raspberry Pi This can generally be done by executing ``arp -a | grep raspberry`` however you can also locate your Raspberry Pi by logging into your router and looking for the device.
7. Update the Raspberry Pi software by running ``sudo apt-get update`` and ``sudo apt-get upgrade``.
8. Run ``raspi-config`` and configure the Pi. At a minimum, expand the filesystem (option 1).
9. Update the default password for the ``pi`` user using ``passwd``
10. *Optional* - `Configure WiFi <https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md>`__ on your Raspberry Pi (if needed)



Additional Info about Install-Time WiFi Configuration
----------------------------------------------------------

To configure WiFi on a headless install (or otherwise configure it at setup) prior to the initial boot on a newly flashed Raspbian installation, create a ``wpa_supplicant.conf`` file in the ``/boot`` directory of the SD card with the following contents (adjusting to match your network configuration):

::

    ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
    country=US
    network={
        ssid="YOUR_SSID"
        psk="YOUR_PASSWORD"
        key_mgmt=WPA-PSK
    }

Note - In the above, ``ssid`` is the name of your wireless network, ``psk`` is the password for your wireless network (if applicable), and ``key_mgmt`` is the password management protocol (which, for most home networks these days is WPA-PSK)
You will also need to select the appropriate `2 letter country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`__ for where you plan on using the Raspberry Pi.
