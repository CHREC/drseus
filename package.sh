#!/bin/bash

mkdir simics-workspace
pushd simics-workspace
git clone git@gitlab.hcs.ufl.edu:F4/simics-p2020rdb
pushd simics-p2020rdb
rm -rf .git
popd
git clone git@gitlab.hcs.ufl.edu:F4/simics-a9x2
pushd simics-a9x2
rm -rf .git
popd
popd

rm .gitignore setup_apps.sh setup_bdi_tftp.sh setup_simics_workspace.sh
rm -rf .git

python3 simics_config.py
python3 -m compileall -l -b .
mv lextab.py lextab.bak
mv parsetab.py parsetab.bak
rm -rf __pycache__
rm ./*.py
mv lextab.bak lextab.py
mv parsetab.bak parsetab.py
touch drseus.sh
printf '#!/bin/bash\npython3 drseus.pyc "$@"' > drseus.sh
chmod +x drseus.sh

pushd log
python3 -m compileall -l -b .
rm -rf __pycache__
rm ./*.py
popd

rm package.sh
