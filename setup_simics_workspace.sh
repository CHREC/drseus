#!/bin/bash

mkdir simics-workspace
pushd simics-workspace
/opt/simics/simics-4.8/simics-4.8*/bin/workspace-setup
git clone git@gitlab.hcs.ufl.edu:F4/simics-p2020rdb
git clone git@gitlab.hcs.ufl.edu:F4/simics-a9x2
popd
