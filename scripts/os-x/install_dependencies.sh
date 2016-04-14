#!/bin/sh

set -e

brew update
brew install openocd postgresql python3
pip3 install --upgrade django django-filter django_tables2 numpy paramiko ply \
                       progressbar2 psycopg2 pyserial pyudev scp termcolor \
                       terminaltables
echo "run 'createdb' after launching postgresql for the first time"
