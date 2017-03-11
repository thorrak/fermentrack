# Hardware Comparison

There are four main types of hardware that currently support BrewPi firmware installations. Each have varying levels of support by Fermentrack.

* [ESP8266](ESP8266.md)
* [Arduino](Arduino.md)
* [Native Python (Fuscus)](Native%20Python.md)
* [Spark Core](Spark.md)

The following table shows which release is expected to have support for various controller types:

| Release    | ESP8266 Serial  | ESP8266 WiFi       | Arduino         | Spark           | Fuscus (Native Python) |
|------------|-----------------|--------------------|-----------------|-----------------|------------------------|
| v1         | :no_entry_sign: | :white_check_mark: | :no_entry_sign: | :no_entry_sign: | :no_entry_sign:        |
| v1 (flash) | :no_entry_sign: | :no_entry_sign:    | :no_entry_sign: | :no_entry_sign: | :no_entry_sign:        |
| v2         | :grey_question: | :white_check_mark: | :grey_question: | :no_entry_sign: |                        |
| v2 (flash) | :grey_question: | :grey_question:    | :grey_question: | :no_entry_sign: | :no_entry_sign:        |
| v3         |                 | :white_check_mark: |                 |                 |                        |


##### Legend:

* :white_check_mark: - Support confirmed in this version
* :grey_question: - Support targeted for this version
* :no_entry_sign: - Unsupported in this version
* Blank - Unknown
