#!/bin/bash

mkdir simics-workspace
# pushd simics-workspace
# git clone git@gitlab.hcs.ufl.edu:F4/simics-p2020rdb
# pushd simics-p2020rdb
# rm -rf .git
# popd
# git clone git@gitlab.hcs.ufl.edu:F4/simics-a9x2
# pushd simics-a9x2
# rm -rf .git
# popd
# popd

rm .gitignore setup_apps.sh setup_bdi_tftp.sh setup_simics.sh
rm -rf .git

python -m compileall -l .
rm ./*.py
chmod +x drseus.pyc

pushd django-logging/drseus_logging
python -m compileall -l .
rm ./*.py
popd

rm package.sh
