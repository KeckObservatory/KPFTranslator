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
        output_file = Path('/s/sdata1701/KPFTranslator_logs/camera_errors.txt')
        if output_file.exists(): output_file.unlink()
        date = datetime.strptime('2023-06-01', '%Y-%m-%d')
        total_green_errors = 0
        total_green_starts = 0
        total_red_errors = 0
        total_red_starts = 0
        print(f"From {date.strftime('%Y-%m-%d')}")
        with open(output_file, 'w') as f:
            while date < datetime.utcnow() - timedelta(days=1):
                date_str = date.strftime('%Y-%m-%d')
                ng_starts, nr_starts = count_start_state_instances(date=date_str)
                ng_errs, nr_errs = count_start_state_errors(date=date_str)
                total_green_errors += ng_errs
                total_green_starts += ng_starts
                total_red_errors += nr_errs
                total_red_starts += nr_starts
                line = f"{date_str}, {ng_errs}, {ng_starts}, {nr_errs}, {nr_starts}"
#                 print(line)
                f.write(f"{line}\n")
                date += timedelta(days=1)
        print(f"Through {date.strftime('%Y-%m-%d')}")
        green_error_rate = total_green_errors/total_green_starts
        print(f"Green error rate = {green_error_rate:.2%} ({total_green_errors}/{total_green_starts})")
        red_error_rate = total_red_errors/total_red_starts
        print(f"Red error rate = {red_error_rate:.2%} ({total_red_errors}/{total_red_starts})")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
