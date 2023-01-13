import os
import time
import subprocess
from datetime import datetime, timedelta
import re

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


def get_window_list(env=None):
    wmctrl_cmd = ['wmctrl', '-l']
    if env is not None:
        wmctrl_proc = subprocess.run(wmctrl_cmd, stdout=subprocess.PIPE, env=env)
    else:
        wmctrl_proc = subprocess.run(wmctrl_cmd, stdout=subprocess.PIPE)
    wmctrl_list = wmctrl_proc.stdout.decode().strip('\n').split('\n')
    patt = "(\w+)\s+([\+\-\d]+)\s+([\.\w\/]+)\s+([\w\s\-\(\)]+)"
    matches = [re.match(patt, line) for line in wmctrl_list]
    window_names = [m.group(4 ) for m in matches if m is not None]
    if len(wmctrl_list) > len(window_names):
        log.error(f"Unmatched window")
        log.error(wmctrl_proc.stdout.decode().strip('\n'))
        log.error(window_names)
    return window_names


def waitfor_window_to_appear(name, env=None, timeout=20):
    start = datetime.now()
    window_names = get_window_list(env=env)
    while name not in window_names\
          and (datetime.now()-start).total_seconds() < timeout:
        log.debug(f"Waiting for '{name}' to appear")
        time.sleep(3)
        window_names = get_window_list(env=env)
    return name in window_names


class StartGUIs(KPFTranslatorFunction):
    '''Start KPF GUIs
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # Get DISPLAY varibales
        env = os.environ
        uidisp = {}
        for dispno in [0, 1, 2, 3]:
            uidisp_proc = subprocess.run(['uidisp', f'{dispno}'], env=env,
                                         stdout=subprocess.PIPE)
            uidisp[dispno] = uidisp_proc.stdout.decode().strip('\n')

        GUIs = [
                {'name': 'KPF Fiber Injection Unit (FIU)',
                 'cmd': ['/kroot/rel/default/bin/fiu_gui'],
                 'dispno': 1,
                 'position': '0,80,165,-1,-1'},
                {'name': 'KPF Exposure Meter',
                 'cmd': ['/kroot/rel/default/bin/expmeter_gui'],
                 'dispno': 1,
                 'position': '0,5,665,-1,-1'},
                {'name': 'SAOImage kpfds9',
                 'cmd':  ['kpf', 'start', 'kpfds9'],
                 'dispno': 2,
                 'position': '0,1,55,1800,900'},
#                 {'name': 'KECK 1 FACSUM',
#                  'cmd':  ['xterm', '-T', 'xterm KECK 1 FACSUM', '-e', 'ssh', '-X', 'k1ruts@vm-k1obs', 'Facsum', '-k1'],
#                  'dispno': 3,
#                  'position': '0,250,10,-1,-1'},
#                 {'name': 'KECK 1 MET',
#                  'cmd':  ['xterm', '-T', 'xterm KECK 1 MET', '-e', 'ssh', '-X', 'k1ruts@vm-k1obs', 'Met', '-k1'],
#                  'dispno': 3,
#                  'position': '0,250,535,-1,-1'},
#                 {'name': 'MAGIQ - Observer UI',
#                  'cmd':  ['xterm', '-T', 'xterm MAGIQ - Observer UI', '-e', 'ssh', '-X', 'k1ruts@k1-magiq-server', 'magiq', 'start', 'ObserverUI'],
#                  'dispno': 3,
#                  'position': '0,500,15,-1,-1'},
                 ]

        # Start GUIs if needed
        for GUI in GUIs:
            # Find out of GUIs are Running
            env['DISPLAY'] = uidisp[GUI['dispno']]
            window_names = get_window_list(env=env)
            GUIname = GUI['name']
            if GUIname not in window_names:
                log.info(f"Starting '{GUIname}' GUI")
                gui_proc = subprocess.Popen(GUI['cmd'], env=env,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
                success = waitfor_window_to_appear(GUIname, env=env)
            else:
                log.info(f"Existing '{GUIname}' window found")
            if GUI.get('position', None) is not None:
                log.info(f"Positioning '{GUIname}' GUI")
                wmctrl_cmd = ['wmctrl', '-r', f'"{GUIname}"', '-e', GUI['position']]
                log.debug(f"  Running: {' '.join(wmctrl_cmd)}")
                wmctrl_proc = subprocess.run(' '.join(wmctrl_cmd), env=env, shell=True)
                if GUI['cmd'][0] == 'xterm':
                    xterm_title = GUI['cmd'][2]
                    success = waitfor_window_to_appear(xterm_title, env=env)
                    log.info(f"Minimizing '{xterm_title}'")
                    wmctrl_cmd = ['wmctrl', '-r', xterm_title, '-b', 'add,hidden']
                    wmctrl_proc = subprocess.run(' '.join(wmctrl_cmd), env=env, shell=True)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
