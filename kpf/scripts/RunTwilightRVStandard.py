import os
import time
from pathlib import Path
import yaml
import subprocess
import traceback
import re

from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy import units as u
from astropy.time import Time

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (set_script_keywords, clear_script_keywords,
                         add_script_log, check_script_running, check_scriptstop)
from kpf.scripts.StartOfNight import StartOfNight
from kpf.scripts.ConfigureForAcquisition import ConfigureForAcquisition
from kpf.scripts.WaitForConfigureAcquisition import WaitForConfigureAcquisition
from kpf.scripts.ConfigureForScience import ConfigureForScience
from kpf.scripts.WaitForConfigureScience import WaitForConfigureScience
from kpf.scripts.ExecuteSci import ExecuteSci
from kpf.scripts.CleanupAfterScience import CleanupAfterScience
from kpf.scripts.EndOfNight import EndOfNight
from kpf.scripts.RunCalOB import RunCalOB
from kpf.utils.SendEmail import SendEmail
from kpf.spectrograph.SetProgram import SetProgram
from kpf.spectrograph.SetObserver import SetObserver


class TwilightTarget():
    '''A class to hold each possible twilight target
    '''
    def __init__(self, targname='', coord=None, priority=1, comment=''):
        self.targname = targname
        self.coord = coord
        self.priority = priority
        self.comment = comment
        self.star_list_line = None

    def alt(self, time=Time.now(), loc=EarthLocation.of_site('keck')):
        altaz = self.coord.transform_to(AltAz(obstime=time,location=loc))
        return altaz.alt.deg * u.deg
        
    def str(self):
        return f"{self.targname}: priority={self.priority}"

    def repr(self):
        return f"{self.targname}: priority={self.priority}"

    @classmethod
    def from_starlist_line(self, line):
        t = TwilightTarget()
        matchline = re.match('([\w\d\s]{16})(.+)\n', line)
        if matchline is None:
            return None
        else:
            t.star_list_line = line.strip('\n')
            t.targname = matchline.group(1).strip()
            targinfo = matchline.group(2)
            comment_i = targinfo.find('#')
            if comment_i > 0:
                components = targinfo[:comment_i].split(' ')
                t.comment = targinfo[comment_i:].strip()
                matchpriority = re.search('priority=([\d\.]+).*', t.comment)
                if matchpriority is not None:
                    t.priority = float(matchpriority.group(1))
                else:
                    t.priority = 1
            else:
                components = targinfo.split(' ')
                t.comment = ''
                t.priority = 1
            remove = -1
            while remove is not None:
                try:
                    remove = components.index('')
                    components.pop(remove)
                except:
                    remove = None
            t.comment += ' '
            t.comment += ':'.join(components[7:])
            t.coord = SkyCoord(':'.join(components[0:3]), ':'.join(components[3:6]), unit=(u.hourangle, u.deg))
            return t


def rank_targets(starlist_file, horizon=30*u.deg):
    log.debug(f"Selecting Twilght Targets from {starlist_file}")
    with open(starlist_file) as f:
        lines = f.readlines()
    all_targets = []
    starlist_dir = Path(starlist_file).parent
    for line in lines:
        targ = TwilightTarget.from_starlist_line(line)
        OB_file = starlist_dir / f"{targ.targname}.yaml"
        if OB_file.exists() is False:
            log.debug(f"  Could not find OB file for {targ.targname}")
        elif targ.alt() > horizon:
            log.debug(f"  {targ.targname} at EL={targ.alt():.1f} is available, priority={targ.priority}")
            all_targets.append(targ)
        else:
            log.debug(f"  {targ.targname} at EL={targ.alt():.1f} is below configured horizon")
    all_targets = sorted(all_targets, key=lambda x: x.priority, reverse=True)
    return all_targets


