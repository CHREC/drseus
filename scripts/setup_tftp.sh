#!/bin/bash

sudo apt-get install --yes xinetd tftpd tftp

dir=$(pwd)
usr=$USER

sudo sh -c "echo \"service tftp
{
	socket_type = dgram
	protocol = udp
	wait = yes
	user = ${usr}
	server = /usr/sbin/in.tftpd
	server_args = -s ${dir}
	disable = no
	per_source = 11
	cps = 100 2
	flags = IPv4
}\" > /etc/xinetd.d/tftp"

sudo service xinetd stop
sudo service xinetd start
