#!/bin/bash

set -e

sudo apt-get update
sudo apt-get install --yes python3-dev python3-pip openocd
sudo pip3 install --upgrade django django-filter django_tables2 numpy paramiko \
                            ply pyserial pyudev scp termcolor
