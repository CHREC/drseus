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
