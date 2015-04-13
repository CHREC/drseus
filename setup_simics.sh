#!/bin/bash

touch simics_license.sh
echo $'#!/bin/bash\n\nssh carlisle@sg-1.hcs.ufl.edu -L 2012:license.hcs.ufl.edu:40071' > simics_license.sh
chmod +x simics_license.sh

mkdir simics-workspace
cd simics-workspace
/opt/simics/simics-4.6/simics-4.6*/bin/workspace-setup
git clone https://ed4@bitbucket.org/ed4/p2020rdb-simics.git
