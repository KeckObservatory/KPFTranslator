import os
import time
import subprocess

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
    wmctrl_list = wmctrl_proc.stdout.decode().split('\n')
    window_names = [w[18:].strip() for w in wmctrl_list]
    return window_names


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

        # Find out of GUIs are Running
        window_names = get_window_list()

        GUIs = [{'name': 'KPF Fiber Injection Unit (FIU)',
                 'cmd': '/kroot/rel/default/bin/fiu_gui',
                 'dispno': 0,
                 'position': '0,5,165,-1,-1'},
                 {'name': 'KPF Exposure Meter',
                 'cmd': '/kroot/rel/default/bin/expmeter_gui',
                 'dispno': 0,
                 'position': '0,5,665,-1,-1'},
                 ]

        # Start GUIs if needed
        for GUI in GUIs:
            GUIname = GUI['name']
            if GUIname not in window_names:
                log.info(f"Starting {GUIname} GUI")
                env['DISPLAY'] = uidisp[GUI['dispno']]
                gui_proc = subprocess.Popen([GUI['cmd']], env=env)
                window_names = get_window_list(env=env)
                while GUI['name'] not in window_names:
                    log.info(f"Waiting for {GUIname} to appear")
                    time.sleep(2)
                    window_names = get_window_list(env=env)
                log.info(f"Positioning {GUIname} GUI")
                wmctrl_cmd = ['wmctrl', '-r', f'"{GUIname}"', '-e', GUI['position']]
                wmctrl_proc = subprocess.run(' '.join(wmctrl_cmd), env=env, shell=True)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
