import json
from os.path import abspath, dirname, join

from targets import calculate_target_bits

directory = dirname(abspath(__file__))

with open(join(directory, 'jtag.json'), 'r') as data:
    jtag_targets = json.load(data)
calculate_target_bits(jtag_targets)

# with open(join(directory, 'simics.json'), 'r') as data:
#     simics_targets = json.load(data)
# calculate_target_bits(simics_targets)

from targets.p2020.simics import targets as simics_targets
calculate_target_bits(simics_targets)

# TODO: add ETSEC_TBI and Security targets
# p2020_ccsrbar = 0xFFE00000
