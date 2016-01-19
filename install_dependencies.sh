#!/bin/bash

sudo apt-get update
sudo apt-get install --yes python-dev python-pip openocd
sudo pip install --upgrade django django-filter django_tables2 numpy paramiko \
                           ply pyserial==2.7 pyudev scp simplejson termcolor
