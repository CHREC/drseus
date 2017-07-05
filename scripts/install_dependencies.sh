#!/bin/sh -e

sudo apt-get update
sudo apt-get install --yes libpq-dev libssl-dev minicom openocd postgresql \
                           python3-dev python3-pip
sudo pip3 install --upgrade virtualenv

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
