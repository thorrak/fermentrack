.. Fermentrack documentation master file, created by
   sphinx-quickstart on Fri Mar 30 17:31:19 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. include:: global.rst


Fermentrack
========================================

.. image:: http://www.fermentrack.com/static/img/fermentrack_logo.png

.. only::html
    What is Fermentrack?
    -----------------------

    Fermentrack is a web interface for controlling and monitoring fermentation temperature and progress. It interfaces with
    BrewPi controllers as well as specific gravity sensors like the Tilt and iSpindel in order to help you make better beer.
    Fermentrack is designed to be run on a Raspberry Pi, but can be used in most environments capable of running Python.

    Fermentrack is a complete replacement for the web interface used by BrewPi written in Python using the Django web
    framework. In addition to the features bundled with brewpi-www, Fermentrack provides an easy install process, simple
    flashing of both Arduino-based and ESP8266-based BrewPi controllers, and the ability to control multiple chambers at once.
    Fermentrack also supports features such as WiFi and Bluetooth connectivity to help reduce clutter in your brewery.

    To help track your wort's progress on it's journey to become beer, Fermentrack also supports multiple specific gravity
    sensors both on a standalone basis as well as in conjunction with BrewPi-based fermentation temperature controllers.
    Currently, Fermentrack supports the `Tilt Hydrometer`_ and iSpindel_ devices for automated gravity logging in addition
    to providing the ability to log manual gravity readings taken with traditional hydrometers or refractometers.


.. toctree::
    :maxdepth: 2
    :caption: Contents:

    about
    getting started/index
    user guide/index
    develop/index
    develop/components
    hardware
    faq
    todo


.. only::html
    .. include:: about.rst



.. todo:: Figure out how to include the text in about.rst on this page in the HTML version only

