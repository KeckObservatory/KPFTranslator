from pathlib import Path

from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.scripts.RunOB import RunOB
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock


class RunOBs(KPFFunction):
    '''Script to run a list of OBs as scheduled cals.
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        for file in args.get('files'):
            file = Path(file)
            try:
                OB = ObservingBlock(file)
            except Exception as e:
                print(f'ERROR: Unable to parse OB from {file}')
                print(e)
                break
            if OB.validate():
                RunOB.execute({'waitforscript': True,
                               'scheduled': True},
                              OB=OB)
            else:
                print(f'ERROR: OB from {file} was invalid, not executing OB')

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('files', nargs='*',
            help='The OB files to run')
        return super().add_cmdline_args(parser)
