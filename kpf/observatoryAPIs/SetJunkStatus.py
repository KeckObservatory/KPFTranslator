from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.observatoryAPIs import setKPFJunkValue


##-------------------------------------------------------------------------
## SetJunkStatus
##-------------------------------------------------------------------------
class SetJunkStatus(KPFFunction):
    '''Set the junk status of the specified exposure for the specified OB in
    the KPF-CC database.

    Args:
        id (str): The unique identifier for the OB.
        start_time (str): The start time of the exposure (in 
                          YYYY-mm-ddTHH:MM:SS.ss format) to mark.
        junk (bool): Mark exposure as junk (True) or not junk (False).
    '''
    @classmethod
    def pre_condition(cls, args):
        if args.get('id', None) is None:
            raise FailedPreCondition('id must be provided')
        if args.get('start_time', None) is None:
            raise FailedPreCondition('start_time must be provided')

    @classmethod
    def perform(cls, args):
        log.info(f"Running {cls.__name__}")
        log.debug(args)
        result = setKPFJunkValue(args.get('id'),
                                 args.get('start_time'),
                                 junk=args.get('junk', False))
        log.info(f"Response: {result}")

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('id', type=str,
                            help='The unique identifier for the OB.')
        parser.add_argument('start_time', type=str,
                            help='The start_time of the exposure.')
        parser.add_argument('--junk', dest="junk",
            default=False, action="store_true",
            help='Is this exposure junk?')

        return super().add_cmdline_args(parser)
