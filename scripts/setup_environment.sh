#!/bin/sh

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


set -e

cd "$(dirname "$(dirname "$(readlink -f "$0")")")"

if [ ! -d python ]; then
    virtualenv python
fi

python/bin/pip3 install --upgrade django==1.11.12 django-filter==1.1.0 django-tables2 \
                                  numpy paramiko pip ply progressbar2 psycopg2 \
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

if [ -d simics-workspace ]; then
    printf 'run simics-gui to setup license? [Y/n]: '
    read -r license
    if [ "$license" != "n" ]; then
        echo 'simics license located at ssoe-vlic-01.engr.pitt.edu:4800'
        simics-workspace/simics-gui
    fi
    printf 'setup simics g-cache2? [Y/n]: '
    read -r cache
    if [ "$cache" != "n" ]; then
        (
            cd simics-workspace
            (
                cd modules
                git clone git@github.com:CHREC/g-cache2
            )
            make
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
