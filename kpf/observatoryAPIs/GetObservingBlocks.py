from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.observatoryAPIs import get_OBs_from_KPFCC_API

##-------------------------------------------------------------------------
## GetObservingBlocks
##-------------------------------------------------------------------------
class GetObservingBlocks(KPFFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args):
        OBid = args.get('OBid', None)
        if OBid is None:
            raise FailedPreCondition('OBid must be provided')

    @classmethod
    def perform(cls, args):
        params = {'id': args.get('OBid', '')}
        OBs = get_OBs_from_KPFCC_API(params)
        return OBs

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('OBid', type=str,
                            help='The unique identifier for the OB to retrieve.')
        return super().add_cmdline_args(parser)


