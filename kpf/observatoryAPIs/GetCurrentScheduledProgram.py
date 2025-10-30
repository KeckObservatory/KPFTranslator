import datetime

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.observatoryAPIs import get_semester_dates, query_observatoryAPI


def string_time_to_decimal(time_str):
    h = int(time_str.split(':')[0])
    m = int(time_str.split(':')[1])
    return h + m/60


class GetCurrentScheduledProgram(KPFFunction):
    '''Return the program ID (e.g. E123) of the program that is currently
    scheduled. Note that this will only return a program if we are between the
    start and end times on the schedule (the night starts and ends at 12 degree
    twilight), so it is possible for observing to be happening before there is
    an officially scheduled program.
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        '''Returns the currently scheduled program ID.
        '''
        if args.get('datetime', 'now') == 'now':
            inputdateUT = datetime.datetime.utcnow()
        else:
            inputdateHST = datetime.datetime.strptime(args.get('datetime'), '%Y-%m-%dT%H:%M:%S')
            inputdateUT = inputdateHST + datetime.timedelta(hours=10)
        startdate = inputdateUT - datetime.timedelta(days=1)
        UTdecimal_hour = inputdateUT.hour + inputdateUT.minute/60

        params = {'date': startdate.strftime('%Y-%m-%d'),
                  'numdays': 1,
                  'telnr': args.get('telnr', 1),
                  'instrument': 'KPF'}
        all_programs = query_observatoryAPI('schedule', 'getSchedule', params)

        progname = None
        for program in all_programs:
            prog_start = string_time_to_decimal(program.get('StartTime'))
            prog_end = string_time_to_decimal(program.get('EndTime'))
            if UTdecimal_hour >= prog_start and UTdecimal_hour <= prog_end:
                progname = program.get('ProjCode')
        return progname

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('datetime', type=str, default='now',
            help='The HST date and time to retrieve (%Y-%m-%dT%H:%M:%S).')
        return super().add_cmdline_args(parser)
