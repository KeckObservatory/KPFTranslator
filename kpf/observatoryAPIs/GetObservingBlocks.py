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
        if args.get('show_history', False):
            print(f'# Observing History for {OBs[0].summary()}')
            for i,h in enumerate(OBs[0].History):
                print(f"- Observer: {h['observer']}")
                print(f"  Start Times: {h['exposure_start_times']}")
                print(f"  Exposure Times: {h['exposure_times']}")
        return OBs

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('OBid', type=str,
                            help='The unique identifier for the OB to retrieve.')
        parser.add_argument('--history', '--show_history', dest="show_history",
            default=False, action="store_true",
            help='Print history to screen?')
        return super().add_cmdline_args(parser)


