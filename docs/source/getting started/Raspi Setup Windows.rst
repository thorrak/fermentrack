Installing Raspbian to a Raspberry Pi using Windows 7
=======================================================

`here <https://www.raspberrypi.org/downloads/raspbian/>`__


Download and Install Raspbian
*******************************

1.	Download the latest version of Raspbian `here <https://www.raspberrypi.org/downloads/raspbian/>`__. You can download either the Lite or Full version - the Lite version is good for "headless" setups where you won't have a monitor & keyboard hooked up to your Raspberry Pi, the full version includes a graphical interface for use with a monitor/keyboard.

2.	Download and install `Etcher <https://etcher.io/>`__ as recommended `here <http://www.raspberrypi.org/documentation/installation/installing-images/windows.md>`__.

3.	Burn Raspbian to your SD card using Etcher:
3.1 Connect the SD card you will be installing Raspbian onto to your Windows PC using a removable SD card adaptor
3.2 Select the proper Raspbian .zip file
3.3 Select the proper removable drive to flash (Etcher only allows you to select removable drives)
3.4 Flash to the SD Card
3.5 Navigate to and open the SD Card to verify files were flashed

4. Enable SSH on your Raspberry Pi by writing an empty file named “ssh” to the root of the SD card via the Notepad Windows Program:
4.1 Run Notepad
4.2 In a new file, put in one space and nothing else
4.3 Click File > Save As, and save the file to the root (lowest level) directory on the SD Card:
4.3.1 Name the file ``ssh``
4.3.2 NOTE - Be certain to Save as type: All Types (* *)
4.4 Close the file

5. Configure WiFi (Optional, but required if running the Lite/Headless Version and you do not plan to connect the Raspberry Pi via Ethernet Cable):
5.1 Run Notepad
5.2 In a new file, paste the contents below. (Inserting the proper country code, network name, and network password) Network Names with some symbols may be problematic. If you have issues connecting, eliminate your SSID from having any unusual symbols. When entering your network name and password include the Quotes.

::

    country=US
    ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
    update_config=1

    network={
        ssid="NETWORK-NAME"
        psk="NETWORK-PASSWORD"
    }

5.3 Click File > Save As, and save the file to the root (lowest level) directory on the SD Card:
5.3.1 Name the file ``wpa_supplicant.conf``
5.3.2 Be certain to Save as type: All Types (* *)
5.4 Close the file

6. Verify that the ``ssh`` and ``wpa_supplicant.conf`` files were created in the Root Directory.
6.1 Open My Computer (File Explorer)
6.2 Navigate and open the removable SD Card containing Raspbian
6.3 Confirm that the ssh file and the wpa_supplicant.conf file can be seen
6.4 Navigate off the SD Card file.
6.5 Eject SD Card properly.

7. Remove the SD Card and plug the SD Card into your Raspberry Pi and plug in power to the Raspberry Pi. (If you did not configure WiFi, connect the Pi to Ethernet, plug in power ) **NOTE - Give time to boot, this can take 60 seconds or longer**


Configure your Raspberry Pi
****************************

8. Download and install Putty (http://www.putty.org/).
(This next step assumes that ssh is enabled on the Raspbian Image (Step 4) and that you properly created the wpa_supplicant.conf file.(Step 5))

Step 9. Login over WiFi/Ethernet using Putty. (Your Windows device MUST be on the same WiFi Network as you configured your Pi for)
9.1 Launch Putty
9.2 Set the Host Name (or IP address) Field to: ``raspberrypi.local`` (you can also log into your router, look for the device, and enter the correct IP address into Putty)
9.3 By default the Port should be set to 22 and the connection type should be set to SSH.
9.4 Click Open
9.5 If you see a Security Alert, select Yes.
9.6 A new terminal window will pop open prompting you for a user name.
9.7 The default user name is: ``pi``
9.8 The default password is: ``raspberry``

(You can now access your Pi via WiFi)

10. Update the Raspberry Pi Software.
10.1 Run the command ``sudo apt-get update -y`` on the Raspberry Pi using SSH (Putty)
10.2 Run the command ``sudo apt-get upgrade -y``

11. Configure Raspberry Pi (RPi 3 B+ with Raspbian Stretch Lite shown)
11.1 Run the command ``sudo Raspi-config``
11.2 Change User Password from default ``raspberry``
•	Option #1
•	Enter new password
11.3 (Optional) Change Hostname from default ``raspberrypi``.
•	Option #2
•	Option N1
•	Enter new Hostname
•	(NOTE - Changing the Hostname will alter how you login via Putty. If Hostname is changed, in step 9.2 you will need to enter the new hostname similar to ``newhostname.local`` and on step 9.8 you would need to enter your new password.
11.4 (Optional, if needed & not done earlier using ``wpa_supplicant.conf``) Configure WiFi
•	Option #2
•	Option N2
•	Follow Prompts
11.5 Reboot

Raspberry Pi is now ready for Fermentrack Install.

(Optional) Set up additional, optional networks
************************************************

::todo Change this to the main Raspi Setup file

If you move your Raspberry Pi around often, or potentially need to connect to multiple networks, you can configure the
``wpa_supplicant.conf`` file to contain multiple network options. To do so, do the following:


1.	Connect Raspberry Pi and Windows based hardware on the same network as original installation.

2.	Launch Putty and login to Raspberry Pi.

3.	Determine additional Networks to configure to. (If you don’t know, run the following command to locate local networks)
3.1 Run the command ``sudo iwlist wlan0 scan``
3.2 Record the ESSID you want to connect to (you will need to know the password)

4.   Add the network details to the Raspberry Pi
4.1 open the ``wpa_supplicant.conf`` file
•	Run the command ``sudo nano /etc/wpa_supplicant/wpa_supplicant.conf``
4.2 Find the following from Installation Step 5.2:

::

    network={
        ssid="NETWORK-NAME"
        psk="NETWORK-PASSWORD"
    }



4.3 Add priority and Network ID to original network configuration.


::

    network={
        ssid="NETWORK-NAME"
        psk="NETWORK-PASSWORD"
        priority=1
    }

4.4 Add additional Networks under your main and set priority.

::
    network={
        ssid="additional-network-name"
        psk="additional-network-password"
        priority=2
    }

    network={
        ssid="Secondary-Network-Name"
        psk="Secondary-Network-Password"
        priority=3
    }


4.5 Save your New Network Configuration. (Press the following)
•	Ctrl + x
•	Y
•	Enter
4.6 Reboot the Pi by running ``sudo shutdown -r now``

5. Confirm that Raspberry Pi is on Priority 1 Network
5.1 Launch Putty and login in to Raspberry Pi
•	If connected successfully, congratulations!
•	If unsuccessful:
•	Make certain RaspberryPi and Windows hardware are on the same network.
•	Log Windows/Pi devices into the original network to see if connection can be made.
•	If Raspberry Pi is lost and can’t be connected to, wipe SD card and start the installation process over.


Fermentrack is now ready to be configured.
