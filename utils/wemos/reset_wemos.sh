#!/usr/bin/env bash
ESPToolDir="$HOME/venv/bin/esptool"
FirmwareDir="."

cd "$FirmwareDir"

port=/dev/ttyUSB0

if [ ! -c $port ]; then
   port=/dev/ttyUSB1
fi

if [ ! -c $port ]; then
   echo "No device appears to be plugged in.  Stopping."
fi

printf "Writing AT firmware to the Wemos D1 Mini in 3..."

sleep 1; printf "2..."

sleep 1; printf "1..."

sleep 1; echo "done."

echo "Erasing the flash first"

"$ESPToolDir/esptool.py" --port $port erase_flash

"$ESPToolDir/esptool.py" --chip esp8266 --port $port \
   write_flash -fm dio -ff 20m -fs detect \
   0x0000 "$FirmwareDir/boot_v1.7.bin" \
   0x01000 "$FirmwareDir/user1.1024.new.2.bin" \
   0x3fc000 "$FirmwareDir/esp_init_data_default_v08.bin"  \
   0x7e000 "$FirmwareDir/bin/blank.bin"  \
   0x3fe000 "$FirmwareDir/bin/blank.bin"

echo "Check the boot by typing: miniterm $port 74800"
echo " and then resetting.  Use Ctrl-] to quit miniterm,"
