import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.ao.SetAFMtoMirror import SetAFMtoMirror
from kpf.ao.SetAFStoNGS import SetAFStoNGS


class SetupAOforACAM(KPFTranslatorFunction):
    '''Set up AO in the safe mode for ACAM operation to assist KPF acquisition

    Scripts Called:

    - `kpf.ao.SetAFMtoMirror`
    - `kpf.ao.SetAFStoNGS`
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        log.info('Set AFM to Mirror')
        SetAFMtoMirror.execute({})

        log.info('Set AFS to NGS')
        SetAFStoNGS.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass