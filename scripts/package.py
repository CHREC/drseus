#!/usr/bin/env python3

from compileall import compile_dir
from os import chdir, remove, walk
from os.path import abspath, dirname, join
from tarfile import open as open_tar

top_dir = dirname(dirname(abspath(__file__)))
chdir(top_dir)
compile_dir('src', force=True, quiet=1, legacy=True)

with open_tar('drseus.tar.gz', 'w:gz') as package:
    package.add('scripts/install_dependencies.sh', 'install_dependencies.sh')
    package.add('drseus.py')
    package.add('README.md')
    for root, dirs, files in walk(join(top_dir, 'src')):
        if 'migrations' not in root and '__pycache__' not in root:
            for file_ in files:
                if not file_.endswith('.py'):
                    package.add(join(root.replace(top_dir+'/', ''), file_))
                if file_.endswith('.pyc'):
                    remove(join(root, file_))
