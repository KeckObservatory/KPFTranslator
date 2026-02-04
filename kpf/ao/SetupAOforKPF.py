import subprocess

import ktl
import ktl.Exceptions

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.ao.SetAORotatorManual import SetAORotatorManual
from kpf.ao.SetAORotator import SetAORotator
from kpf.ao.TurnHepaOff import TurnHepaOff
from kpf.ao.SetAODCStoSIM import SetAODCStoSIM
from kpf.ao.SendPCUtoHome import SendPCUtoHome
from kpf.ao.SendPCUtoKPF import SendPCUtoKPF
from kpf.ao.TurnLightSourceOff import TurnLightSourceOff


class SetupAOforKPF(KPFFunction):
    '''Set up AO in the safe mode for KPF operation

    - Set AO roator in Manual mode
    - Set AO rotator to 0 deg
    - Turn off HEPA
    - Set AO in DCS sim mode
    - Home PCU
    - Move PCU to the KPF position
    - Open AO hatch

    KTL Keywords Used:

    - `ao.PCSFNAME`

    Functions Called:

    - `kpf.ao.SetAORotatorManual`
    - `kpf.ao.SetAORotator`
    - `kpf.ao.TurnHepaOff`
    - `kpf.ao.SetAODCStoSIM`
    - `kpf.ao.TurnLightSourceOff`
    - `kpf.ao.SendPCUtoHome`
    - `kpf.ao.SendPCUtoKPF`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):

        try:
            assert 2 == 3
            log.info('Set AO rotator to Manual')
            SetAORotatorManual.execute({})
    
            log.info('Set AO rotator to 0 deg')
            SetAORotator.execute({'dest': 0})
    
            log.info('Turn off HEPA')
            TurnHepaOff.execute({})
    
            log.info('Set AO in DCS sim mode')
            SetAODCStoSIM.execute({})
    
            log.info('Turn K1 AO light source off')
            TurnLightSourceOff.execute({})
    
            PCSstagekw = ktl.cache('ao', 'PCSFNAME')
            if PCSstagekw.read() != 'kpf':
                log.info('Move PCU to KPF')
                SendPCUtoKPF.execute({})
        except Exception as e:
            log.warning('SetupAOforKPF failed.')
            log.warning(e)
            log.warning(f'SSHing to k1obsao@k1aoserver-new to run kpfStart.csh')
            ssh_cmd = 'ssh k1obsao@k1aoserver-new kpfStart.csh'
            cmd = ['xterm', '-title', 'SetupAOforKPF', '-name', 'SetupAOforKPF',
                   '-fn', '10x20', '-bg', 'black', '-fg', 'white',
                   '-e', f'{ssh_cmd}']
            proc = subprocess.Popen(cmd)

    @classmethod
    def post_condition(cls, args):
        pass
