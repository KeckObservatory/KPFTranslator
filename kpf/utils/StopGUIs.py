import os
import time
import subprocess
import re

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import GUI_list


class StopGUIs(KPFTranslatorFunction):
    '''Start KPF GUIs
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):

        for GUI in GUI_list:
            if GUI['cmd'][0] == 'kpf':
                GUIname = GUI['name']
                GUIscriptname = GUI['cmd'][2]
                status_cmd = GUI['cmd']
                status_cmd[1] = 'status'
                log.info(f"Getting status of '{GUIname}' GUI")
                gui_proc = subprocess.run(status_cmd,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)
                stdout = gui_proc.stdout.decode().strip()
                is_running = re.search('is running on', stdout)
                if is_running is not None:
                    stop_cmd = GUI['cmd']
                    stop_cmd[1] = 'stop'
                    log.info(f"Stopping '{GUIname}' GUI")
                    gui_proc = subprocess.Popen(stop_cmd,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
