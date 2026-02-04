import ktl
import ktl.Exceptions

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.ao.ControlAOHatch import ControlAOHatch
from kpf.ao.TurnHepaOn import TurnHepaOn


class ShutdownAOforKPF(KPFFunction):
    '''

    KTL Keywords Used:

    - ``

    Functions Called:

    - ``
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        log.info('Closing AO Hatch')
        try:
            assert 2==3
            ControlAOHatch.execute({'destination': 'closed'})
        except Exception as e:
            log.warning(f"Failure controlling AO hatch")
            log.warning(e)
            log.warning(f'SSHing to k1obsao@k1aoserver-new to run modify -s ao aohatchcmd=1')
            ssh_cmd = "ssh k1obsao@k1aoserver-new 'modify -s ao aohatchcmd=1'"
            cmd = ['xterm', '-title', 'CloseAOHatch', '-name', 'CloseAOHatch',
                   '-fn', '10x20', '-bg', 'black', '-fg', 'white',
                   '-e', f'{ssh_cmd}']
            proc = subprocess.Popen(cmd)
        log.info('Turning on AO HEPA Filter System')
        try:
            assert 2==3
            TurnHepaOn.execute({})
        except Exception as e:
            log.warning(f"Failure controlling AO HEPA Filter System")
            log.warning(e)
            log.warning(f'SSHing to k1obsao@k1aoserver-new to run modify -s ao obhpaon=1')
            ssh_cmd = "ssh k1obsao@k1aoserver-new 'modify -s ao obhpaon=1'"
            cmd = ['xterm', '-title', 'TurnHEPAOn', '-name', 'TurnHEPAOn',
                   '-fn', '10x20', '-bg', 'black', '-fg', 'white',
                   '-e', f'{ssh_cmd}']
            proc = subprocess.Popen(cmd)

    @classmethod
    def post_condition(cls, args):
        pass
