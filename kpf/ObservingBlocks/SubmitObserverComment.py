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
from kpf.ObservingBlocks.GetObservingBlocks import query_database, GetObservingBlocks
from kpf.schedule import getPI, getObserverInfo
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
        log.info(f"Collecting info to email the PI")
        if params.get('id') == '':
            log.warning('No OB ID found, not emailing PI')
            return
        OB = GetObservingBlocks.execute({'OBid': args.get('OBid')})[0]
        print(OB.semid)
        PI_ID = getPI(OB.semid)[0]
        print(PI_ID)
        PIinfo = getObserverInfo(PI_ID.get('Principal'))[0]
        print(PIinfo)
        email = {'To': PIinfo.get('Email'),
                 'From': 'kpf_info@keck.hawaii.edu',
                 'Subject': f'Observer Comment on {OB.summary()}',
                 'Message': args.get('comment', ''),
                 }
        print(email)
        import json
        import logging
        from pathlib import Path
        # Set up temporary file for test emails to sit
        for handler in log.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                kpflog_filehandler = handler
        utnow = datetime.datetime.utcnow()
        date = utnow-datetime.timedelta(days=1)
        date_str = date.strftime('%Y%b%d').lower()
        date_log_path = Path(kpflog_filehandler.baseFilename).parent / date_str
        if date_log_path.exists() is False:
            date_log_path.mkdir(mode=0o777, parents=True)
            # Try to set permissions on the date directory
            # necessary because the mode input to mkdir is modified by umask
            try:
                os.chmod(date_log_path, 0o777)
            except OSError as e:
                pass
        email_buffer_file = date_log_path / 'emails.json'
        if email_buffer_file.exists():
            with open(email_buffer_file, 'r') as f:
                emails = json.loads(f.read())
        else:
            emails = []
        emails.append(email)
        print(emails)
        with open(email_buffer_file, 'w') as f:
            json.dump(emails, f)


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
