#!/bin/sh

set -e

cd "$(dirname "$(dirname "$(readlink -f "$0")")")"

tmux new-session -d -s inject
tmux new-window -t inject:1
tmux send-keys -t inject:1 "./drseus.py -c 1 @conf/a9 i -p 4" ENTER
tmux new-window -t inject:2
tmux send-keys -t inject:2  "./drseus.py -c 2 @conf/p2020 i" ENTER
tmux new-window -t inject:3
tmux send-keys -t inject:3  "./drseus.py -c 2 @conf/p2021 i" ENTER
tmux new-window -t inject:4
tmux send-keys -t inject:4  "./drseus.py -c 3 i -p 4" ENTER
tmux new-window -t inject:5
tmux send-keys -t inject:5  "./drseus.py -c 4 i -p 4" ENTER
