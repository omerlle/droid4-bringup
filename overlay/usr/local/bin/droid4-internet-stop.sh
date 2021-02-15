#!/bin/sh
pkill qmicli
pkill dhclient
ifconfig wwan0 down
