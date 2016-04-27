#!/bin/sh

set -e

cd "$(dirname "$(dirname "$(readlink -f "$0")")")"

./drseus.py @conf/sample/a9
./drseus.py @conf/sample/p2020
./drseus.py @conf/sample/a9 -s
./drseus.py @conf/sample/p2020 -s
