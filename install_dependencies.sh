#!/bin/bash

sudo usermod -a -G dialout "$USER"
echo "added $USER to the dialout group (allows non-root access to serial ports)"
echo 'logout for this change to take effect'
sudo apt-get install python-pip
sudo pip install paramiko scp termcolor django django-chartit simplejson django_tables2 django-filter
dir=$(pwd)
pushd /usr/local/lib/python2.7/dist-packages/chartit
sudo patch -p1 -i "${dir}/chartit.patch"
popd
