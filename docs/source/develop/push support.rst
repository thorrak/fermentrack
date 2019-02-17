.. include:: ../global.rst

"Push" Support
==============================

Although Fermentrack is focused on the "fermentation" phase of your brewing operation, Fermentrack is designed to
integrate with your brewing operation as a whole. To support the use of data collected by Fermentrack in other
applications, Fermentrack allows for data to be "pushed" on a periodic basis via HTTP requests (and will - in the
future - support pushing via TCP (sockets)).


Supported "Push" Targets
------------------------------

Fermentrack currently supports two push targets, though more are likely to be added in the near future:

- Brewers Friend - Fermentrack supports pushing collected data from specific gravity sensors to Brewers Friend using their push API
- "Generic" Push Target - Fermentrack's "native" push format - Pushes both specific gravity & temperature data




Generic Push Target Format
******************************

The "generic" push target format is the one recommended for use by developers who are adding native Fermentrack
support to their apps. This format contains temperature/gravity data collected by Fermentrack for each available
specific gravity sensor and BrewPi controller.

This format is supported by the `Fermentrack Push Target app <http://github.com/thorrak/fermentrack_push_target>`__ for
testing/development purposes.

::

    {'api_key': 'abcde',
     'brewpi_devices': [{'beer_temp': 0.0,
                         'control_mode': 'f',
                         'fridge_temp': 0.0,
                         'internal_id': 1,
                         'name': 'Legacy 2',
                         'temp_format': 'F'},
                        {'beer_temp': 27.64,
                         'control_mode': 'f',
                         'fridge_temp': 34.11,
                         'internal_id': 2,
                         'name': 'Kegerator',
                         'temp_format': 'F'}],
     'gravity_sensors': [{'gravity': 1.247,
                          'internal_id': 1,
                          'name': 'Pinky',
                          'sensor_type': 'tilt',
                          'temp': 79.0,
                          'temp_format': 'F'},
                         {'gravity': 0.0,
                          'internal_id': 3,
                          'name': 'Spindly',
                          'sensor_type': 'ispindel',
                          'temp': 86.225,
                          'temp_format': 'F'},
                         {'gravity': 1.2120000123977661,
                          'internal_id': 4,
                          'name': 'Purple Bridge',
                          'sensor_type': 'tilt',
                          'temp': 81.0,
                          'temp_format': 'F'}],
     'version': '1.0'}


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