##-------------------------------------------------------------------------
## RunTwilightRVStandard
##-------------------------------------------------------------------------
class RunTwilightRVStandard(KPFTranslatorFunction):
    '''Executes a twilight observation of one a selected RV standard star. This
    script performs all necessary instrument actions from sart up to shut down.

    Sequence of Actions (and who performs them) once this script is invoked:
    - (Script): run StartOfNight
    - (Script): Start Sci OB + Slew Cal
    - (OA): Slew to target
    - (OA): Perform autofoc
    - (Script): Obtain science data
    - (OA): Release to regular use, OA can park or do other tasks
    - (Script): run EndOfNight
    - (Script): run Calibration
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args, logger, cfg):

        # ---------------------------------
        # Select Target
        # ---------------------------------
        horizon = 30*u.deg
        starlist_file = Path(f'/s/sdata1701/OBs/kpftwilight/starlist.txt')
        all_targets = rank_targets(starlist_file, horizon=horizon)
        if len(all_targets) == 0:
            log.error(f'No targets available above horizon ({horizon:.1f})')
            return

        targname = all_targets[0].targname
        sciOBfile = starlist_file.parent / f'{targname}.yaml'
        with open(sciOBfile, 'r') as f:
            sciOB = yaml.safe_load(f)

        calOBfile = Path('/s/sdata1701/OBs/kpftwilight/twilight_program_cal.yaml')
        if calOBfile.exists() is False:
            log.error(f"Could not load OB file: {calOBfile}")
            return
        with open(calOBfile, 'r') as f:
            calOB = yaml.safe_load(f)

        log_string = f"Selected: {targname} at {all_targets[0].alt():.1f}, "\
                     f"priority={all_targets[0].priority}"
        log.debug(log_string)
        if args.get('test_only', False) is True:
            print(log_string)
            return

        # ---------------------------------
        # Start Of Night
        # ---------------------------------
        msg = ["",
               "-------------------------------------------------------------",
               "Thank you for executing a KPF Twilight Stability Measurement.",
               "If you encounter urgent problems or questions contact one of",
               "the KPF SAs.  Contact info:",
               "    Josh Walawender: 808-990-4294 (cell)",
               "",
               "Please load the starlist at",
               f"{starlist_file}",
               "",
               f"Our target will be:",
               f"  {targname}",
               "",
               "If the instrument has not been in use, you will presumably",
               "need to run the Start Of Night script.  This will open the AO",
               "hatch and configure AO and KPF for observing.  This is not",
               "needed if KPF has been observing immediately prior to this.",
               "Do you wish to run the Start Of Night Script? [Y/n]",
               "-------------------------------------------------------------",
               "",
               ]
        for line in msg:
            print(line)
        user_input = input()
        if user_input.lower() in ['n', 'no', 'cancel']:
            log.warning('User opted to skip Start Of Night script')
        else:
            StartOfNight.execute({})

        SetProgram.execute({'progname': 'K444'})
        SetObserver.execute({'observer': 'OA'})

        # Wrap operations in try/except to ensure we get to end of night
        try:
            log.info(f"Configuring for Acquisition")
            ConfigureForAcquisition.execute(sciOB)

            # ---------------------------------
            # OA Focus
            # ---------------------------------
            msg = ["",
                   "-------------------------------------------------------------",
                   "The instrument is being configured now, please begin slewing",
                   "to the target. Once you are on target:",
                   " - Focus on target using autfoc",
                   " - Then place the target on the KPF PO",
                   "When those steps are done, press Enter to continue.",
                   "-------------------------------------------------------------",
                   "",
                   ]
            for line in msg:
                print(line)
            user_input = input()

            # Open an xshow for exposure status
            cmd = ['xshow', '-s', 'kpfexpose', 'EXPOSE', 'ELAPSED', 'EXPOSURE']
            xshow_proc = subprocess.Popen(cmd,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)

            # ---------------------------------
            # Execute Observation
            # ---------------------------------
            WaitForConfigureAcquisition.execute(sciOB)
            log.info(f"Configuring for Science")
            ConfigureForScience.execute(sciOB)
            WaitForConfigureScience.execute(sciOB)

            # Execute Sequences
            check_script_running()
            set_script_keywords(Path(__file__).name, os.getpid())
            # Execute the Cal Sequence
            observations = sciOB.get('SEQ_Observations', [])
            for observation in observations:
                observation['Template_Name'] = 'kpf_sci'
                observation['Template_Version'] = sciOB['Template_Version']
                observation['Gmag'] = sciOB['Gmag']
                log.debug(f"Automatically setting TimedShutter_CaHK: {sciOB['TriggerCaHK']}")
                observation['TimedShutter_CaHK'] = sciOB['TriggerCaHK']
                observation['TriggerCaHK'] = sciOB['TriggerCaHK']
                observation['TriggerGreen'] = sciOB['TriggerGreen']
                observation['TriggerRed'] = sciOB['TriggerRed']
                observation['TriggerGuide'] = (sciOB.get('GuideMode', 'off') != 'off')
                # Wrap in try/except so that cleanup happens
                try:
                    ExecuteSci.execute(observation)
                except Exception as e:
                    log.error("ExecuteSci failed:")
                    log.error(e)
            clear_script_keywords()
        except Exception as e:
            log.error(f'Encountered exception during operations')
            log.error(e)
            log.error(traceback.format_exc())

        # Cleanup
        CleanupAfterScience.execute(sciOB)

        # Close xshow
        xshow_proc.terminate()

        # ---------------------------------
        # Done with telescope
        # ---------------------------------
        log.debug('Observations complete. Alerting OA.')

        msg = ["",
               "-------------------------------------------------------------",
               "Observation complete. Do you wish to run end of night and",
               "perform a calibration set? Please answer yes if this is a",
               "morning twilight or if some other instrument will be observing.",
               "",
               "Regardless of the choice below, you may perform other tasks as",
               "needed after answering.",
               "",
               "Run End of Night and then start calibrations? [Y/n]",
               "-------------------------------------------------------------",
               "",
               ]
        for line in msg:
            print(line)
        user_input = input()
        if user_input.lower() in ['y', 'yes']:
            EndOfNight.execute({})
            RunCalOB.execute(calOB)

        # Send email
        email = {
                 'To': 'kpf_info@keck.hawaii.edu,ahoward@caltech.edu,sphalverson@gmail.com',
#                  'To': 'jwalawender@keck.hawaii.edu',
                 'Subject': 'KPF Twilight Program Completed',
                 'Message': 'A KPF twilight observation has been completed.'}
        SendEmail.execute(email)
        print()
        print('Script complete.')
        time.sleep(120)


    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('--test', dest="test_only",
                            default=False, action="store_true",
                            help='Only execute the target selection code')
        return super().add_cmdline_args(parser, cfg)
