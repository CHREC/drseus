#!/bin/sh

set -e

cd "$(dirname "$(dirname "$(readlink -f "$0")")")"

./drseus.py ls

printf "enter pynq0 campaign number: "
read -r pynq0
printf "enter pynq1 campaign number: "
read -r pynq1
printf "enter pynq2 campaign number: "
read -r pynq2
printf "enter pynq3 campaign number: "
read -r pynq3

tmux new-session -d -s supervise
tmux send-keys -t supervise:0 "./drseus.py -c $pynq0 @conf/lansce/pynq0 supervise" ENTER
tmux new-window -t supervise:1
tmux send-keys -t supervise:1  "./drseus.py -c $pynq1 @conf/lansce/pynq1 supervise" ENTER
tmux new-window -t supervise:2
tmux send-keys -t supervise:2  "./drseus.py -c $pynq2 @conf/lansce/pynq2 supervise" ENTER
tmux new-window -t supervise:3
tmux send-keys -t supervise:3  "./drseus.py -c $pynq3 @conf/lansce/pynq3 supervise" ENTER
tmux join-pane -s supervise:1 -t supervise:0
tmux join-pane -s supervise:2 -t supervise:0
tmux join-pane -s supervise:3 -t supervise:0
tmux select-layout -t supervise:0 tiled

tmux attach -t supervise
