#!/bin/sh -e

sudo apt-get update
sudo apt-get install --yes libpq-dev minicom openocd postgresql python3-dev \
                           python3-pip
sudo pip3 install --upgrade virtualenv

printf 'install simics? [y/N]: '
read -r simics
case "$simics" in
    Y*|y*)
        git clone git@gitlab.hcs.ufl.edu:F4/setup-simics.git
        (
            cd setup-simics
            ./setup_simics.sh
        )
        rm -rf setup-simics
        ;;
esac
