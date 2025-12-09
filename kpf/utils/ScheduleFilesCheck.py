from pathlib import Path
import datetime

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.observatoryAPIs import get_semester_dates
from kpf.observatoryAPIs.GetScheduledPrograms import GetScheduledPrograms
from kpf.utils.SendEmail import SendEmail


##-----------------------------------------------------------------------------
## ScheduleFilesCheck
##-----------------------------------------------------------------------------
class ScheduleFilesCheck(KPFFunction):
    '''

    Args:
        progname (str): The program name to set if a choice is needed.

    Functions Called:

    - `kpf.observatoryAPIs.GetScheduledPrograms`
    - `kpf.utils.SendEmail`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        errors = []
        utnow = datetime.datetime.utcnow()
        semester, s_start, s_end = get_semester_dates(utnow)

        band_names = ['full-band1', 'full-band2', 'full-band3']
        classical, cadence = GetScheduledPrograms.execute({'semester': 'tonight'})
        if len(cadence) > 0:
            band_names.extend(['band1', 'band2', 'band3'])

        base_path = Path('/s/sdata1701/Schedules')
        semester_path = base_path / semester
        date_string = (utnow - datetime.timedelta(hours=24)).strftime('%Y-%m-%d')
        date_path = semester_path / date_string
        if date_path.exists() is False:
            err = f"{str(date_path)} does not exist"
            errors.append(err)
            log.error(err)

        band_paths = [date_path / band for band in band_names]
        line_counts = {}
        for band_path in band_paths:
            if band_path.exists() is False:
                err = f"{str(band_path)} does not exist"
                errors.append(err)
                log.error(err)
            output_path = band_path / 'output'
            if output_path.exists() is False:
                err = f"{str(output_path)} does not exist"
                errors.append(err)
                log.error(err)
            output_file = output_path / 'night_plan.csv'
            if output_file.exists() is False:
                err = f"{str(output_file)} does not exist"
                errors.append(err)
                log.error(err)
            try:
                with open(output_file, 'r') as f:
                    lines = f.readlines()
                nlines = len(lines)
                line_counts[band_path.name] = nlines
                if nlines <= 1:
                    err = f"{str(output_file)} has only {nlines} lines"
                    errors.append(err)
                    log.error(err)
            except:
                err = f'Failed to read {str(output_file)}'
                errors.append(err)
                log.error(err)

        # Results
        result_str = 'Band        Line Count\n'
        for band in sorted(line_counts.keys()):
            if line_counts[band] <= 1:
                result_str += f'{band:11s} {line_counts[band]:d} <-- Low target count!\n'
            else:
                result_str += f'{band:11s} {line_counts[band]:d}\n'
        print(result_str)

        # Send Email
        if len(errors) > 0:
            msg = 'KPF-CC Schedule May Be Bad\n\n'
            if args.get('email', False) == True:
                try:
                    SendEmail.execute({'Subject': f'KPF-CC Schedule May Be Bad',
                                       'Message': msg+result_str,
                                       'To': 'jwalawender@keck.hawaii.edu'})
                except Exception as email_err:
                    log.error(f'Sending email failed')
                    log.error(email_err)


    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('--email', dest="email",
                            default=False, action="store_true",
                            help='Send email if SoCal is not shut down?')
        return super().add_cmdline_args(parser)
