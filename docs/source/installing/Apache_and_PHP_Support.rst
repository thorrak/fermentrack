.. include:: ../global.rst

Legacy (PHP/Apache) Application Support (Optional)
====================================================

Unlike apps such as RaspberryPints and BrewPi-www which use `Apache <https://www.apache.org/>`_ to serve webpages,
Fermentrack uses `nginx <https://nginx.org/en/>`_. If you wish to run applications other than Fermentrack on the same
Raspberry Pi you will need to configure nginx to serve those applications instead of Apache.

Fermentrack-tools includes a script which can be used to install this support automatically.

.. warning:: Support for PHP 5 was discontinued in the latest versions of Raspbian.



Understanding Legacy Support
-------------------------------

To support legacy applications, the fermentrack-tools script does the following:

* Install ``php5-common``, ``php5-cli``, and ``php5-fpm`` to allow Nginx to serve php files
* Disable ``apache2`` from launching at startup
* Create a new nginx configuration file serving webpages from ``/var/www/html`` on port 81

**Note** - Due to the port change mentioned above, any apps that were previously running at ``http://<your-ip>/`` will now be running at ``http://<your-ip>:81/``


Installation
--------------

Although fermentrack-tools offers a script to allow for fully automated installation of support for PHP/legacy apps, support can be installed manually as well.


Automated Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~

To run the fully automated installation script, simply SSH into your Raspberry Pi and execute:

``curl -L install-legacy-support.fermentrack.com | sudo bash``


Manual Installation
~~~~~~~~~~~~~~~~~~~~~~

To manually install legacy app support, you will need to do the following as root:

1. Install PHP5 support - ``apt-get install php5-common php5-cli php5-fpm``
2. Disable ``apache2`` from running at startup - ``update-rc.d apache2 disable``
3. Disable any currently running instance of ``apache2`` - ``service apache2 stop``
4. Install the appropriate configuration file to ``nginx``. An example configuration file can be found `here <https://github.com/thorrak/fermentrack-tools/tree/master/nginx-configs>`__, and must be installed in ``/etc/nginx/sites-enabled``
5. Restart PHP5-FPM - ``service php5-fpm restart``
6. Restart Nginx - ``service nginx restart``


Legacy BrewPi-www Installation Support
----------------------------------------

Although performing the above actions will allow brewpi-www to run alongside Fermentrack, doing so is not recommended.
Attempting to run brewpi-www in this way can result in issues as Fermentrack and brewpi-www compete to access/manage
your fermentation controller.
