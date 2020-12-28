.. include:: ../global.rst

"Push" Support
==============================

Although Fermentrack is focused on the "fermentation" phase of your brewing operation, Fermentrack is designed to
integrate with your brewing operation as a whole. To support the use of data collected by Fermentrack in other
applications, Fermentrack allows for data to be "pushed" on a periodic basis via HTTP requests (and will - in the
future - support pushing via TCP (sockets)).


Supported "Push" Targets
------------------------------

Fermentrack currently supports five push targets:

- **"Generic" Push Target** - Fermentrack's "native" push format - Pushes both specific gravity & temperature data
- **Brewer's Friend** - Pushes both specific gravity & temperature data associated with gravty sensors
- **Brewfather** - Pushes both specific gravity & temperature data associated with gravity sensors, as well as temperature data from BrewPi controllers with gravity sensors attached
- **ThingSpeak** - Pushes temperature data
- **Grainfather** - iSpindel push format - Pushes both specific gravity & temperature data from gravity sensors




Generic Push Target Format
******************************

The "generic" push target format is the one recommended for use by developers who are adding native Fermentrack
support to their apps. This format contains temperature/gravity data collected by Fermentrack for each available
specific gravity sensor and BrewPi controller.

This format is supported by the `Fermentrack Push Target app <http://github.com/thorrak/fermentrack_push_target>`__ for
testing/development purposes.

::

    {'api_key': 'abcde',
     'brewpi_devices': [{'control_mode': 'f',
                         'internal_id': 1,
                         'name': 'Legacy 2',
                         'temp_format': 'F'},
                        {'beer_temp': 31.97,
                         'control_mode': 'f',
                         'fridge_temp': 36.26,
                         'internal_id': 2,
                         'name': 'Kegerator',
                         'temp_format': 'F'}],
     'gravity_sensors': [{'gravity': 1.247,
                          'internal_id': 1,
                          'name': 'Pinky',
                          'sensor_type': 'tilt',
                          'temp': 78.0,
                          'temp_format': 'F'},
                         {'internal_id': 3,
                          'name': 'Spindly',
                          'sensor_type': 'ispindel',
                          'temp': 86.225,
                          'temp_format': 'F'}],
     'version': '1.0'}



Brewer's Friend Support
***********************

Fermentrack supports pushing data from specific gravity sensors to `Brewer's Friend <https://www.brewersfriend.com/>`_ using the "Device Stream" API. To configure:


#. Log into Fermentrack and click the "gear" icon in the upper right
#. Click "Add Brewer's Friend Push Target" at the bottom of the page
#. Log into your Brewer's Friend acount and go to `Profile > Integrations <https://www.brewersfriend.com/homebrew/profile/integrations>`_
#. Copy the API key listed at the top of the page in Brewer's Friend (the string of letters/numbers)
#. Within Fermentrack, paste the API key you just copied into the "Api key" field
#. Set the desired push frequency and select the gravity sensor from which you want to push data
#. Click "Add Push Target"

Within 60 seconds, Fermentrack will begin sending data from your gravity sensor to Brewer's Friend. This data can be seen on the `Device Settings <https://www.brewersfriend.com/homebrew/profile/device_settings>`_ page. (*Note* - You may need to click "Show All" on the right of this page to see the data for newly added devices)


Brewfather Support
***********************

Fermentrack supports pushing data from specific gravity sensors or temperature data from a brewpi to Brewfather using the "Custom Stream" API.

The following values in the Brewfather API is used;

::

    { "name": "",      // Will be either brewpi or gravitysensor
      "temp": 0,       // Temperature from gravity sensor or beer temp from attached brewpi
      "aux_temp": 0,   // Fridge temperature from brewpi
      "ext_temp": 0,   // Room temperature from brewpi
      "temp_unit": "C" //
      "gravity": 0,    // Gravity from sensor
      "gravity_unit": "G", 
      "pressure": 0,   // not used
      "pressure_unit": "", // not used
      "ph": 0,         // not used
      "bpm": 0,        // not used
      "comment": "",   // not used
      "beer": ""       // Name of active beer log
      }


To configure:

#. Log into Fermentrack and click the "gear" icon in the upper right
#. Click "Add Brewfather Push Target" at the bottom of the page
#. Log into your Brewfather acount and go to `Settings <https://web.brewfather.app/#/tabs/settings/settings>`_
#. At the bottom of the page, under "Power-ups" click the "switch" next to "Custom Stream"
#. Copy the Logging URL (starting with http and ending with a string of letters/numbers) listed under "Custom Stream"
#. Within Fermentrack, paste the Logging URL you just copied into the "Logging URL" field
#. From the drop down list, select either Gravity or BrewPi as source.
#. Set the desired push frequency and select the gravity sensor/brewpi from which you want to push data
#. Click "Add Push Target"

Within 60 seconds, Fermentrack will begin sending data from your gravity sensor to Brewfather. This data can be seen on the `Devices <https://web.brewfather.app/#/tabs/devices/devices>`_ page.

**NOTE** - If your gravity sensor is attached to a BrewPi controller, the temperature readings from that controller will be used instead of the ones from the gravity sensor.


ThingSpeak Support
***********************

Fermentrack supports pushing data from specific sensors to a ThinkSpeak Channel. The Channel Speak API is fixed to receive fields in the channel, so the designation of each channel is already defined.  This means that Field 1 is always Beer Name, Field 2 is Sensor Name, etc. To configure:

#. Log into Fermentrack and click the "gear" icon in the upper right
#. Click "Add ThingSpeak Push Target" at the bottom of the page
#. Now log into your ThingSpeak acount and on the My Channels Page select New Channel
#. Enter the data below in

::

    Name - Give your Channel a Name
    Description - Give your Channel a Description
    Field 1 - Beer Name
    Field 2 - Sensor Name
    Field 3 - Temp Format
    Field 4 - Beer Temp
    Field 5 - Fridge Temp
    Field 6 - Room Temp
    Field 7 - Beer Gravity

Feel free to fill out the optional elements but only the 'field' values above are sent.  The values entered are just labels for the data sent and can be customised. For example you can change 'Beer Temp' to 'My Beer (°C)'.


#. At the bottom of the page, select 'Save Channel'
#. Copy the "Write API Key" from the "API Keys" section
#. Within Fermentrack, paste the API Key you just copied into the "API Key" field
#. Set the desired push frequency and select the gravity sensor from which you want to push data
#. Click "Add Push Target"

Within 60 seconds, Fermentrack will begin sending data from to the ThingSpeak Channel. This data can be seen on the ThingSpeak 'Private View' tab in the channel page.

Grainfather Support
***********************

Fermentrack supports pushing data from specific gravity sensors (Gravity & Temperature) to Grainfather using the brew tracking API. To configure:

#. Log into your Grainfather account and select Equipment.
#. Add a Fermentation device and select iSpindel as device type. Fermentrack will push data in this format independant of what your device is. Copy the logging URL.
#. The second thing you need to do is to go to an active brew and link the device to a brew session. This is done under the headline fermentration tracking and the function "Add Tracking Device". Make note of the Name value (this is the brew ID).
#. Log into Fermentrack and click the "gear" icon in the upper right
#. Click "Add Grainfather Push Target" at the bottom of the page
#. Within Fermentrack, paste the Logging URL you just copied into the "Logging URL" field and enter the name (brew id) under the "gf_name" field.
#. Set the desired push frequency and select the gravity sensor from which you want to push data
#. Click "Add Push Target"

Within 60 seconds, Fermentrack will begin sending data from your gravity sensor to Grainfather. This data can be seen in your Grainfather account under Equipment or the Brew Session.


Implementation Notes
------------------------------

Push support within Fermentrack is implemented through the use of a "helper script" which currently is launched once
every minute. The helper script polls the defined push targets to determine which (if any) are overdue for data to be
pushed, and - for those targets - then executes the push based on how those targets are configured. Fermentrack polls
Redis for the latest available data point for specific gravity sensors, and polls BrewPi controllers for the latest data
point directly. This data is then encoded based on the selected push format and sent downstream to the requested target.

Push requests are handled asynchronously. Due to the way that the polling script is implemented, push "frequencies" may
be up to one polling cycle (currently 1 minute) later than expected. For 1 minute push cycles, this means that the
actual frequency could be as high as 2 minutes.


Feedback
------------------------------

Push support was designed to support future applications that do not yet exist, and as such, may not be perfect for
*your* application. That said, feedback is always appreciated and welcome. Feel free to reach out (HBT forums,
GitHub, Reddit...) if you have something in mind that you'd like to integrate Fermentrack into, and don't think the
existing push options will quite work.

