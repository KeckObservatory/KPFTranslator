import datetime

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.observatoryAPIs.schedule import get_semester_dates, query_schedule_API


class GetScheduledPrograms(KPFFunction):
    '''

    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        '''Returns list of dicts with the classical and cadence program info.
        
        If no args, returns everything remaining on this semester's schedule.
        If args contains a value for "semester" then that is either interpreted
        as the semester string (e.g. "2025A") or it can be "current" which
        instructs the code to use the current semester.
        '''
        utnow = datetime.datetime.utcnow()
        semester, semester_start, semester_end = get_semester_dates(utnow)
        if args.get('semester', None) == 'current':
            start = semester_start
            numdays = (semester_end-start).days + 2
        elif str(args.get('semester', None)) == 'today':
            start = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            numdays = 1
        elif str(args.get('semester', None))[0] == '2':
            semester, semester_start, semester_end = get_semester_dates(args.get('semester'))
            start = semester_start
            numdays = (semester_end-start).days + 2
        else:
            # Pull programs from the rest of the semester
            start = utnow
        date_str = (start-datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        query = 'getSchedule'
        params = {'date': date_str,
                  'numdays': numdays,
                  'telnr': args.get('telnr', 1),
                  'instrument': 'KPF'}
        all_programs = query_schedule_API(query, params)
        classical_programs = [p for p in all_programs if p['Instrument'] == 'KPF' and p['Semester'] == semester]
        cadence_programs = [p for p in all_programs if p['Instrument'] == 'KPF-CC' and p['Semester'] == semester]
        return classical_programs, cadence_programs

    @classmethod
    def post_condition(cls, args):
        pass
