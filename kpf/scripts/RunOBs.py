from pathlib import Path

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.scripts.RunOB import RunOB
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock


class RunOBs(KPFFunction):
    '''Script to run a list of OBs as scheduled cals.
    '''
    @classmethod
    def pre_condition(cls, args):
        # If specified obey the ALLOWSCHEDULEDCALS keyword
        if args.get('scheduled', False) == True:
            ALLOWSCHEDULEDCALS = ktl.cache('kpfconfig', 'ALLOWSCHEDULEDCALS')
            if ALLOWSCHEDULEDCALS.read(binary=True) == False:
                raise FailedPreCondition('ALLOWSCHEDULEDCALS is No')

    @classmethod
    def perform(cls, args):
        for file in args.get('files'):
            file = Path(file)
            try:
                OB = ObservingBlock(file)
            except Exception as e:
                log.error(f'Unable to parse OB from {file}')
                log.error(e)
                break
            if OB.validate():
                RunOB.execute({'waitforscript': True,
                               'scheduled': True},
                              OB=OB)
            else:
                log.error(f'OB from {file} was invalid, not executing OB')

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('files', nargs='*',
            help='The OB files to run')
        return super().add_cmdline_args(parser)
