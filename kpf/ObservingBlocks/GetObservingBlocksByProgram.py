import os
import json
import requests

import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock


##-------------------------------------------------------------------------
## GetObservingBlocksByProgram
##-------------------------------------------------------------------------
class GetObservingBlocksByProgram(KPFFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args):
        url = cfg.get('Database', 'url', fallback=None)
        if url is None:
            raise FailedPreCondition('Database URL is not defined in configuration')
        program = args.get('program', None)
        if program is None:
            raise FailedPreCondition('Program must be provided')

    @classmethod
    def perform(cls, args):
        url = cfg.get('Database', 'url')
        program = args.get('program', '')
        apihash = os.getenv('APIHASH', default='')
        query = f'getAllObservingBlocks'
        params = {'semid': program,
                  'hash': apihash}
        r = requests.get(f"{url}{query}", params=params)
        result = json.loads(r.text)
        OBs = result.get('observing_blocks', [])
        print(f"Retrieved {len(OBs)} OBs")
        for OBdict in OBs:
            print(OBdict.keys())
            print(OBdict.get('target', ''))
            print(OBdict.get('Observations', []))
            print()


    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('program', type=str,
                            help='The program ID to retrieve OBs for.')
        return super().add_cmdline_args(parser)
