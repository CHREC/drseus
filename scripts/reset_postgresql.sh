#!/bin/sh

sudo pg_dropcluster --stop 9.4 main
sudo pg_createcluster 9.4 main
sudo service postgresql restart
