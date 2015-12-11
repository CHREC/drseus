#!/bin/bash

sudo apt-get install --yes python-dev python-pip openocd
sudo pip install django django-filter django_tables2 numpy paramiko ply \
                 pyserial pyudev scp simplejson termcolor
