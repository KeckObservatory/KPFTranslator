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
from kpf.schedule import getPI, getUserInfo
from kpf.utils.SendEmail import SendEmail


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

        # Email PI
        if params.get('id') == '':
            log.warning('No OB ID found, not emailing PI')
            return
        OB = GetObservingBlocks.execute({'OBid': args.get('OBid')})[0]
        PI_ID = getPI(OB.semid)[0]
        PIinfo = getObserverInfo(PI_ID.get('Principal'))[0]
        email = {'To': PIinfo.get('Email'),
                 'From': 'kpf_info@keck.hawaii.edu',
                 'Subject': f'Observer Comment on {OB.summary()}',
                 'Message': args.get('comment', ''),
                 }
        import json
        import logging
        from pathlib import Path
        # Set up temperary file for test emails to sit
        for handler in log.handlers:
            if isinstance(handler, RotatingFileHandler):
                kpflog_filehandler = handler
        utnow = datetime.utcnow()
        date = utnow-timedelta(days=1)
        date_str = date.strftime('%Y%b%d').lower()
        date_log_path = Path(kpflog_filehandler.baseFilename).parent / date_str
        email_buffer_file = date_log_path / 'emails.json'
        if email_buffer_file.exists():
            with open(email_buffer_file, 'r') as f:
                emails = json.loads(f.read())
        else:
            emails = []
        with open(email_buffer_file, 'w') as f:
            json.dump(emails.append(email), f)


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
