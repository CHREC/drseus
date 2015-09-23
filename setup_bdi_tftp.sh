#!/bin/bash

pushd ~/
git clone git@gitlab.hcs.ufl.edu:F4/bdi3000-tftp.git
pushd bdi3000-tftp
./setup_bdi_tftp.sh
popd
popd
