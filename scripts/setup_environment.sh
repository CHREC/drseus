#!/bin/sh

cd "$(dirname "$(dirname "$(readlink -f "$0")")")"

virtualenv python

python/bin/pip3 install --upgrade django django-filter django_tables2 numpy \
                                  paramiko pip ply progressbar2 psycopg2 \
                                  pyserial pyudev scp termcolor terminaltables
