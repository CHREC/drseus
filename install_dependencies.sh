#!/bin/bash

sudo usermod -a -G dialout "$USER"
echo "added $USER to the dialout group (allows non-root access to serial ports)"
echo 'logout for this change to take effect'
sudo apt-get install python-pip
sudo pip install paramiko scp termcolor django simplejson django_tables2 django-filter numpy
