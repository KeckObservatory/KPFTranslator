from pathlib import Path
import time
from datetime import datetime, timedelta

import ktl
import keygrabber

from kpf.KPFTranslatorFunction import KPFTranslatorFunction


def count_start_state_instances(date='2023-07-20'):
    begin = datetime.strptime(date, '%Y-%m-%d')
    end = begin + timedelta(days=1)
    history = keygrabber.retrieve({'kpfgreen': ['EXPSTATE']},
                                  begin=time.mktime(begin.timetuple()),
                                  end=time.mktime(end.timetuple()) )
    g_starts = [h for h in history if h['ascvalue'] == 'Start']
    history = keygrabber.retrieve({'kpfred': ['EXPSTATE']},
                                  begin=time.mktime(begin.timetuple()),
                                  end=time.mktime(end.timetuple()) )
    r_starts = [h for h in history if h['ascvalue'] == 'Start']
    return len(g_starts), len(r_starts)


def count_start_state_errors(date='2023-07-20'):
    begin = datetime.strptime(date, '%Y-%m-%d')
    end = begin + timedelta(days=1)
    history = keygrabber.retrieve({'kpfmon': ['G_STARTSTA', 'R_STARTSTA']},
                                  begin=time.mktime(begin.timetuple()),
                                  end=time.mktime(end.timetuple()) )
    r_errs = [h for h in history if h['ascvalue'] == 'ERROR' and h['keyword'] == 'R_STARTSTA']
    g_errs = [h for h in history if h['ascvalue'] == 'ERROR' and h['keyword'] == 'G_STARTSTA']
    ng_errs = len(g_errs)
    nr_errs = len(r_errs)
    return ng_errs, nr_errs




##-------------------------------------------------------------------------
## CountCameraErrors
##-------------------------------------------------------------------------
class CountCameraErrors(KPFTranslatorFunction):
    '''

    ARGS:
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        
        start = datetime.strptime('2023-05-01', '%Y-%m-%d')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('fgs_cube_fileX', type=str,
            help="The FGS FITS cube for the X pixel scan")
        parser.add_argument('fgs_cube_fileY', type=str,
            help="The FGS FITS cube for the Y pixel scan")
        parser.add_argument('targname', type=str,
            help="The target name")
        parser.add_argument("--xfit", dest="xfit", type=float,
            default=335.5,
            help="The X pixel position to use as the center when overlaying the model.")
        parser.add_argument("--yfit", dest="yfit", type=float,
            default=258,
            help="The X pixel position to use as the center when overlaying the model.")
        return super().add_cmdline_args(parser, cfg)
