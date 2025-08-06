from pathlib import Path
import datetime

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.observatoryAPIs.GetScheduledPrograms import GetScheduledPrograms
from kpf.observatoryAPIs.GetObservingBlocksByProgram import GetObservingBlocksByProgram
from kpf.observatoryAPIs import get_semester_dates


##-------------------------------------------------------------------------
## GetKPFCCObservingBlocks
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
        log.info(f'Retrieved {len(OBs)} OBs in KPF-CC programs')
        # Save to files if requested
        if args.get('save', False) == True:
            semester, start, end = get_semester_dates(datetime.datetime.now())
            OBpath = Path('/s/sdata1701/OBs/KPFCC') / semester
            if OBpath.exists() is False:
                OBpath.mkdir(mode=0o777)
            log.info(f'Writing {len(OBs)} OBs to disk at: {OBpath}')
            for OB in OBs:
                OBfile = OBpath / f"{str(OB.Target.TargetName).replace(' ', '_')}.yaml"
                log.debug(f'  Writing: {OBfile.name}')
                OB.write_to(OBfile, overwrite=True)
        else:
            return OBs

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('--save', dest="save",
            default=False, action="store_true",
            help='Save OBs to disk?')
        return super().add_cmdline_args(parser)
