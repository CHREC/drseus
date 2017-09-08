#!/bin/sh

set -e

cd "$(dirname "$(dirname "$(readlink -f "$0")")")"

if [ ! -d python ]; then
    virtualenv python
fi

python/bin/pip3 install --upgrade django django-filter django-tables2 numpy \
                                  paramiko pip ply progressbar2 psycopg2 \
                                  pyserial pyudev scp termcolor terminaltables

if [ ! -d simics-workspace ]; then
    printf 'setup simics workspace? [Y/n]: '
    read -r simics
    if [ "$simics" != "n" ]; then
        (
            mkdir simics-workspace
            cd simics-workspace
            simics=$(find /opt/simics/ -name "simics-4.8.*" | tail -n 1)
            "$simics"/bin/workspace-setup
            git clone git@github.com:CHREC/simics-a9x2
            git clone git@github.com:CHREC/simics-p2020rdb
        )
    fi
fi

if [ ! -d fiapps ]; then
    printf 'clone fiapps git repo? [Y/n]: '
    read -r fiapps
    if [ "$fiapps" != "n" ]; then
       git clone git@github.com:CHREC/fiapps.git
    fi
fi
