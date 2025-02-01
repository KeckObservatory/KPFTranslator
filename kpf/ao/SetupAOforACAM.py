import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.ao.SetAFMtoMirror import SetAFMtoMirror
from kpf.ao.SetAFStoNGS import SetAFStoNGS


class SetupAOforACAM(KPFFunction):
    '''Set up AO in the safe mode for ACAM operation to assist KPF acquisition

    Scripts Called:

    - `kpf.ao.SetAFMtoMirror`
    - `kpf.ao.SetAFStoNGS`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        log.info('Set AFM to Mirror')
        SetAFMtoMirror.execute({})

        log.info('Set AFS to NGS')
        SetAFStoNGS.execute({})

    @classmethod
    def post_condition(cls, args):
        pass