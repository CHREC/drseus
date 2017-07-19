#!/bin/sh -e

sudo apt-get update
sudo apt-get install --yes libpq-dev libssl-dev minicom postgresql python3-dev \
                           python3-pip
sudo pip3 install --upgrade virtualenv

sudo apt-get install --yes automake libtool libusb-1.0-0-dev pkg-config
git clone git://git.code.sf.net/p/openocd/code openocd
(
    cd openocd
    git checkout tags/v0.10.0
    ./bootstrap
    ./configure --enable-ftdi
    make
)

printf 'install simics? [y/N]: '
read -r simics
case "$simics" in
    Y*|y*)
        git clone git@github.com:CHREC/setup-simics
        (
            cd setup-simics
            ./setup_simics.sh
        )
        rm -rf setup-simics
        ;;
esac
