#!/bin/sh -e

echo "host all all 192.168.0.0/24 trust" | sudo -u postgres tee /etc/postgresql/9.6/main/pg_hba.conf
echo "listen_addresses='*'" | sudo -u postgres tee /etc/postgresql/9.6/main/postgresql.conf
sudo service postgresql restart
