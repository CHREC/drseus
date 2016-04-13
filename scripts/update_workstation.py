#!/usr/bin/env python3

from subprocess import check_call, check_output
from os.path import abspath, dirname

directory = dirname(dirname(abspath(__file__)))

files = check_output(['git', 'status', '-s'],
                     cwd=directory,
                     universal_newlines=True)
ignored_files = []
for file in files.split('\n'):
    file = file.split()
    if file:
        if file[0] in ('A', 'M', 'AM', 'MM'):
            check_call(['scp', file[1], 'drseus:drseus/'+file[1]],
                       cwd=directory)
        else:
            ignored_files.append(file[1])

if ignored_files:
    print('ignored files: '+', '.join(ignored_files))
