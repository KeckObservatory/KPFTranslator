import os
import time
import subprocess
import re
import socket

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.utils.StartGUIs import GUI_list


def find_process(process, server='kpf'):
    if isinstance(process, list):
        process = ' '.join(process)
    prefix_cmd = []
    if socket.gethostname() != server:
        prefix_cmd = ['ssh', server]
    psout = subprocess.run(prefix_cmd + ['ps', '-ef'], stdout=subprocess.PIPE)
    psout = psout.stdout.decode().split('\n')
    process_id = None
    for line in psout:
        if line.find(process) > 0:
            process_id = line.split()[1]
            break
    if process_id is None:
        log.debug(f'Could not find process: {process}')
    return process_id


def kill_process(process, server='kpf'):
    if isinstance(process, list):
        process = ' '.join(process)
    prefix_cmd = []
    if socket.gethostname() != server:
        prefix_cmd = ['ssh', server]
    process_id = find_process(process, server=server)
    if process_id is not None:
        kill_cmd = prefix_cmd + ['kill', process_id]
        log.debug(f'Running: {" ".join(kill_cmd)}')
        killout = subprocess.run(kill_cmd, stdout=subprocess.PIPE)
        if killout.returncode > 0:
            log.warning(f'{" ".join(kill_cmd)} failed')


class StopGUIs(KPFTranslatorFunction):
    '''Start KPF GUIs
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

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
                    stopout = subprocess.run(stop_cmd,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
                    log.debug(f"{stopout.returncode}")
                    log.debug(f"{stopout.stdout.decode()}")
                    log.debug(f"{stopout.stderr.decode()}")
                else:
                    log.info(f"{GUIname} is not running")
                    log.debug(f"{stdout}")
            else:
                kill_process(GUI['cmd'], server='kpf')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
