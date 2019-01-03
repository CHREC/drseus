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


ask() {
    while true; do
        if [ "${2:-}" = "Y" ]; then
            prompt="Y/n"
            default=Y
        elif [ "${2:-}" = "N" ]; then
            prompt="y/N"
            default=N
        else
            prompt="y/n"
            default=""
        fi

        printf "$1 [$prompt]: "
        read -r REPLY

        if [ -z "$REPLY" ]; then
            REPLY=$default
        fi
        case "$REPLY" in
            Y*|y*) return 0 ;;
            N*|n*) return 1 ;;
        esac
    done
}

cd "$(dirname "$(dirname "$(readlink -f "$0")")")"

./drseus.py ls

printf "enter pynq0 campaign number: "
read -r campaign0
if ask 'disable l2 cache for pynq0?' N; then
    if ask 'disable l1 cache for pynq0?' N; then
        cache0="cache_off"
    else
        cache0="l2_off"
    fi
else
    cache0="cache_on"
fi
printf "enter pynq1 campaign number: "
read -r campaign1
if ask 'disable l2 cache for pynq1?' N; then
    if ask 'disable l1 cache for pynq1?' N; then
        cache1="cache_off"
    else
        cache1="l2_off"
    fi
else
    cache1="cache_on"
fi
printf "enter pynq2 campaign number: "
read -r campaign2
if ask 'disable l2 cache for pynq2?' N; then
    if ask 'disable l1 cache for pynq2?' N; then
        cache2="cache_off"
    else
        cache2="l2_off"
    fi
else
    cache2="cache_on"
fi
printf "enter pynq3 campaign number: "
read -r campaign3
if ask 'disable l2 cache for pynq3?' N; then
    if ask 'disable l1 cache for pynq3?' N; then
        cache3="cache_off"
    else
        cache3="l2_off"
    fi
else
    cache3="cache_on"
fi
printf "enter pynq7 campaign number: "
read -r campaign7
if ask 'disable l2 cache for pynq7?' N; then
    if ask 'disable l1 cache for pynq7?' N; then
        cache7="cache_off"
    else
        cache7="l2_off"
    fi
else
    cache7="cache_on"
fi

tmux new-session -d -s supervise
tmux send-keys -t supervise:0 "./drseus.py -c $campaign0 @conf/lansce/supervise/pynq0_$cache0 --cmd 'supervise 0'" ENTER
tmux new-window -t supervise:1
tmux send-keys -t supervise:1  "./drseus.py -c $campaign1 @conf/lansce/supervise/pynq1_$cache1 --cmd 'supervise 0'" ENTER
tmux new-window -t supervise:2
tmux send-keys -t supervise:2  "./drseus.py -c $campaign2 @conf/lansce/supervise/pynq2_$cache2 --cmd 'supervise 0'" ENTER
tmux new-window -t supervise:3
tmux send-keys -t supervise:3  "./drseus.py -c $campaign3 @conf/lansce/supervise/pynq3_$cache3 --cmd 'supervise 0'" ENTER
tmux new-window -t supervise:4
tmux send-keys -t supervise:4  "./drseus.py -c $campaign7 @conf/lansce/supervise/pynq7_$cache7 --cmd 'supervise 0'" ENTER
tmux join-pane -s supervise:1 -t supervise:0
tmux join-pane -s supervise:2 -t supervise:0
tmux join-pane -s supervise:3 -t supervise:0
tmux select-layout -t supervise:0 tiled
tmux join-pane -s supervise:4 -t supervise:0
tmux select-layout -t supervise:0 tiled

tmux attach -t supervise
