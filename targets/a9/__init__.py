import json
from os.path import abspath, dirname, join

from targets import calculate_target_bits

directory = dirname(abspath(__file__))

with open(join(directory, 'jtag.json'), 'r') as data:
    jtag_targets = json.load(data)
calculate_target_bits(jtag_targets)

with open(join(directory, 'simics.json'), 'r') as data:
    simics_targets = json.load(data)
calculate_target_bits(simics_targets)

# TODO: are sp and lr in CPU copies of others? (jtag)

# RAZ: Read-As-Zero
# WI: Write-ignored
# RAO: Read-As-One
# RAZ/WI: Read-As-Zero, Writes Ignored
# RAO/SBOP: Read-As-One, Should-Be-One-or-Preserved on writes.
# RAO/WI: Read-As-One, Writes Ignored
# RAZ/SBZP: Read-As-Zero, Should-Be-Zero-or-Preserved on writes
# SBO: Should-Be-One
# SBOP: Should-Be-One-or-Preserved
# SBZ: Should-Be-Zero
# SBZP: Should-Be-Zero-or-Preserved
