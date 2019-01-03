#!/usr/bin/env python3
"""
Copyright (c) 2018 NSF Center for Space, High-performance, and Resilient Computing (SHREC)
University of Pittsburgh. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided
that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, 
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
OF SUCH DAMAGE.
"""


from compileall import compile_dir
from os import chdir, remove, walk
from os.path import abspath, dirname, join
from tarfile import open as open_tar

top_dir = dirname(dirname(abspath(__file__)))
chdir(top_dir)
compile_dir('src', force=True, quiet=1, legacy=True)

with open_tar('drseus.tar.gz', 'w:gz') as package:
    package.add('scripts/install_dependencies.sh', 'install_dependencies.sh')
    package.add('scripts/setup_environment.sh', 'setup_environment.sh')
    package.add('drseus.py')
    package.add('README.md')
    for root, dirs, files in walk(join(top_dir, 'src')):
        if 'migrations' not in root and '__pycache__' not in root:
            for file_ in files:
                if not file_.endswith('.py'):
                    package.add(join(root.replace(top_dir+'/', ''), file_))
                if file_.endswith('.pyc'):
                    remove(join(root, file_))
