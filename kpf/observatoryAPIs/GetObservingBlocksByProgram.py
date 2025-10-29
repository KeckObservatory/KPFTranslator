import datetime

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.observatoryAPIs import get_semester_dates, get_OBs_from_KPFCC_API


##-------------------------------------------------------------------------
## GetObservingBlocksByProgram
##-------------------------------------------------------------------------
class GetObservingBlocksByProgram(KPFFunction):
    '''Retrieve all OB associated with the given program ID in the KPF-CC
    database.
    '''
    @classmethod
    def pre_condition(cls, args):
        program = args.get('program', None)
        if program is None:
            raise FailedPreCondition('Program must be provided')

    @classmethod
    def perform(cls, args):
        semester = args.get('semester', None)
        if semester is None:
            now = datetime.datetime.now()
            semester, start, end = get_semester_dates(now)
        program = args.get('program', None)
        if program is None:
            return
        params = {'semid': f"{semester}_{program}"}
        OBs, failure_messages = get_OBs_from_KPFCC_API(params)
        return OBs, failure_messages

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


