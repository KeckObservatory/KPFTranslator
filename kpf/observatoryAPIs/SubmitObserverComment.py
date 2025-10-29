import datetime
import json
import requests

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.observatoryAPIs import addObservingBlockHistory, getPI, get_OBs_from_KPFCC_API
from kpf.utils.SendEmail import SendEmail


##-------------------------------------------------------------------------
## SubmitObserverComment
##-------------------------------------------------------------------------
class SubmitObserverComment(KPFFunction):
    '''Adds a comment to the specified OB in the KPF-CC database. Also emails
    the PI of the associated program immediately with the comment.

    Args:
        OBid (str): The unique identifier for the OB to comment on.
        observer (str): The commenter/observer's name
        comment (str): The comment to submit.

    Functions Called:

    - `kpf.observatoryAPIs.GetObservingBlocks`
    - `kpf.utils.SendEmail`
    '''
    @classmethod
    def pre_condition(cls, args):
        OBid = args.get('OBid', None)
        if OBid is None:
            raise FailedPreCondition('OBid must be provided')

    @classmethod
    def perform(cls, args):
        log.info(f"Running {cls.__name__}")
        if args.get('OBid', None) == None:
            log.warning('No OB ID found, unable to submit comment')
            return
        params = {'id': args.get('OBid', ''),
                  'observer': args.get('observer', ''),
                  'comment': args.get('comment', ''),
                  }
        # For testing
#         comments = ['an observer comment', 'another comment', 'this is a lot of comments for a single OB!',
#                     'This is a long soliloquy on the observing conditions during this observation which is here to make sure we do not have overly restrictive string length limits somewhere in the system.',
#                     "For completeness, a check on various inconvienient characters:\nJohn O'Meara, Cecilia Payne-Gaposchkin, are question marks ok? (should I even ask?) [perhaps not] {right?}"]
#         params["comment"] = '\n'.join(comments)
#         log.info('Submitting data to DB:')
#         log.info(params)
#         result = addObservingBlockHistory(params)
#         log.info(f"Response: {result}")

        # Email PI
        log.info(f"Collecting info to email the PI")

        params = {'id': args.get('OBid', '')}
        OBs, failure_messages = get_OBs_from_KPFCC_API(params)
        if len(OBs) > 0:
            semid = OB[0].semid
        else:
            semid = failure_messages[0].split()[1].strip(':').strip('(').strip(')')
        result = getPI(semid)
        if result.get('success', False) == False:
            log.error('Unable to retrieve PIinfo from API')
        else:
            PIinfo = result.get('data', {})
            email = {'To': PIinfo.get('Email'),
                     'From': 'cc@keck.hawaii.edu',
                     'Subject': f'KPF Observer Comment',
                     'Message': args.get('comment', ''),
                     }
        print(email)
#             SendEmail.execute(email)

#         import json
#         import logging
#         from pathlib import Path
#         # Set up temporary file for test emails to sit
#         for handler in log.handlers:
#             if isinstance(handler, logging.handlers.RotatingFileHandler):
#                 kpflog_filehandler = handler
#         utnow = datetime.datetime.utcnow()
#         date = utnow-datetime.timedelta(days=1)
#         date_str = date.strftime('%Y%b%d').lower()
#         date_log_path = Path(kpflog_filehandler.baseFilename).parent / date_str
#         if date_log_path.exists() is False:
#             date_log_path.mkdir(mode=0o777, parents=True)
#             # Try to set permissions on the date directory
#             # necessary because the mode input to mkdir is modified by umask
#             try:
#                 os.chmod(date_log_path, 0o777)
#             except OSError as e:
#                 pass
#         email_buffer_file = date_log_path / 'emails.json'
#         if email_buffer_file.exists():
#             with open(email_buffer_file, 'r') as f:
#                 emails = json.loads(f.read())
#         else:
#             emails = []
#         emails.append(email)
#         print(emails)
#         with open(email_buffer_file, 'w') as f:
#             json.dump(emails, f)


    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('OBid', type=str,
                            help='The unique identifier for the OB.')
        parser.add_argument('observer', type=str,
                            help='The observer submitting the comment.')
        parser.add_argument('comment', type=str,
                            help='The comment.')
        return super().add_cmdline_args(parser)
