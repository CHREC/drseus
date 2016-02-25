#!/bin/bash

set -e

sudo apt-get update
sudo apt-get install --yes libpq-dev openocd postgresql python3-dev python3-pip
sudo pip3 install --upgrade django django-filter django_tables2 numpy paramiko \
                            ply progressbar2 psycopg2 pyserial pyudev scp \
                            termcolor terminaltables
