#!/bin/sh

set -e

cd "$(dirname "$(dirname "$(readlink -f "$0")")")"

./drseus.py ls

printf "enter zynq0 campaign number: "
read -r zynq0
printf "enter zynq1 campaign number: "
read -r zynq1
printf "enter zynq2 campaign number: "
read -r zynq2
printf "enter zynq3 campaign number: "
read -r zynq3

tmux new-session -d -s supervise
tmux send-keys -t supervise:0 "./drseus.py -c $zynq0 @conf/lansce/zynq0 supervise" ENTER
tmux new-window -t supervise:1
tmux send-keys -t supervise:1  "./drseus.py -c $zynq1 @conf/lansce/zynq1 supervise" ENTER
tmux new-window -t supervise:2
tmux send-keys -t supervise:2  "./drseus.py -c $zynq2 @conf/lansce/zynq2 supervise" ENTER
tmux new-window -t supervise:3
tmux send-keys -t supervise:3  "./drseus.py -c $zynq3 @conf/lansce/zynq3 supervise" ENTER
tmux join-pane -s supervise:1 -t supervise:0
tmux join-pane -s supervise:2 -t supervise:0
tmux join-pane -s supervise:3 -t supervise:0
tmux select-layout -t supervise:0 tiled
