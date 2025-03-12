import os
import datetime
import json
import requests
import urllib3
urllib3.disable_warnings() # We're going to do verify=False, so ignore warnings

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock


##-------------------------------------------------------------------------
## query_database
##-------------------------------------------------------------------------
def query_database(query, params):
    url = cfg.get('Database', 'url')
    log.debug(f"Running database query: {query}")
    log.debug(params)
    if 'hash' not in params.keys():
        params['hash'] = os.getenv('APIHASH', default='')
    r = requests.post(f"{url}{query}", json=params, verify=False)
    try:
        result = json.loads(r.text)
        log.debug(f'{query} retrieved {len(result)} results')
    except Exception as e:
        log.error(f'Failed to parse result:')
        log.error(r.text)
        log.error(e)
        result = None
    if type(result) == dict:
        success = result.get('success', None)
        if success == 'ERROR':
            log.error('success: {success}')
            msg = result.get('message', None)
            if msg: log.error('Message: {msg}')
            details = result.get('details', None)
            if details: log.error('Details: {details}')
            result = None
    return result


def get_OBs_from_database(params):
    result = query_database('getKPFObservingBlock', params)
    if result is None:
        return []
    OBs = []
    for i,entry in enumerate(result):
        try:
            OB = ObservingBlock(entry)
        except Exception as e:
            print('Unable to parse result in to an ObservingBlock')
            log.error('Unable to parse result in to an ObservingBlock')
            log.debug(entry)
            log.error(e)
        else:
            if OB.validate():
                print('OB is valid')
                OBs.append(OB)
            else:
                print('OB is invalid')

    log.debug(f'get_OBs_from_database parsed {len(OBs)} ObservingBlocks')
    return OBs


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
#         params = {'id': ['67acdce3eac565e90ea5249b',
#                          '67bce24b163351af181eb2d0',
#                          '67c0c7e86d1b806b332847ef',
#                          ]}
        OBs = get_OBs_from_database(params)
        return OBs

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('OBid', type=str,
                            help='The unique identifier for the OB to retrieve.')
        return super().add_cmdline_args(parser)


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
        semester = args.get('semester', None)
        if semester is None:
            now = datetime.datetime.now()
            if now.month > 1 and now.month < 8:
                semester = f"{now.year}A"
            else:
                semester = f"{now.year}B"
        program = args.get('program', None)
        if program is None:
            return
        params = {'semid': f"{semester}_{program}"}
        OBs = get_OBs_from_database(params)
        return OBs

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('semester', type=str,
                            help='The semester for the associated program ID.')
        parser.add_argument('program', type=str,
                            help='The program ID to retrieve OBs for.')
        return super().add_cmdline_args(parser)
