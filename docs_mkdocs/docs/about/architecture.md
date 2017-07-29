# The Fermentrack architecture

The Fermentrack stack is based on a front end application, a controller, and a firmware
running on the device that handles reading temperatures, switching cooling and heating etc.
Everything but the firmware part is running under a process manager which takes care of
launching the front end and brewpi.py controller scripts.

![Fermentrack Architechture](img/fermentrack.png)

See [components](components.md) documentation for links and licenses.

## The webserver nginx and chaussette WSGI server

Used to proxy http requests to chaussette over WSGI to the Fermentrack django application.

## cron

Used to start the Fermentrack stack, it starts the Circus process manager via a @reboot job,
it also checks the status of circus every 10 seconds, if it not running it will start it.
All this is handled by a script: *updateCronCircus.sh*

Supports the following arguments: *{start|stop|status|startifstopped|add2cron}* where:

* *start* - will start circusd and all the services
* *stop* - will quit circusd and all processes (note it would be started again in 10 minutes)
* *status* - will output a status of all processes running (see below)
* *startifstopped* - will start the process manager if stopped (called from cron every 10 minutes)
* *add2cron* - if crontab entries are missing, it will add them back.

Crontab entries added with *add2cron*:

    @reboot ~/fermentrack/brewpi-script/utils/updateCronCircus.sh start
    */10 * * * * ~/fermentrack/brewpi-script/utils/updateCronCircus.sh startifstopped


Example *status* output:

    $ ~/fermentrack/brewpi-script/utils/updateCronCircus.sh status
    Fermentrack: active
    brewpi-spawner: active
    circusd-stats: active
    dev-brewpi1: active


## The process manager *circus*

Fermentrack is started at boot with the help of cron (see *cron*), the process manager handles
all the different processes needed by Fermentrack.

* **Fermentrack** - The django application (web interface) runs under chaussette
* **brewpi-spawner** - An internal Fermentrack process for spawning controller scripts for controlling controllers like brewpi-esp8266.
* **circusd-stats** - An Internal circus process for stats, not used yet.
* **dev-brewpi1** - Is a controller script spawned by brewpi-spawner, handing a controller.

Circus documentation can be found [here](https://circus.readthedocs.io/en/latest/).

## Logging

* Circus process manager logs:
    - */home/fermentrack/fermentrack/log/circusd.log*
* Controller script (brewpi.py) log: 
    - */home/fermentrack/fermentrack/log/dev-[name]-stdout.log*
* Controller script (brewpi.py) error/info log:
   - */home/fermentrack/fermentrack/log/dev-[name]-stderr.log*
* Controller script spawner:
   - */home/fermentrack/fermentrack/log/fermentrack-brewpi-spawner.log*
* Fermentrack django application:
   - */home/fermentrack/fermentrack/log/fermentrack.log*

Logs are rotated every 2MB and the last 5 are saved with a number suffix.