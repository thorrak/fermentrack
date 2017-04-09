#!/usr/bin/env bash

# In the interest of releasing this update, I'm creating this script to make reloading circus easier. This should be
# easily accomplished from within Fermentrack itself - but I don't have the patience to figure it out at the moment.

# TODO - Get Fermentrack to natively reload Circus instead of using this file

sleep 1s
circusctl stop
circusctl reloadconfig
circusctl start
