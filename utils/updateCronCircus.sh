#!/bin/bash
# Crontab setup:
#
# At reboot startup
# @reboot ~/fermentrack/utils/updateCronCircus.sh start
#
# Every 10 minutes check if circus are running, if not start it up again
# */10 * * * * ~/fermentrack/utils/updateCronCircus.sh startifstopped
#

# Path to circus config file
SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
CONFIG="$SCRIPTPATH"/../circus.ini

# Config

if [ -f "$HOME/venv/bin/circusd" ]; then
  # Standard install environment - circusd is available in a venv in the standard location
  CIRCUSD=~/venv/bin/circusd
  # Source in our virtualenv
  if [ ! -e ~/venv/bin/activate ]; then
    echo "ERROR: Could not find activation script for  python virtualenv environment"
    exit 1
  else
    source ~/venv/bin/activate
  fi
elif command -v circusd &> /dev/null; then
  # circusd is naturally available on the path
  CIRCUSD=circusd
else
    echo "ERROR: Could not find circusd"
    exit 1
fi

CIRCUSCTL="python -m circus.circusctl --timeout 10"
NAME="Fermentrack supervisor: circusd: "
# Cron Regexp
REBOOT_ENTRY="^@reboot.*updateCronCircus.sh start$"
CHECK_ENTRY="^\*/10 \* \* \* \*.*updateCronCircus.sh startifstopped$"
# Cron Entries
REBOOT_CRON="@reboot \"${SCRIPTPATH}\"/updateCronCircus.sh start"
CHECK_CRON="*/10 * * * * \"${SCRIPTPATH}\"/updateCronCircus.sh startifstopped"



start() {
    echo -n "Starting $NAME"
    export PYTHONPATH=$PYTHONPATH:"$SCRIPTPATH/.."
    $CIRCUSD --daemon $CONFIG
    RETVAL=$?
    if [ $RETVAL -eq 0 ]; then
        echo "done"
    else
        echo "failed, please see logfile."
    fi
}

stop() {
    echo -n "Stopping $NAME"
    $CIRCUSCTL quit
}

status() {
    $CIRCUSCTL status
}

startifstopped() {
    $CIRCUSCTL status >/dev/null 2>&1
    RETVAL=$?
    if [ ! $RETVAL -eq 0 ]; then
        start
    fi
}

add2cron() {
    echo "Checking and fixing cron entries for Fermentrack"
    if ! crontab -l|grep -E -q "$REBOOT_ENTRY"; then
        (crontab -l; echo "$REBOOT_CRON" ) | crontab -
        echo " - Adding @reboot cron entry for fermentrack to cron"
    fi
    if ! crontab -l|grep -E -q "$CHECK_ENTRY"; then
        (crontab -l; echo "$CHECK_CRON" ) | crontab -
        echo " - Adding periodic checks for fermentrack to cron"
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status
        ;;
    startifstopped)
        startifstopped
        ;;
    add2cron)
        add2cron
        ;;
    *)
        echo "Usage: $0 {start|stop|status|startifstopped|add2cron}"
        exit 0
        ;;
esac
