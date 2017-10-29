# Hardware Comparison

There are four main types of hardware that currently support BrewPi firmware installations. Each have varying levels of support by Fermentrack.

* [ESP8266](ESP8266.md)
* [Arduino](Arduino.md)
* [Native Python (Fuscus)](Native%20Python.md)
* [Spark Core](Spark.md)

The following table shows which release is expected to have support for various controller types:

| Release    | ESP8266 Serial     | ESP8266 WiFi       | Arduino            | Spark           | Fuscus (Native Python) |
|------------|--------------------|--------------------|--------------------|-----------------|------------------------|
| v1         | No                 | Yes                | No                 | No              | No                     |
| v1 (flash) | No                 | No                 | No                 | No              | No                     |
| v2         | Yes                | Yes                | Yes                | No              | No                     |
| v2 (flash) | Yes                | Yes                | Yes                | No              | No                     |
| v3         | Yes                | Yes                | Yes                | Targeted        | Targeted               |


##### Legend:

* Yes - Support confirmed in this version
* Targeted - Support targeted for this version
* No - Unsupported in this version
* Blank - Unknown
