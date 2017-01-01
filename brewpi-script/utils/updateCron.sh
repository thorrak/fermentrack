#!/bin/bash
# This bash script will update the CRON job that is used to start/restart/check BrewPi

############
### Functions to catch/display errors during setup
############
warn() {
  local fmt="$1"
  command shift 2>/dev/null
  echo -e "$fmt\n" "${@}"
  echo -e "\n*** ERROR ERROR ERROR ERROR ERROR ***\n----------------------------------\nSee above lines for error message\nScript NOT completed\n"
}

die () {
  local st="$?"
  warn "$@"
  exit "$st"
}

# the script path will one dir above the location of this bash file
unset CDPATH
myPath="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
defaultScriptPath="$(dirname "$myPath")"

############
### Check for old crontab entry
############
echo -e "\n***** Updating cron for the brewpi user... *****\n"

sudo crontab -u brewpi -l > /tmp/oldcron
if [ -s /tmp/oldcron ]; then
  if sudo grep -q "brewpi.py" /tmp/oldcron; then
     > /tmp/newcron||die
     firstLine=true
     while read line
     do
       if [[ "$line" == *brewpi.py* ]]; then
         case "$line" in
             \#*) # just copy commented lines
             echo "$line" >> /tmp/newcron;
             continue ;;
             *)
             echo -e "It looks like you have an old brewpi entry in your crontab."
             echo -e "The cron job to start/restart brewpi has been moved to cron.d"
             echo -e "This means the lines for brewpi in your crontab are not needed anymore."
             echo -e "Nearly all users will want to comment out this line\n"
             firstLine=false
             echo "crontab line: $line"
             read -p "Do you want to comment out this line? [Y/n]: " yn </dev/tty
             case "$yn" in
                 y | Y | yes | YES| Yes ) echo "Commenting line"; echo "# $line" >> /tmp/newcron;;
                 n | N | no | NO | No ) echo -e "Keeping original line\n"; echo "$line" >> /tmp/newcron;;
                 * ) echo "No valid choice received, assuming yes..."; echo "Commenting line"; echo "# $line" >> /tmp/newcron;;
             esac
         esac
       fi
     done < /tmp/oldcron
     sudo crontab -u brewpi /tmp/newcron||die
     rm /tmp/newcron||warn
     if ! ${firstLine}; then
         echo -e "Updated crontab to:"
         sudo crontab -u brewpi -l||die
         echo -e "Finished updating crontab"
     fi
  fi
fi
rm /tmp/oldcron||warn

############
# Update etc/cron.d/brewpi
# Settings are stored in the cron file itself: active entries, scriptpath and stdout/stderr redirect paths
#
# Entries is a list of entries that should be active.
#   entries="brewpi wifichecker"
# If an entry is disabled, it is prepended with ~
#   entries="brewpi ~wifichecker"
#
# Each entry is two lines, one comment with the entry name, one for the actual entry
#   entry:wifichecker
#   */10 * * * * $scriptpath/util/wifiChecker.sh 1>$stdoutpath 2>>$stderrpath &
#
# This script checks the available entries whether they are up-to-date.# If not, it can replace the entry with a new version.
# If the entry is not in entries (enabled or disabled), it needs to be disabled or added.
# Known entries: brewpi wifichecker
#
# Full Example:
#   stderrpath="/home/brewpi/logs/stderr.txt"
#   stdoutpath="/home/brewpi/logs/stdout.txt"
#   scriptpath="/home/brewpi"
#   entries="brewpi wifichecker"
#   # entry:brewpi
#   * * * * * brewpi python $scriptpath/brewpi.py --checkstartuponly --dontrunfile; [ $? != 0 ] && python -u $scriptpath/brewpi.py 1>$stdoutpath 2>>$stderrpath &
#   # entry:wifichecker
#   */10 * * * * $scriptpath/util/wifiChecker.sh 1>$stdoutpath 2>>$stderrpath &
#
############

# default cron lines for brewpi
cronfile="/etc/cron.d/brewpi"
# make sure it exists
sudo touch "$cronfile"

brewpicron='* * * * * brewpi python $scriptpath/brewpi.py --checkstartuponly --dontrunfile $scriptpath/brewpi.py 1>/dev/null 2>>$stderrpath; [ $? != 0 ] && python -u $scriptpath/brewpi.py 1>$stdoutpath 2>>$stderrpath &'
wificheckcron='*/10 * * * * root sudo -u brewpi touch $stdoutpath $stderrpath; $scriptpath/utils/wifiChecker.sh 1>>$stdoutpath 2>>$stderrpath &'

