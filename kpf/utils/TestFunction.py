from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)


class TestFunction(KPFTranslatorFunction):
    '''Test function.

    ARGS:
    =====
    '''
    @classmethod
    def pre_condition(cls, args):
        print(f'Pre-condition Arguments: {args}')

    @classmethod
    def perform(cls, args):
        print(f'Perform Arguments: {args}')

    @classmethod
    def post_condition(cls, args):
        print(f'Post-condition Arguments: {args}')

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('a', type=float,
                            help="Argument a")
        parser.add_argument('b', type=float,
                            help="Argument b")
        parser.add_argument('c', type=float,
                            help="Argument c")
        return super().add_cmdline_args(parser)
