import os
import sys
import time
import datetime
import json
import requests
import numpy as np

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.ObservingBlocks.GetObservingBlocks import query_database


##-------------------------------------------------------------------------
## SubmitObserverComment
##-------------------------------------------------------------------------
class SubmitObserverComment(KPFFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args):
        OBid = args.get('OBid', None)
        if OBid is None:
            raise FailedPreCondition('OBid must be provided')

    @classmethod
    def perform(cls, args):
        log.info(f"Running {cls.__name__}")
        params = {'id': args.get('OBid', ''),
                  'observer': args.get('observer', ''),
                  'comment': args.get('comment', ''),
                  }

        # For testing
#         comments = ['an observer comment', 'another comment', 'this is a lot of comments for a single OB!',
#                     'This is a long soliloquy on the observing conditions during this observation which is here to make sure we do not have overly restrictive string length limits somewhere in the system.',
#                     "For completeness, a check on various inconvienient characters:\nJohn O'Meara, Cecilia Payne-Gaposchkin, are question marks ok? (should I even ask?) [perhaps not] {right?}"]
#         params["comment"] = '\n'.join(comments)

        log.info('Submitting data to DB:')
        log.info(params)
        result = query_database('addObservingBlockHistory', params=params)
        log.info(f"Response: {result}")

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('OBid', type=str,
                            help='The unique identifier for the OB to retrieve.')
        parser.add_argument('observer', type=str,
                            help='The observer submitting the comment.')
        parser.add_argument('comment', type=str,
                            help='The comment.')
        return super().add_cmdline_args(parser)
