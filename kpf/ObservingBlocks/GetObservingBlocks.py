from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.ObservingBlocks import query_database
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock


##-------------------------------------------------------------------------
## GetObservingBlock
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
#         params = {'id': ['67acdce3eac565e90ea5249b',
#                          '67bce24b163351af181eb2d0',
#                          '67c0c7e86d1b806b332847ef',
#                          ]}
        OBs = query_database(query='getKPFObservingBlock', params=params)
        return OBs

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('OBid', type=str,
                            help='The unique identifier for the OB to retrieve.')
        return super().add_cmdline_args(parser)
