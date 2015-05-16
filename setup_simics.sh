#!/bin/bash

touch simics_license.sh
echo $'#!/bin/bash\n\nssh carlisle@sg-1.hcs.ufl.edu -L 2012:license.hcs.ufl.edu:40071' > simics_license.sh
chmod +x simics_license.sh

mkdir simics-workspace
cd simics-workspace
/opt/simics/simics-4.8/simics-4.8*/bin/workspace-setup
git clone git@gitlab.hcs.ufl.edu:F4/simics-p2020rdb
git clone git@gitlab.hcs.ufl.edu:F4/simics-vexpress-a9x4
