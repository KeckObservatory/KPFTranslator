import os
import time
from pathlib import Path
import yaml
import subprocess

from astropy.time import Time
from astropy.coordinates import EarthLocation

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
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
        return True

    @classmethod
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args, logger, cfg):

        # ---------------------------------
        # Select Target
        # ---------------------------------
        keck = EarthLocation.of_site('keck')
        now = Time.now()
        now.location = keck
        lst = now.sidereal_time('apparent')
        if lst.value > 14.3 and lst.value < 20.3:
            targname = "HD157347"
        elif lst.value > 3.5 and lst.value < 10.5:
            targname = 'HD55575'
        elif lst.value > 3.5 and lst.value < 10.5:
            targname = "HD52711"
        elif lst.value > 2.0 and lst.value < 9.0:
            targname = "HD37008"

        sciOBfile = Path(f'/s/starlists/000000_kpftwilight/{targname}.yaml')
        if sciOBfile.exists() is False:
            log.error(f"Could not load OB file: {sciOBfile}")
            return
        with open(sciOBfile, 'r') as f:
            sciOB = yaml.safe_load(f)

        calOBfile = Path('/s/starlists/000000_kpftwilight/twilight_program_cal.yaml')
        if calOBfile.exists() is False:
            log.error(f"Could not load OB file: {calOBfile}")
            return
        with open(calOBfile, 'r') as f:
            calOB = yaml.safe_load(f)

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
               "/s/starlists/000000_kpftwilight/starlist.txt",
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

        SetProgram.execute({'progname': 'E310'})
        SetObserver.execute({'observer': 'OA'})

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
        return True
