#! /kroot/rel/default/bin/kpython3

'''Script to build executable files for each entry in the KPFTranslator
linking table. This makes it so that the commands can be tab completed on the
command line.  So for example, the KPFTranslator function `StartGUIs` which
would normally be invoked via `kpfdo StartGUIs` can now also be invoked by
`kpfStartGUIs` (which can be tab completed, because it is an executable file in
the path).

This is currently meant to be run by the kpfeng user and will put scripts in
~kpfeng/bin/kpftranslator_scripts/, but the intention is to later change this
to be in KROOT.
'''

import os
import stat
from pathlib import Path
import subprocess

output = subprocess.run(['kpfdo', '-l'], stdout=subprocess.PIPE)
binpath = Path('~/bin/kpftranslator_scripts').expanduser()


for entry in output.stdout.decode().split('\n'):
    if entry != '':
        contents = ['#! /bin/csh', f'kpfdo {entry} $*']
        filename = binpath / f"kpf{entry}"
        with open(filename, 'w') as f:
            f.write('\n'.join(contents))
        new_permissions = os.stat(f"{filename}").st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        os.chmod(f"{filename}", new_permissions)
