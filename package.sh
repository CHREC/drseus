#!/bin/bash

set -e

python3 simics_config.py
python3 -m compileall -l -b .
rm -rf __pycache__
rm ./*.py
touch drseus.sh
printf '#!/bin/bash\npython3 drseus.pyc "$@"' > drseus.sh
chmod +x drseus.sh

pushd log
python3 -m compileall -l -b .
rm -rf __pycache__
rm ./*.py
popd

rm -rf .git
rm .sublimelinterrc .gitignore setup_apps.sh setup_simics_workspace.sh \
   package.sh
