from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.schedule import getSchedule


class GetScheduledPrograms(KPFFunction):
    '''

    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        return [entry['ProjCode'] for entry in getSchedule(**args)]

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('date', type=str,
            help="date")
        return super().add_cmdline_args(parser)
