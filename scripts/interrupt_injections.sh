#!/bin/sh

set -e

tmux send-keys -t inject:1 C-c
tmux send-keys -t inject:2 C-c
tmux send-keys -t inject:3 C-c
tmux send-keys -t inject:4 C-c
