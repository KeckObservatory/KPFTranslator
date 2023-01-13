import os
import time
import subprocess
from datetime import datetime, timedelta
import re
from astropy.table import Table

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
#         for dispno in [0, 1, 2, 3]:
#             uidisp_proc = subprocess.run(['uidisp', f'{dispno}'], env=env,
#                                          stdout=subprocess.PIPE)
#             uidisp[dispno] = uidisp_proc.stdout.decode().strip('\n')

        kvncstatus_proc = subprocess.run(['kvncstatus'], env=env,
                                         stdout=subprocess.PIPE)
        kvncstatus = Table.read(kvncstatus_proc.stdout.decode(), format='ascii')
        username = os.getlogin()
        display = {'control0':  kvncstatus[kvncstatus['Desktop'] == f'kpf-{username}-control0']['Display'][0],
                   'control1':  kvncstatus[kvncstatus['Desktop'] == f'kpf-{username}-control1']['Display'][0],
                   'control2':  kvncstatus[kvncstatus['Desktop'] == f'kpf-{username}-control2']['Display'][0],
                   'telstatus':  kvncstatus[kvncstatus['Desktop'] == f'kpf-{username}-telstatus']['Display'][0],
                   }

        GUIs = [
                # Control0 for DSI
                # Control1
                # - add Spectrograph GUI
                {'name': 'KPF Fiber Injection Unit (FIU)',
                 'cmd': ['/kroot/rel/default/bin/fiu_gui'],
                 'display': 'control1',
                 'position': '0,80,50,-1,-1'},
                {'name': 'KPF Exposure Meter',
                 'cmd': ['/kroot/rel/default/bin/expmeter_gui'],
                 'display': 'control1',
                 'position': '0,5,550,-1,-1'},
                # Control2
                # - add Eventsounds
                {'name': 'SAOImage kpfds9',
                 'cmd':  ['kpf', 'start', 'kpfds9'],
                 'display': 'control2',
                 'position': '0,1,55,1800,900'},
                # Telstatus
                # - add Tip Tilt GUI
                {'name': 'xshow_TipTilt',
                 'cmd':  ['/home/kpfeng/bin/xshow_tiptilt'],
                 'display': 'telstatus',
                 'position': '0,1020,5,200,310'},
                {'name': 'KECK 1 FACSUM',
                 'cmd':  ['xterm', '-T', 'xterm KECK 1 FACSUM', '-e', 'ssh', '-X', 'k1ruts@vm-k1obs', 'Facsum', '-k1'],
                 'display': 'telstatus',
                 'position': '0,250,10,-1,-1'},
                {'name': 'KECK 1 MET',
                 'cmd':  ['xterm', '-T', 'xterm KECK 1 MET', '-e', 'ssh', '-X', 'k1ruts@vm-k1obs', 'Met', '-k1'],
                 'display': 'telstatus',
                 'position': '0,250,535,-1,-1'},
                {'name': 'MAGIQ - Observer UI',
                 'cmd':  ['xterm', '-T', 'xterm MAGIQ - Observer UI', '-e', 'ssh', '-X', 'k1ruts@k1-magiq-server', 'magiq', 'start', 'ObserverUI'],
                 'display': 'telstatus',
                 'position': '0,500,15,-1,-1'},
                 ]

        # Start GUIs if needed
        for GUI in GUIs:
            # Find out of GUIs are Running
            log.debug(f"Setting DISPLAY to kpf{display[GUI['display']]}")
            env['DISPLAY'] = f"kpf{display[GUI['display']]}"
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
            time.sleep(2)
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
