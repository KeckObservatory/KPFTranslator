import json
import requests

import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


##-------------------------------------------------------------------------
## RetrieveOB
##-------------------------------------------------------------------------
class RetrieveOB(KPFFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args):
        url = config.get('Database', 'url', fallback=None)
        if url is None:
            raise FailedPreCondition('Database URL is not defined in configuration')
        OBid = args.get('OBid', None)
        if OBid is None:
            raise FailedPreCondition('OBid must be provided')

    @classmethod
    def perform(cls, args):
        url = config.get('Database', 'url')
        OBid = args.get('OBid', None)
        query = f'getKPFObservingBlock?id={OBid}'
        r = requests.get(f"{url}{query}")
        OBdict = json.loads(r.text)
        print(OBdict.keys())

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('OBid', type=str,
                            help='The unique identifier for the OB to retrieve?')
        return super().add_cmdline_args(parser)
