#!/bin/sh

set -e

pushd ..

pushd src

python3 simics_config.py
python3 -m compileall -l -b .
rm -rf __pycache__
rm ./*.py
printf '#!/bin/bash\npython3 drseus.pyc "$@"' > drseus

pushd log
python3 -m compileall -l -b .
rm -rf __pycache__
rm ./*.py
popd

popd

rm -rf .git
rm .sublimelinterrc .gitignore
rm -rf scripts

popd
