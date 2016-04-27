#!/bin/sh

set -e

brew update
brew install openocd postgresql python3
pip3 install --upgrade virtualenv
echo "run 'createdb' after launching postgresql for the first time"
