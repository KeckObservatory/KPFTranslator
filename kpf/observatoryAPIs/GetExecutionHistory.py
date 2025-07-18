from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.observatoryAPIs import getObservingBlockHistory


##-------------------------------------------------------------------------
## GetExecutionHistory
##-------------------------------------------------------------------------
class GetExecutionHistory(KPFFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        utdate = args.get('utdate', 'today')
        return getObservingBlockHistory(utdate=utdate)

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('utdate', type=str, default='today',
                            help='The UT date to retrieve.')
        return super().add_cmdline_args(parser)
