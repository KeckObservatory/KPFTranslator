#! /kroot/rel/default/bin/kpython3

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
