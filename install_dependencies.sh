#!/bin/bash

sudo apt-get install python-pip
sudo pip install paramiko scp termcolor django django-chartit simplejson
dir=$(pwd)
pushd /usr/local/lib/python2.7/dist-packages/chartit
sudo patch -p1 -i "${dir}/chartit.patch"
popd
