#!/bin/sh -e

##Copyright (c) 2018 NSF Center for Space, High-performance, and Resilient Computing (SHREC)
##University of Pittsburgh. All rights reserved.
##
##Redistribution and use in source and binary forms, with or without modification, are permitted provided
##that the following conditions are met:
##1. Redistributions of source code must retain the above copyright notice,
##   this list of conditions and the following disclaimer.
##2. Redistributions in binary form must reproduce the above copyright notice,
##   this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
##
##THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES,
##INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
##IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
##CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
##OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
##(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
##OF SUCH DAMAGE.


sudo apt-get update
sudo apt-get install --yes libpq-dev libssl-dev minicom postgresql python3-dev \
                           python3-pip libtool pkg-config texinfo libusb-dev libusb-1.0.0-dev libftdi-dev autoconf
sudo pip3 install --upgrade virtualenv

sudo apt-get install --yes automake libtool libusb-1.0-0-dev pkg-config
if [ -d "openocd" ]; then
    git clone git://git.code.sf.net/p/openocd/code openocd
    (
        cd openocd
        git fetch http://openocd.zylin.com/openocd refs/changes/21/4421/7 && git checkout FETCH_HEAD
        git checkout tags/v0.10.0
        ./bootstrap
        ./configure --enable-ftdi --disable-werror
        make
    )
fi
sudo groupadd usb
echo 'SUBSYSTEMS=="usb", ACTION=="add", MODE="0664", GROUP="usb"' | \
    sudo tee -a /etc/udev/rules.d/99-usbftdi.rules
sudo /etc/init.d/udev reload
sudo usermod -a -G usb "$USER"

printf 'install simics? [y/N]: '
read -r simics
case "$simics" in
    Y*|y*)
        (
            cd ~
            git clone git@github.com:CHREC/setup-simics
            cd setup-simics
            ./setup_simics.sh
        )
        ;;
esac
