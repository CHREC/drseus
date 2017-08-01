#!/bin/sh -e

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
if ask 'disable caches for pynq0?' N; then
    cache0="off"
else
    cache0="on"
fi
printf "enter pynq1 campaign number: "
read -r campaign1
if ask 'disable caches for pynq1?' N; then
    cache1="off"
else
    cache1="on"
fi
printf "enter pynq2 campaign number: "
read -r campaign2
if ask 'disable caches for pynq2?' N; then
    cache2="off"
else
    cache2="on"
fi
printf "enter pynq3 campaign number: "
read -r campaign3
if ask 'disable caches for pynq3?' N; then
    cache3="off"
else
    cache3="on"
fi

tmux new-session -d -s supervise
tmux send-keys -t supervise:0 "./drseus.py -c $campaign0 @conf/lansce/supervise/pynq0_cache_$cache0 --cmd 'supervise 0'" ENTER
tmux new-window -t supervise:1
tmux send-keys -t supervise:1  "./drseus.py -c $campaign1 @conf/lansce/supervise/pynq1_cache_$cache1 --cmd 'supervise 0'" ENTER
tmux new-window -t supervise:2
tmux send-keys -t supervise:2  "./drseus.py -c $campaign2 @conf/lansce/supervise/pynq2_cache_$cache2 --cmd 'supervise 0'" ENTER
tmux new-window -t supervise:3
tmux send-keys -t supervise:3  "./drseus.py -c $campaign3 @conf/lansce/supervise/pynq3_cache_$cache3 --cmd 'supervise 0'" ENTER
tmux join-pane -s supervise:1 -t supervise:0
tmux join-pane -s supervise:2 -t supervise:0
tmux join-pane -s supervise:3 -t supervise:0
tmux select-layout -t supervise:0 tiled

tmux attach -t supervise
