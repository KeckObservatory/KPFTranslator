from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.observatoryAPIs.GetScheduledPrograms import GetScheduledPrograms
from kpf.observatoryAPIs.GetObservingBlocksByProgram import GetObservingBlocksByProgram


##-------------------------------------------------------------------------
## GetAllKPFCCObservingBlocks
##-------------------------------------------------------------------------
class GetKPFCCObservingBlocks(KPFFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        log.info('Getting OBs for all KPF-CC programs this semester')
        OBs = []
        classical, cadence = GetScheduledPrograms.execute({'semester': 'current'})
        progIDs = set([p['ProjCode'] for p in cadence])
        # Iterate of KPF-CC programIDs and retrieve their OBs from DB
        for i,progID in enumerate(progIDs):
            log.debug(f'Retrieving OBs for {progID}')
            programOBs = GetObservingBlocksByProgram.execute({'program': progID})
            OBs.extend(programOBs)

        return OBs

    @classmethod
    def post_condition(cls, args):
        pass
