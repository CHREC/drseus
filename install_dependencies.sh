#!/bin/bash

sudo apt-get install --yes python-dev python-pip
sudo pip install django django-filter django_tables2 numpy paramiko ply \
                 pyserial scp simplejson termcolor
