#!/bin/bash

sudo apt-get install --yes python-dev python-pip openocd
sudo pip install django django-filter django_tables2 numpy paramiko ply \
                 pyserial==2.7 pyudev scp simplejson termcolor
                 # pyserial 3 breaks when connecting to /dev/pts/ (pty)