# get variables from old cron job. First grep gets the line, second one the sting, tr removes the quotes.
# in cron file: entries="brewpi wifichecker"
entries=$(grep -m1 'entries=".*"' /etc/cron.d/brewpi | grep -oE '".*"' | tr -d \")
scriptpath=$(grep -m1 'scriptpath=".*"' /etc/cron.d/brewpi | grep -oE '".*"' | tr -d \")
stdoutpath=$(grep -m1 'stdoutpath=".*"' /etc/cron.d/brewpi | grep -oE '".*"' | tr -d \")
stderrpath=$(grep -m1 'stderrpath=".*"' /etc/cron.d/brewpi | grep -oE '".*"' | tr -d \")

# if the variables did not exist, add the defaults
if [ -z "$entries" ]; then
    entries="brewpi"
    echo "Cron file is old version, starting fresh"
    sudo rm -f "$cronfile"
    echo "entries=\"brewpi\"" | sudo tee "$cronfile" > /dev/null
fi

if [ -z "$scriptpath" ]; then
    scriptpath="$defaultScriptPath"
    echo "No previous setting for scriptpath found, using default $scriptpath"
    sudo sed -i '1iscriptpath="/home/brewpi"' "$cronfile"
fi

if [ -z "$stdoutpath" ]; then
    stdoutpath="/home/brewpi/logs/stdout.txt"
    echo "No previous setting for stdoutpath found, using default $stdoutpath"
    sudo sed -i '1istdoutpath="/home/brewpi/logs/stdout.txt"' "$cronfile"
fi

if [ -z "$stderrpath" ]; then
    stderrpath="/home/brewpi/logs/stdout.txt"
    echo "No previous setting for stdoutpath found, using default $stderrpath"
    sudo sed -i '1istderrpath="/home/brewpi/logs/stderr.txt"' "$cronfile"
fi

function checkEntry {
    entry=$1 # entry name
    newEntry=$2 # new cron job
    echo "Checking entry for $entry ..."
    # find old entry for this name
    oldEntry=$(grep -A1 "entry:$entry" "$cronfile" | tail -n 1)
    # check whether it is up to date
    if [ "$oldEntry" != "$newEntry" ]; then
        # if not up to date, prompt to replace
        echo -e "\nYour current cron entry:"
        if [ -z "$oldEntry" ]; then
            echo "None"
        else
            echo "$oldEntry"
        fi
        echo -e "\nLatest version of this cron entry:"
        echo "$newEntry"
        echo -e "\n"
        read -p "Your current cron entry differs from the latest version, would you like me to update? [Y/n]: " yn
        if [ -z "$yn" ]; then
            yn="y" # no entry/enter = yes
        fi
        case "$yn" in
            y | Y | yes | YES| Yes )
                line=$(grep -n "entry:$entry" /etc/cron.d/brewpi | cut -d: -f 1)
                if [ -z "$line" ]; then
                    echo -e "\nAdding new cron entry to file"
                    # entry did not exist, add at end of file
                    echo "# entry:$entry" | sudo tee -a "$cronfile" > /dev/null
                    echo "$newEntry" | sudo tee -a "$cronfile" > /dev/null
                else
                    echo -e "\nReplacing cron entry on line $line with newest version"
                    # get line number to replace
                    cp "$cronfile" /tmp/brewpi.cron
                    # write head of old cron file until replaced line
                    head -"$line" /tmp/brewpi.cron | sudo tee "$cronfile" > /dev/null
                    # write replacement
                    echo "$newEntry" | sudo tee -a "$cronfile" > /dev/null
                    # write remainder of old file
                    tail -n +$((line+2)) /tmp/brewpi.cron | sudo tee -a "$cronfile" > /dev/null
                fi
                ;;
            * )
                echo "Skipping entry for $entry"
                ;;
        esac
    fi
    echo "Done checking entry $entry ..."
}

# Entry for brewpi.py
found=false
for entry in $entries; do
    # entry for brewpi.py
    if [ "$entry" == "brewpi" ] ; then
        found=true
        checkEntry brewpi "$brewpicron"
        break
    fi
done

# Entry for WiFi check script
found=false
for entry in $entries; do
    if [ "$entry" == "wifichecker" ] ; then
        # check whether cron entry is up to date
        found=true
        checkEntry wifichecker "$wificheckcron"
        break
    elif [ "$entry" == "~wifichecker" ] ; then
        echo "WiFi checker is disabled."
        found=true
        break
    fi
done
# If there was no entry for wifichecker, ask to add it or disable it
if [ "$found" == false ] ; then
    echo "No setting found for wifi check script"
    if [ -n "$(ifconfig | grep wlan)" ]; then
        echo -e "\nIt looks like you're running a wifi adapter on your Pi"
    else
        echo -e "\nIt looks like you're not running a wifi adapter on your Pi."
    fi
    echo "We recently added a utility script that can attempt to restart the "
    echo "WiFi connection on your Pi, if the connection were to drop."
    read -p "Would you like to enable the cron entry? [Y/n]: " yn
    if [ -z "$yn" ]; then
        yn="y"
    fi
    case "$yn" in
        y | Y | yes | YES| Yes )
            # update entries="..." to entries="... wifichecker"
            sudo sed -i '/entries=.*/ s/"$/ wifichecker"/' "$cronfile"
            checkEntry wifichecker "$wificheckcron"
            sudo bash "$scriptpath"/utils/wifiChecker.sh checkinterfaces
            ;;
        * )
            # update entries="..." to entries="... ~wifichecker"
            sudo sed -i '/entries=.*/ s/"$/ ~wifichecker"/' "$cronfile"
            echo "Setting wifichecker to disabled"
            ;;
    esac
fi


echo -e "Restarting cron"
sudo /etc/init.d/cron restart||die
