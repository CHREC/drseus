#!/bin/sh

set -e

sudo apt-get update
sudo apt-get install --yes libpq-dev minicom openocd postgresql python3-dev \
                           python3-pip
sudo pip3 install --upgrade virtualenv
