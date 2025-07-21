#!/kroot/rel/default/bin/kpython3
import sys
import os
import traceback
import time
import copy
from pathlib import Path
import argparse
import logging
from logging.handlers import RotatingFileHandler
# import json
import re
import yaml
import datetime
import subprocess
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, Angle
from astropy.time import Time
from astropy.table import Table

import ktl                      # provided by kroot/ktl/keyword/python
import kPyQt                    # provided by kroot/kui/kPyQt
from PyQt5 import uic, QtWidgets, QtCore, QtGui

from kpf import cfg
from kpf.OB_GUI.OBListModel import OBListModel
from kpf.OB_GUI.HistoryListModel import HistoryListModel
from kpf.OB_GUI.Popups import (ConfirmationPopup, InputPopup,
                               OBContentsDisplay, EditableMessageBox,
                               ObserverCommentBox, SelectProgramPopup)
from kpf.telescope import above_horizon, near_horizon
from kpf.ObservingBlocks.Target import Target
from kpf.ObservingBlocks.Calibration import Calibration
from kpf.ObservingBlocks.Observation import Observation
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.observatoryAPIs.SubmitObserverComment import SubmitObserverComment
from kpf.observatoryAPIs.GetObservingBlocks import GetObservingBlocks
from kpf.observatoryAPIs.GetObservingBlocksByProgram import GetObservingBlocksByProgram
from kpf.observatoryAPIs.GetExecutionHistory import GetExecutionHistory
from kpf.observatoryAPIs.SetJunkStatus import SetJunkStatus
from kpf.scripts.EstimateOBDuration import EstimateOBDuration
from kpf.spectrograph.QueryFastReadMode import QueryFastReadMode
from kpf.spectrograph.SetObserver import SetObserver
from kpf.spectrograph.SetProgram import SetProgram
from kpf.utils.StartOfNight import StartOfNight
from kpf.utils.EndOfNight import EndOfNight
from kpf.observatoryAPIs import get_semester_dates
from kpf.observatoryAPIs.GetScheduledPrograms import GetScheduledPrograms
from kpf.observatoryAPIs.GetTelescopeRelease import GetTelescopeRelease
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.magiq.SelectTarget import SelectTarget


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
logging.addLevelName(25, 'SCHEDULE')

def schedule(self, message, *args, **kwargs):
    if self.isEnabledFor(25):
        self._log(25, message, args, **kwargs)

logging.Logger.schedule = schedule


def create_GUI_log(verbose=False):
    guilog = logging.getLogger('KPF_OB_GUI')
    guilog.setLevel(logging.DEBUG)
    ## Set up console output
    LogConsoleHandler = logging.StreamHandler()
    if verbose:
        LogConsoleHandler.setLevel(logging.DEBUG)
    else:
        LogConsoleHandler.setLevel(logging.INFO)
    LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s')
    LogConsoleHandler.setFormatter(LogFormat)
    guilog.addHandler(LogConsoleHandler)
    ## Set up file output
    logdir = Path(f'/s/sdata1701/KPFTranslator_logs/')
    if logdir.exists() is False:
        logdir.mkdir(mode=0o777, parents=True)
    LogFileName = logdir / 'OB_GUI_v2.log'
    LogFileHandler = RotatingFileHandler(LogFileName,
                                         maxBytes=100*1024*1024, # 100 MB
                                         backupCount=1000) # Keep old files
    LogFileHandler.setLevel(logging.DEBUG)
    LogFileHandler.setFormatter(LogFormat)
    guilog.addHandler(LogFileHandler)
    return guilog


##-------------------------------------------------------------------------
## Wrapper to launch script in xterm
##-------------------------------------------------------------------------
def launch_command_in_xterm(script_name, capture_stdout=False, window_title=None):
    '''Pop up an xterm with the script running.
    '''
    kpfdo = Path(__file__).parent.parent / 'kpfdo'
    if window_title is None:
        window_title = script_name
    if capture_stdout:
        ## Set up script stdout file
        log = logging.getLogger('KPFTranslator')
        for handler in log.handlers:
            if isinstance(handler, RotatingFileHandler):
                kpflog_filehandler = handler
        utnow = datetime.datetime.utcnow()
        now_str = utnow.strftime('%Y%m%dat%H%M%S')
        date = utnow-datetime.timedelta(days=1)
        date_str = date.strftime('%Y%b%d').lower()
        script_log_path = Path(kpflog_filehandler.baseFilename).parent / date_str
        if script_log_path.exists() is False:
            script_log_path.mkdir(mode=0o777, parents=True)
            # Try to set permissions on the date directory
            # necessary because the mode input to mkdir is modified by umask
            try:
                os.chmod(script_log_path, 0o777)
            except OSError as e:
                pass
        script_name_for_log = script_name.split()[0]
        stdout_file = script_log_path / f"kpfdo_{script_name_for_log}_{now_str}.log"
        script_cmd = f'{kpfdo} {script_name} > {stdout_file} ; echo "Done!" ; sleep 30'
    else:
        script_cmd = f'{kpfdo} {script_name} ; echo "Done!" ; sleep 30'
    cmd = ['xterm', '-title', f'{window_title}', '-name', f'{window_title}',
           '-fn', '10x20', '-bg', 'black', '-fg', 'white',
           '-e', f'{script_cmd}']
    proc = subprocess.Popen(cmd)#, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     stdout_output, stderr_output = proc.communicate(timeout=)
#     return stdout_output, stderr_output


##-------------------------------------------------------------------------
## Define Application MainWindow
##-------------------------------------------------------------------------
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, clargs, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
        ui_file = Path(__file__).parent / 'KPF_OB_GUI.ui'
        uic.loadUi(f"{ui_file}", self)
        self.log = guilog
        self.clargs = clargs
        self.pid = os.getpid()
        self.log.info(f'Initializing OB GUI. PID={self.pid}')
        self.file_path = Path('/s/sdata1701/OBs')
        self.log.debug('Initializing MainWindow')
        self.KPFCC = False
        # Keywords
        # DCS
        dcsint = cfg.getint('telescope', 'telnr', fallback=1)
        self.dcs = f'dcs{dcsint}'
        self.log.debug('Cacheing keyword services')
        self.DCS_AZ = ktl.cache(self.dcs, 'AZ')
        self.DCS_AZ.monitor()
        self.DCS_EL = ktl.cache(self.dcs, 'EL')
        self.DCS_EL.monitor()
        self.INSTRUME = kPyQt.kFactory(ktl.cache(self.dcs, 'INSTRUME'))
        self.DCS_UT = kPyQt.kFactory(ktl.cache(self.dcs, 'UT'))
        self.DCS_LST = kPyQt.kFactory(ktl.cache(self.dcs, 'LST'))
        # kpfconfig
        self.kpfconfig = ktl.cache('kpfconfig')
        self.SCRIPTNAME = kPyQt.kFactory(ktl.cache('kpfconfig', 'SCRIPTNAME'))
        self.SCRIPTMSG = kPyQt.kFactory(ktl.cache('kpfconfig', 'SCRIPTMSG'))
        self.SCRIPTSTOP = kPyQt.kFactory(ktl.cache('kpfconfig', 'SCRIPTSTOP'))
        self.SLEWCALREQ = self.kpfconfig['SLEWCALREQ']
        self.SLEWCALTIME = kPyQt.kFactory(self.kpfconfig['SLEWCALTIME'])
        self.SLEWCALFILE = self.kpfconfig['SLEWCALFILE']
        self.SLEWCALFILE.monitor()
        self.CA_HK_ENABLED = kPyQt.kFactory(self.kpfconfig['CA_HK_ENABLED'])
        self.GREEN_ENABLED = kPyQt.kFactory(self.kpfconfig['GREEN_ENABLED'])
        self.RED_ENABLED = kPyQt.kFactory(self.kpfconfig['RED_ENABLED'])
        self.EXPMETER_ENABLED = kPyQt.kFactory(self.kpfconfig['EXPMETER_ENABLED'])
        # kpfexpose
        self.OBJECT = kPyQt.kFactory(ktl.cache('kpfexpose', 'OBJECT'))
        self.EXPOSE = kPyQt.kFactory(ktl.cache('kpfexpose', 'EXPOSE'))
        self.ELAPSED = kPyQt.kFactory(ktl.cache('kpfexpose', 'ELAPSED'))
        self.EXPOSURE = kPyQt.kFactory(ktl.cache('kpfexpose', 'EXPOSURE'))
        self.PROGNAME = kPyQt.kFactory(ktl.cache('kpfexpose', 'PROGNAME'))
        # kpfgreen and kpfred
        self.READOUTPCT_G = kPyQt.kFactory(ktl.cache('kpfgreen', 'READOUTPCT'))
        self.READOUTPCT_R = kPyQt.kFactory(ktl.cache('kpfred', 'READOUTPCT'))
        self.red_acf_file_kw = kPyQt.kFactory(ktl.cache('kpfred', 'ACFFILE'))
        self.green_acf_file_kw = kPyQt.kFactory(ktl.cache('kpfgreen', 'ACFFILE'))
        # kpflamps
        self.LAMPS = kPyQt.kFactory(ktl.cache('kpflamps', 'LAMPS'))
        # Selected OB
        self.SOBindex = -1
        self.exp_index = -1
        self.SOBobservable = False
        self.update_counter = 0
        # Coordinate Systems
        self.keck = EarthLocation.of_site('Keck Observatory')
        # Settings
        self.good_slew_cal_time = 1.0 # hours
        self.bad_slew_cal_time = 2.0 # hours
        self.ADC_horizon = 30
        self.fast = False
        # Tracked values
        self.disabled_detectors = []
        self.telescope_released = GetTelescopeRelease.execute({})
        # Get KPF Programs on schedule
        classical, cadence = GetScheduledPrograms.execute({'semester': 'current'})
        program_IDs = list(set([f"{p['ProjCode']}" for p in classical]))
        self.program_strings = []
        for progID in sorted(program_IDs):
            dates = [e['Date'] for e in classical if e['ProjCode'] == progID]
            self.program_strings.append(f"{progID} on {', '.join(dates)}")
        # KPF-CC Settings and Values
        self.schedule_path = Path(f'/s/sdata1701/Schedules/')
        self.KPFCC_weather_bands = ['1', '2', '3']#, 'backups']
        self.KPFCC_weather_band = '1'
        self.KPFCC_OBs = {}
        self.KPFCC_start_times = {}
        for WB in self.KPFCC_weather_bands:
            self.KPFCC_OBs[WB] = []
            self.KPFCC_start_times[WB] = None
        self.prepare_execution_history_file()
        # Add OB List Model Component
        self.OBListModel = OBListModel(log=self.log)
        self.HistoryListModel = HistoryListModel(log=self.log)
        # Add OB Builder Component
        self.SciObservingBlock = None
        self.CalObservingBlock = None
        self.BuildTarget = Target({})
        self.BuildObservation = [Observation({})]
        self.BuildCalibration = [Calibration({})]
        # Example Calibrations
        try:
            self.slewcalOB = ObservingBlock(self.SLEWCALFILE.ascii)
        except Exception as e:
            self.log.warning(f'Faied to load slewcal file: {self.SLEWCALFILE.ascii}')
            self.log.debug(e)
            try:
                self.log.debug('Loading temporary slewcal OB')
                self.slewcalOB = ObservingBlock('/s/sdata1701/OBs/jwalawender/Calibrations/SlewCal_EtalonFiber.yaml')
            except:
                self.slewcalOB = None
        if self.slewcalOB is not None:
            comment = ['This is a pure calibration OB, so the FIU will be in ',
                       'calibration or stow mode when this finishes.\n\n',
                       'Run "FIU->Configure FIU for Observing" from the Menu ',
                       'bar to allow target acquisition once this OB has completed.']
            self.slewcalOB.CommentToObserver = ''.join(comment)
            self.example_calOB = copy.deepcopy(self.slewcalOB)
        else:
            self.example_calOB = ObservingBlock({})
        # Load other example Cal OBs
        self.example_cal_file = Path(__file__).parent.parent / 'ObservingBlocks' / 'exampleOBs' / 'Calibrations.yaml'
        if self.example_cal_file.exists():
            example_OB = ObservingBlock(self.example_cal_file)
            self.example_calOB.Calibrations.extend(example_OB.Calibrations)

    def setupUi(self):
        self.log.debug('setupUi')
        self.setWindowTitle("KPF OB GUI")

        #-------------------------------------------------------------------
        # Menu Bar: File
        ActionExit = self.findChild(QtWidgets.QAction, 'actionExit')
        ActionExit.triggered.connect(self.exit)

        #-------------------------------------------------------------------
        # Menu Bar: Observing
        self.RunStartOfNight = self.findChild(QtWidgets.QAction, 'actionRun_Start_of_Night')
        self.RunStartOfNight.triggered.connect(self.run_start_of_night)
        self.SetObserverNames = self.findChild(QtWidgets.QAction, 'actionSet_Observer_Names')
        self.SetObserverNames.triggered.connect(self.set_observer)
        self.SetProgramID = self.findChild(QtWidgets.QAction, 'actionSet_Program_ID')
        self.SetProgramID.triggered.connect(self.set_programID)
        self.RunEndOfNight = self.findChild(QtWidgets.QAction, 'actionRun_End_of_Night')
        self.RunEndOfNight.triggered.connect(self.run_end_of_night)

        #-------------------------------------------------------------------
        # Menu Bar: OB List
        ActionClearOBList = self.findChild(QtWidgets.QAction, 'action_ClearOBList')
        ActionClearOBList.triggered.connect(self.clear_OB_list)
        ActionLoadOBsFromFiles = self.findChild(QtWidgets.QAction, 'action_LoadOBsFromFiles')
        ActionLoadOBsFromFiles.triggered.connect(self.load_OBs_from_files)
        LoadKPFCCSchedule = self.findChild(QtWidgets.QAction, 'actionLoad_KPF_CC_Schedule')
        LoadKPFCCSchedule.triggered.connect(self.load_OBs_from_schedule)
        LoadOBsFromProgram = self.findChild(QtWidgets.QAction, 'action_LoadOBsFromProgram')
        LoadOBsFromProgram.triggered.connect(self.load_OBs_from_program)
        LoadOBsFromKPFCC = self.findChild(QtWidgets.QAction, 'actionLoad_KPF_CC_OBs')
        LoadOBsFromKPFCC.triggered.connect(self.load_OBs_from_KPFCC)

        #-------------------------------------------------------------------
        # Menu Bar: FIU
        self.ConfigureFIU_Observing = self.findChild(QtWidgets.QAction, 'actionConfigure_FIU_for_Observing')
        self.ConfigureFIU_Observing.triggered.connect(self.configure_FIU_observing)
        self.ConfigureFIU_Calibrations = self.findChild(QtWidgets.QAction, 'actionConfigure_FIU_for_Calibrations')
        self.ConfigureFIU_Calibrations.triggered.connect(self.configure_FIU_calibrations)
        self.ConfigureFIU_Stow = self.findChild(QtWidgets.QAction, 'actionConfigure_FIU_to_Stow_Position')
        self.ConfigureFIU_Stow.triggered.connect(self.configure_FIU_stow)

        #-------------------------------------------------------------------
        # Menu Bar: Magiq 
        self.SendOBListToMagiq = self.findChild(QtWidgets.QAction, 'actionSend_Current_OBs_as_Star_List')
        self.SendOBListToMagiq.triggered.connect(self.OBListModel.update_star_list)
        self.SendOBListToMagiq.setEnabled(False)

        #-------------------------------------------------------------------
        # Main Window

        # Program ID
        self.ProgID = self.findChild(QtWidgets.QLabel, 'ProgID')
        self.PROGNAME.stringCallback.connect(self.ProgID.setText)

        # Observer
        self.Observer = self.findChild(QtWidgets.QLabel, 'Observer')
        observer_kw = kPyQt.kFactory(ktl.cache('kpfexpose', 'OBSERVER'))
        observer_kw.stringCallback.connect(self.Observer.setText)

        # Selected Instrument
        self.SelectedInstrument = self.findChild(QtWidgets.QLabel, 'SelectedInstrument')
        self.INSTRUME.stringCallback.connect(self.update_selected_instrument)
        self.INSTRUME.primeCallback()

        # Progress Bar and Task Description
        self.GUITaskLabel = self.findChild(QtWidgets.QLabel, 'GUITaskLabel')
        self.ProgressBar = self.findChild(QtWidgets.QProgressBar, 'progressBar')
        self.ProgressBar.setValue(0)
        self.ProgressBar.setVisible(False)

        # script name
        self.scriptname_value = self.findChild(QtWidgets.QLabel, 'scriptname_value')
        self.SCRIPTNAME.stringCallback.connect(self.update_scriptname_value)
        self.SCRIPTNAME.primeCallback()

        # script message
        self.ScriptMessageValue = self.findChild(QtWidgets.QLabel, 'ScriptMessageValue')
        self.SCRIPTMSG.stringCallback.connect(self.ScriptMessageValue.setText)
        self.SCRIPTMSG.primeCallback()

        # script stop
        self.scriptstop_value = self.findChild(QtWidgets.QLabel, 'scriptstop_value')
        self.SCRIPTSTOP.stringCallback.connect(self.update_scriptstop_value)
        self.scriptstop_btn = self.findChild(QtWidgets.QPushButton, 'scriptstop_btn')
        self.scriptstop_btn.clicked.connect(self.set_scriptstop)

        # full stop
        self.fullstop_btn = self.findChild(QtWidgets.QPushButton, 'fullstop_btn')
        self.fullstop_btn.clicked.connect(self.do_fullstop)

        # expose status
        self.expose_status_value = self.findChild(QtWidgets.QLabel, 'expose_status_value')
        self.EXPOSE.stringCallback.connect(self.update_expose_status_value)
        self.EXPOSE.primeCallback()
        self.ELAPSED.stringCallback.connect(self.update_expose_status_value)
        self.ELAPSED.primeCallback()
        self.READOUTPCT_G.stringCallback.connect(self.update_expose_status_value)
        self.READOUTPCT_G.primeCallback()
        self.READOUTPCT_R.stringCallback.connect(self.update_expose_status_value)
        self.READOUTPCT_R.primeCallback()

        # object
        self.ObjectValue = self.findChild(QtWidgets.QLabel, 'ObjectValue')
        self.OBJECT.stringCallback.connect(self.ObjectValue.setText)
        self.OBJECT.primeCallback()

        # time since last cal
        self.slewcaltime_value = self.findChild(QtWidgets.QLabel, 'slewcaltime_value')
        self.SLEWCALTIME.stringCallback.connect(self.update_slewcaltime_value)

        # readout mode
        self.read_mode = self.findChild(QtWidgets.QLabel, 'readout_mode_value')
        self.red_acf_file_kw.stringCallback.connect(self.update_acffile)
        self.green_acf_file_kw.stringCallback.connect(self.update_acffile)

        # disabled detectors
        self.disabled_detectors_value = self.findChild(QtWidgets.QLabel, 'disabled_detectors_value')
        self.disabled_detectors_value.setText('')
        self.CA_HK_ENABLED.stringCallback.connect(self.update_ca_hk_enabled)
        self.GREEN_ENABLED.stringCallback.connect(self.update_green_enabled)
        self.RED_ENABLED.stringCallback.connect(self.update_red_enabled)
        self.EXPMETER_ENABLED.stringCallback.connect(self.update_expmeter_enabled)

        # Universal Time
        self.UTValue = self.findChild(QtWidgets.QLabel, 'UTValue')
        self.DCS_UT.stringCallback.connect(self.update_UT)

        # Sidereal Time
        self.SiderealTimeValue = self.findChild(QtWidgets.QLabel, 'SiderealTimeValue')
        self.DCS_LST.stringCallback.connect(self.update_LST)

        #-------------------------------------------------------------------
        # Tab: Observing Blocks

        # Sorting or Weather Band Selector
        self.SortOrWeatherLabel = self.findChild(QtWidgets.QLabel, 'SortOrWeatherLabel')
        self.SortOrWeather = self.findChild(QtWidgets.QComboBox, 'SortOrWeather')
        self.SortOrWeatherLabel.setEnabled(False)
        self.SortOrWeather.setEnabled(False)

        # List of Observing Blocks
        self.OBListHeader = self.findChild(QtWidgets.QLabel, 'OBListHeader')
        self.hdr = 'TargetName       RA          Dec      Gmag Jmag Observations'
        self.OBListHeader.setText(self.hdr)
        self.OBListView = self.findChild(QtWidgets.QListView, 'ListOfOBs')
        self.OBListView.setModel(self.OBListModel)
        self.OBListView.selectionModel().selectionChanged.connect(self.select_OB)

        # Selected Observing Block Details
        self.SOB_TargetName = self.findChild(QtWidgets.QLabel, 'SOB_TargetName')
        self.SOB_GaiaID = self.findChild(QtWidgets.QLabel, 'SOB_GaiaID')
        self.SOB_TargetRA = self.findChild(QtWidgets.QLabel, 'SOB_TargetRA')
        self.SOB_TargetRALabel = self.findChild(QtWidgets.QLabel, 'TargetRALabel')
        self.SOB_TargetDec = self.findChild(QtWidgets.QLabel, 'SOB_TargetDec')
        self.SOB_TargetDecLabel = self.findChild(QtWidgets.QLabel, 'TargetDecLabel')
        self.SOB_Mags = self.findChild(QtWidgets.QLabel, 'SOB_Mags')
        self.SOB_Observation1 = self.findChild(QtWidgets.QLabel, 'SOB_Observation1')
        self.SOB_Observation2 = self.findChild(QtWidgets.QLabel, 'SOB_Observation2')
        self.SOB_Observation3 = self.findChild(QtWidgets.QLabel, 'SOB_Observation3')

        # Calculated Values
        self.SOB_ExecutionTime = self.findChild(QtWidgets.QLabel, 'SOB_ExecutionTime')
        self.SOB_AltAz = self.findChild(QtWidgets.QLabel, 'SOB_AltAz')
        self.SOB_AzSlew = self.findChild(QtWidgets.QLabel, 'SOB_AzSlew')
        self.SOB_ELSlew = self.findChild(QtWidgets.QLabel, 'SOB_ELSlew')

        # SOB Execution
        self.SOB_NotesForObserver = self.findChild(QtWidgets.QLabel, 'CommentToObserver')
        self.SOB_ShowButton = self.findChild(QtWidgets.QPushButton, 'SOB_ShowButton')
        self.SOB_ShowButton.clicked.connect(self.show_SOB)
        self.SOB_AddComment = self.findChild(QtWidgets.QPushButton, 'SOB_AddComment')
        self.SOB_AddComment.clicked.connect(self.add_comment)
        self.SOB_ExecuteButton = self.findChild(QtWidgets.QPushButton, 'SOB_ExecuteButton')
        self.SOB_ExecuteButton.clicked.connect(self.execute_SOB)
        self.SOB_ExecuteSlewCalButton = self.findChild(QtWidgets.QPushButton, 'SOB_ExecuteSlewCalButton')
        self.SOB_ExecuteSlewCalButton.clicked.connect(self.execute_SOB_with_slewcal)
        self.SOB_RemoveFromList = self.findChild(QtWidgets.QPushButton, 'SOB_RemoveFromList')
        self.SOB_RemoveFromList.clicked.connect(self.remove_SOB)
        self.update_SOB_display()


        #-------------------------------------------------------------------
        # Tab: Execution History
        self.HistoryListHeader = self.findChild(QtWidgets.QLabel, 'HistoryListHeader')
        self.HistoryListView = self.findChild(QtWidgets.QListView, 'HistoryList')
        self.HistoryListView.setModel(self.HistoryListModel)
        self.HistoryListView.selectionModel().selectionChanged.connect(self.select_exposure)

        self.MarkExposureJunk = self.findChild(QtWidgets.QPushButton, 'MarkExposureJunk')
        self.MarkExposureJunk.clicked.connect(self.mark_exposure_junk)

        #-------------------------------------------------------------------
        # Tab: Build Science OB
        # Observing Block
        self.SciOBString = self.findChild(QtWidgets.QLabel, 'BS_OBString')
        self.SciOBString.setStyleSheet("background:white")
        self.SciOBValid = self.findChild(QtWidgets.QLabel, 'BS_OBValid')
        self.SciOBEstimatedDuration = self.findChild(QtWidgets.QLabel, 'BS_EstimatedDuration')
        self.SendSciOBToList = self.findChild(QtWidgets.QPushButton, 'BS_SendToOBList')
        self.SendSciOBToList.clicked.connect(self.send_SciOB_to_list)
        self.SaveSciOBToFile = self.findChild(QtWidgets.QPushButton, 'BS_SaveToFile')
        self.SaveSciOBToFile.clicked.connect(self.save_SciOB_to_file)
        self.LoadSciOBFromFile = self.findChild(QtWidgets.QPushButton, 'BS_LoadFromFile')
        self.LoadSciOBFromFile.clicked.connect(self.load_SciOB_from_file)
        self.SciOBProgramID = self.findChild(QtWidgets.QLineEdit, 'BS_ProgramID')
        self.SciOBProgramID.textChanged.connect(self.form_SciOB)
        # Target
        self.QuerySimbadLineEdit = self.findChild(QtWidgets.QLineEdit, 'BS_QuerySimbadLineEdit')
        self.QuerySimbadLineEdit.returnPressed.connect(self.query_Simbad)
        self.QuerySimbadButton = self.findChild(QtWidgets.QPushButton, 'BS_QuerySimbadButton')
        self.QuerySimbadButton.clicked.connect(self.query_Simbad)
        self.BuildTargetValid = self.findChild(QtWidgets.QLabel, 'BS_TargetValid')
        self.ClearTargetButton = self.findChild(QtWidgets.QPushButton, 'BS_ClearTargetButton')
        self.ClearTargetButton.clicked.connect(self.clear_Target)
        self.BuildTargetView = self.findChild(QtWidgets.QPlainTextEdit, 'BS_TargetView')
        self.BuildTargetView.setFont(QtGui.QFont('Courier New', 11))
        self.set_Target(Target({}))
        self.BuildTargetView.textChanged.connect(self.edit_Target)
        # Observations
        self.BuildObservationValid = self.findChild(QtWidgets.QLabel, 'BS_ObservationsValid')
        self.ClearObservationsButton = self.findChild(QtWidgets.QPushButton, 'BS_ClearObservationsButton')
        self.ClearObservationsButton.clicked.connect(self.clear_Observations)
        self.BuildObservationView = self.findChild(QtWidgets.QPlainTextEdit, 'BS_ObservationsView')
        self.BuildObservationView.setFont(QtGui.QFont('Courier New', 11))
        self.set_Observations([Observation({})])
        self.BuildObservationView.textChanged.connect(self.edit_Observations)

        #-------------------------------------------------------------------
        # Tab: Build Calibration OB
        # Observing Block
        self.CalOBString = self.findChild(QtWidgets.QLabel, 'BC_OBString')
        self.CalOBString.setStyleSheet("background:white")
        self.CalOBValid = self.findChild(QtWidgets.QLabel, 'BC_OBValid')
        self.CalEstimatedDuration = self.findChild(QtWidgets.QLabel, 'BC_EstimatedDuration')
        self.SendCalOBToList = self.findChild(QtWidgets.QPushButton, 'BC_SendToOBList')
        self.SendCalOBToList.clicked.connect(self.send_CalOB_to_list)
        self.SaveCalOBToFile = self.findChild(QtWidgets.QPushButton, 'BC_SaveToFile')
        self.SaveCalOBToFile.clicked.connect(self.save_CalOB_to_file)
        self.LoadCalOBFromFile = self.findChild(QtWidgets.QPushButton, 'BC_LoadFromFile')
        self.LoadCalOBFromFile.clicked.connect(self.load_CalOB_from_file)
        # Calibrations
        self.BuildCalibrationValid = self.findChild(QtWidgets.QLabel, 'BC_CalibrationsValid')
        self.ClearCalibrationsButton = self.findChild(QtWidgets.QPushButton, 'BC_ClearCalibrationsButton')
        self.ClearCalibrationsButton.clicked.connect(self.clear_Calibrations)
        self.ExampleCalibrations = self.findChild(QtWidgets.QComboBox, 'BC_ExampleCalibrations')
        self.ExampleCalibrations.addItems([''])
        self.ExampleCalibrations.addItems([cal.get('Object') for cal in self.example_calOB.Calibrations])
        self.ExampleCalibrations.currentTextChanged.connect(self.add_example_calibration)
        self.BuildCalibrationView = self.findChild(QtWidgets.QPlainTextEdit, 'BC_CalibrationsView')
        self.BuildCalibrationView.setFont(QtGui.QFont('Courier New', 11))
        self.set_Calibrations(self.BuildCalibration)
        self.BuildCalibrationView.textChanged.connect(self.edit_Calibrations)
        self.clear_Calibrations()

        if clargs.loadschedule == True:
            self.load_OBs_from_schedule()

    ##-------------------------------------------
    ## Methods to display updates from keywords
    ##-------------------------------------------
    # kpfconfig.SCRIPTSTOP
    def update_scriptstop_value(self, value):
        '''Set label text and set color'''
        self.log.debug(f'update_scriptstop_value: {value}')
        self.scriptstop_value.setText(f"{value}")
        if value == 'Yes':
            self.scriptstop_value.setStyleSheet("color:red")
            self.scriptstop_btn.setText('CLEAR STOP')
        elif value == 'No':
            self.scriptstop_value.setStyleSheet("color:green")
            self.scriptstop_btn.setText('Request Script STOP')
        self.set_SOB_enabled()

    def set_scriptstop(self, value):
        self.log.debug(f'button clicked set_scriptstop: {value}')
        current_kw_value = self.scriptstop_value.text()
        if current_kw_value == 'Yes':
            self.kpfconfig['SCRIPTSTOP'].write('No')
            self.scriptstop_btn.setText('CLEAR STOP')
        elif current_kw_value == 'No':
            self.kpfconfig['SCRIPTSTOP'].write('Yes')
            self.scriptstop_btn.setText('Request Script STOP')

    def do_fullstop(self, value):
        self.log.warning(f"button clicked do_fullstop: {value}")
        msg = ["Do you wish to stop the current exposure and script?",
               "",
               "The current exposure will read out then script cleanup will take place."]
        result = ConfirmationPopup('Full Stop Confirmation', msg).exec_()
        if result == QtWidgets.QMessageBox.Yes:
            # Set SCRIPTSTOP
            self.kpfconfig['SCRIPTSTOP'].write('Yes')
            self.log.warning(f"Sent kpfconfig.SCRIPTSTOP=Yes")
            # Stop current exposure
            if self.EXPOSE.ktl_keyword.ascii == 'InProgress':
                self.EXPOSE.ktl_keyword.write('End')
                self.log.warning(f"Sent kpfexpose.EXPOSE=End")
                self.log.debug('Waiting for kpfexpose.EXPOSE to be Readout')
                readout = self.EXPOSE.ktl_keyword.waitFor("=='Readout'", timeout=10)
                self.log.debug(f"Reached readout? {readout}")
        else:
            self.log.debug('Confirmation is no, not stopping script')

    # kpfconfig.SCRIPTNAME
    def update_scriptname_value(self, value):
        '''Set label text and set color'''
        scriptname_string = value.replace('.py', '')
        self.log.debug(f"update_scriptname_value: {scriptname_string}")
        self.scriptname_value.setText(f"{scriptname_string}")
        if value in ['None', '']:
            self.scriptname_value.setStyleSheet("color:green")
            self.RunStartOfNight.setEnabled(self.SelectedInstrument.text() != 'OSIRIS')
            self.RunEndOfNight.setEnabled(True)
            self.ConfigureFIU_Observing.setEnabled(True)
            self.ConfigureFIU_Calibrations.setEnabled(True)
            self.ConfigureFIU_Stow.setEnabled(True)
            self.SetObserverNames.setEnabled(True)
            self.SetProgramID.setEnabled(True)
            self.refresh_history() # Refresh history, it may have updated
        else:
            self.scriptname_value.setStyleSheet("color:orange")
            self.RunStartOfNight.setEnabled(False)
            self.RunEndOfNight.setEnabled(False)
            self.ConfigureFIU_Observing.setEnabled(False)
            self.ConfigureFIU_Calibrations.setEnabled(False)
            self.ConfigureFIU_Stow.setEnabled(False)
            self.SetObserverNames.setEnabled(False)
            self.SetProgramID.setEnabled(False)

    # kpfexpose.EXPOSE
    def update_expose_status_value(self, value):
        status = self.EXPOSE.ktl_keyword.ascii
        exposure_status_string = f"{status}"
        if status == 'InProgress':
            elapsed = self.ELAPSED.ktl_keyword.binary
            exptime = self.EXPOSURE.ktl_keyword.binary
            exposure_status_string += f" ({elapsed:.0f}/{exptime:.0f} s)"
        if status == 'Readout':
            RDPCT_green = self.READOUTPCT_G.ktl_keyword.binary
            RDPCT_red = self.READOUTPCT_R.ktl_keyword.binary
            exposure_status_string += f" ({RDPCT_green:.0f}%,{RDPCT_red:.0f}%)"
        self.expose_status_value.setText(exposure_status_string)
        if status == 'Ready':
            self.expose_status_value.setStyleSheet("color:green")
        elif status in ['Start', 'InProgress', 'Readout']:
            self.expose_status_value.setStyleSheet("color:orange")

    # dcs.INSTRUME
    def update_selected_instrument(self, value):
        self.log.debug('update_selected_instrument')
        self.SelectedInstrument.setText(value)
        release_str = {True: 'Telescope Released.',
                       False: 'Telescope NOT Released.'}[self.telescope_released]
        diabled_msg = 'Telescope moves and Magiq integration disabled'
        if value in ['KPF', 'KPF-CC']:
            if self.telescope_released:
                self.SelectedInstrument.setStyleSheet("color:green")
                self.SelectedInstrument.setToolTip(f'{release_str}')
                self.SendOBListToMagiq.setEnabled(True)
            else:
                self.SelectedInstrument.setStyleSheet("color:orange")
                self.SelectedInstrument.setToolTip(f'{release_str}. {diabled_msg}')
                self.SendOBListToMagiq.setEnabled(False)
        else:
            self.SelectedInstrument.setStyleSheet("color:red")
            self.SelectedInstrument.setToolTip(f'Instrument is not KPF. {diabled_msg}')
            self.SendOBListToMagiq.setEnabled(False)

    # kpfconfig.SLEWCALTIME
    def update_slewcaltime_value(self, value):
        '''Updates value in QLabel and sets color'''
        value = float(value)
        self.slewcaltime_value.setText(f"{value:.1f} hrs")
        if value < self.good_slew_cal_time:
            self.slewcaltime_value.setStyleSheet("color:green")
        elif value >= self.good_slew_cal_time and value <= self.bad_slew_cal_time:
            self.slewcaltime_value.setStyleSheet("color:orange")
        elif value > self.bad_slew_cal_time:
            self.slewcaltime_value.setStyleSheet("color:red")

    # kpfred.ACF & kpfgreen.ACF
    def update_acffile(self, value):
        self.log.debug(f'update_acffile: {value}')
        self.fast = QueryFastReadMode.execute({})
        if self.fast is True:
            self.read_mode.setText('Fast')
            self.read_mode.setStyleSheet("color:orange")
        else:
            self.read_mode.setText('Normal')
            self.read_mode.setStyleSheet("color:green")

    # kpfconfig.CAHK_ENABLED
    def update_ca_hk_enabled(self, value):
        self.log.debug(f"update_ca_hk_enabled: {value}")
        if value in ['Yes', True]:
            if 'Ca_HK' in self.disabled_detectors:
                self.log.debug(f"Removing Ca HK from disbaled detectors")
                id = self.disabled_detectors.index('Ca_HK')
                self.log.debug(f"  List index = {id}")
                self.log.debug(f"  {self.disabled_detectors}")
                self.disabled_detectors.pop(id)
                self.log.debug(f"  {self.disabled_detectors}")
                self.update_disabled_detectors_value()
        elif value in ['No', False]:
            if 'Ca_HK' not in self.disabled_detectors:
                self.disabled_detectors.append('Ca_HK')
                self.update_disabled_detectors_value()

    # kpfconfig.GREEN_ENABLED
    def update_green_enabled(self, value):
        self.log.debug(f"update_green_enabled: {value}")
        if value in ['Yes', True]:
            if 'Green' in self.disabled_detectors:
                self.disabled_detectors.pop(self.disabled_detectors.index('Green'))
                self.update_disabled_detectors_value()
        elif value in ['No', False]:
            if 'Green' not in self.disabled_detectors:
                self.disabled_detectors.append('Green')
                self.update_disabled_detectors_value()

    # kpfconfig.RED_ENABLED
    def update_red_enabled(self, value):
        self.log.debug(f"update_red_enabled: {value}")
        if value in ['Yes', True]:
            if 'Red' in self.disabled_detectors:
                self.disabled_detectors.pop(self.disabled_detectors.index('Red'))
                self.update_disabled_detectors_value()
        elif value in ['No', False]:
            if 'Red' not in self.disabled_detectors:
                self.disabled_detectors.append('Red')
                self.update_disabled_detectors_value()

    # kpfconfig.EXPMETER_ENABLED
    def update_expmeter_enabled(self, value):
        self.log.debug(f"update_expmeter_enabled: {value}")
        if value in ['Yes', True]:
            if 'ExpMeter' in self.disabled_detectors:
                self.disabled_detectors.pop(self.disabled_detectors.index('ExpMeter'))
                self.update_disabled_detectors_value()
        elif value in ['No', False]:
            if 'ExpMeter' not in self.disabled_detectors:
                self.disabled_detectors.append('ExpMeter')
                self.update_disabled_detectors_value()

    def update_disabled_detectors_value(self):
        self.log.debug(f"update_disabled_detectors_value")
        self.log.debug(f"  disabled detector list: {self.disabled_detectors}")
        if isinstance(self.disabled_detectors, list) is True:
            if len(self.disabled_detectors) > 0:
                self.disabled_detectors_value.setText(",".join(self.disabled_detectors))
                self.disabled_detectors_value.setStyleSheet("color:red")
            else:
                self.disabled_detectors_value.setText('')
                self.disabled_detectors_value.setStyleSheet("color:black")
        else:
            self.disabled_detectors_value.setText('')
            self.disabled_detectors_value.setStyleSheet("color:red")

    # dcs.UT
    def update_UT(self, value):
        self.UTValue.setText(value[:-3])

    # dcs.LST
    def update_LST(self, value):
        self.SiderealTimeValue.setText(value[:-3])
        self.update_counter += 1
        if self.update_counter > 180:
            self.log.debug('Updating: SOB info, telescope_released, and history')
            self.update_counter = 0
            self.update_SOB_display() # Updates alt, az
            self.telescope_released = GetTelescopeRelease.execute({})
            self.refresh_history()


    ##-------------------------------------------
    ## Methods for Observing Menu Actions
    ##-------------------------------------------
    def run_start_of_night(self):
        self.log.debug(f"action run_start_of_night")
        # Handle case where script is currently running
        script_running = self.scriptname_value.text() not in ['', 'None', None]
        if script_running is True:
            self.do_fullstop(True)
        # Repeat check to make sure it stopped (needs proper wait added)
        script_running = self.scriptname_value.text() not in ['', 'None', None]
        if script_running is True:
            self.log.warning('Script is still running, aborting run_start_of_night')
            return
        # Confirm for start of night
        msg = ["Do you wish to run the Start Of Night script?",
               "",
               "This script will configure the FIU and AO bench for observing.",
               "The AO bench area should be clear of personnel before proceeding.",
               "Do you wish to to continue?"]
        result = ConfirmationPopup('Run Start of Night Script?', msg).exec_()
        if result == QtWidgets.QMessageBox.Yes:
            self.log.debug('Confirmation is yes, running StartOfNight script')
            launch_command_in_xterm('StartOfNight')
        else:
            self.log.debug('Confirmation is no, not running script')

    def configure_FIU(self, mode):
        self.log.info(f"configure_FIU: {mode}")
        if mode not in ['Stowed', 'Alignment', 'Acquisition', 'Observing', 'Calibration']:
            self.log.error(f"Desired FIU mode {mode} is not allowed")
            return
        launch_command_in_xterm(f'ConfigureFIU {mode}')

    def configure_FIU_observing(self):
        self.configure_FIU('Observing')

    def configure_FIU_calibrations(self):
        self.configure_FIU('Calibration')

    def configure_FIU_stow(self):
        self.configure_FIU('Stowed')

    def set_observer(self):
        self.log.debug(f"set_observer")
        observer_input = InputPopup('Set observer names', 'Observer names:')
        if observer_input.exec_():
            if self.EXPOSE.ktl_keyword.ascii == 'Ready':
                SetObserver.execute({'observer': observer_input.result.strip()})
            else:
                msg = 'Unable to set observer while exposure is in progress'
                ConfirmationPopup('Unable to set observer', msg, info_only=True, warning=True).exec_()

    def set_programID(self):
        self.log.debug(f"set_programID")
        program_input = InputPopup('Set program ID', 'Program ID:')
        if program_input.exec_():
            if self.EXPOSE.ktl_keyword.ascii == 'Ready':
                SetProgram.execute({'progname': program_input.result.strip()})
            else:
                msg = 'Unable to set program while exposure is in progress'
                ConfirmationPopup('Unable to set program', msg, info_only=True, warning=True).exec_()

    def run_end_of_night(self):
        self.log.info(f"run_end_of_night")
        # Handle case where script is currently running
        script_running = self.scriptname_value.text() not in ['', 'None', None]
        if script_running is True:
            self.do_fullstop(True)
        script_running = self.scriptname_value.text() not in ['', 'None', None]
        if script_running is True:
            self.log.warning('Script is still running, aborting run_end_of_night')
            return
        # Confirm for end of night
        msg = ["Do you wish to run the End Of Night script?",
               "",
               "This script will configure the FIU and AO bench.",
               "The AO bench area should be clear of personnel before proceeding.",
               "Do you wish to to continue?"]
        result = ConfirmationPopup('Run End of Night Script?', msg).exec_()
        if result == QtWidgets.QMessageBox.Yes:
            self.log.debug('Confirmation is yes, running EndOfNight script')
            launch_command_in_xterm(f'EndOfNight')
        else:
            self.log.debug('Confirmation is no, not running script')


    ##-------------------------------------------
    ## Methods to Operate on OB List UI
    ##-------------------------------------------
    def set_SortOrWeather(self):
        '''Set the QComboBox above the OB List to handle either the sort order
        or the weather band depending on whether we are in KPF-CC mode or not.
        '''
        self.log.debug(f"set_SortOrWeather (KPFCC={self.KPFCC})")
        if self.KPFCC == True:
            self.SortOrWeatherLabel.setText('Weather Band:')
            self.SortOrWeatherLabel.setEnabled(True)
            self.SortOrWeather.clear()
            self.SortOrWeather.addItems(self.KPFCC_weather_bands)
            self.SortOrWeather.currentTextChanged.connect(self.set_weather_band)
            self.SortOrWeather.setEnabled(True)
        else:
            self.SortOrWeatherLabel.setText('Sort List By:')
            self.SortOrWeatherLabel.setEnabled(True)
            self.SortOrWeather.clear()
            self.SortOrWeather.addItems(['', 'Name', 'RA', 'Dec', 'Gmag', 'Jmag'])
            self.SortOrWeather.currentTextChanged.connect(self.sort_OB_list)
            self.SortOrWeather.setEnabled(True)

    def sort_OB_list(self, value):
        self.log.debug(f"sort_OB_list")
        self.OBListModel.sort(value)
        self.clear_OB_selection()

    def verify_overwrite_of_OB_list(self):
        if len(self.OBListModel.OBs) == 0:
            return True
        else:
            msg = 'Loading OBs from a new program will clear the current list of OBs. Continue?'
            result = ConfirmationPopup('Overwrite OB List?', msg).exec_()
            if result == QtWidgets.QMessageBox.Yes:
                self.log.debug('Confirmed overwrite of OB list')
                return True
            else:
                self.log.debug("Cancel! Not overwriting OB list.")
                return False

    def set_weather_band(self, WB):
        if WB == "":
            return
        elif WB not in self.KPFCC_weather_bands:
            self.log.error(f'Band "{WB}" not in allowed weather band values')
            return
        self.log.info(f"set_weather_band: {WB}")
        self.SortOrWeather.setCurrentText(WB)
        self.KPFCC_weather_band = WB
        self.OBListModel.set_list(self.KPFCC_OBs[WB],
                                  start_times=self.KPFCC_start_times[WB])


    ##-------------------------------------------
    ## Methods to interact with OB files on disk
    ##-------------------------------------------
    def load_OBs_from_files(self):
        self.log.debug(f"load_OBs_from_files")
        files, filefilter = QtWidgets.QFileDialog.getOpenFileNames(self, 
                                       'Open Files', f"{self.file_path}",
                                       "OB Files (*yaml);;All Files (*)")
        if files:
            for file in files:
                file = Path(file)
                if file.exists():
                    self.log.debug(f"Opening: {str(file)}")
                    newOB = ObservingBlock(file)
                    if newOB.validate() == True:
                        self.OBListModel.appendOB(newOB)
                    self.file_path = Path(file).parent

    def save_OB_to_file(self, OB, default=None):
        self.log.debug('save_OB_to_file')
        if default is None: default = self.file_path
        result = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File',
                                             f"{default}",
                                             "OB Files (*yaml);;All Files (*)")
        if result:
            save_file = result[0]
            if save_file != '':
                # save fname as path to use in future
                self.file_path = Path(save_file).parent
                self.log.info(f'Saving OB to file: {save_file}')
                OB.write_to(save_file)
        else:
            self.log.debug('No output file chosen')

    def load_OB_from_file(self):
        self.log.debug('load_SciOB_from_file')
        newOB = None
        file, filefilter = QtWidgets.QFileDialog.getOpenFileName(self, 
                                     "Open File", f"{self.file_path}",
                                     "OB Files (*yaml);;All Files (*)")
        if file:
            file = Path(file)
            if file.exists():
                self.file_path = file.parent
                self.log.debug(f"Opening: {str(file)}")
                newOB = ObservingBlock(file)
        return newOB


    ##-------------------------------------------
    ## Methods to Populate OB List (and star list)
    ##-------------------------------------------
        # This select/deselect operation caches something in the AltAz 
        # calculation which happens the first time an OB is selected. This
        # just makes the GUI more "responsive" as the loading of the OBs when
        # program ID is chosen contains all of the slow caching of values
        # instead of having it happen on the first click.
#         if len(self.OBListModel.OBs) > 0:
#             self.select_OB(0)
#             self.select_OB(-1)

    def clear_OB_list(self):
        self.log.debug(f"clear_OB_list")
        self.clear_OB_selection()
        self.KPFCC = False
        self.OBListHeader.setText(self.hdr)
        self.OBListModel.clear_list()
        self.set_SortOrWeather()

    def load_OBs_from_program(self):
        self.log.debug(f"load_OBs_from_program")
        if self.verify_overwrite_of_OB_list():
            select_program_popup = SelectProgramPopup(self.program_strings)
            if select_program_popup.exec():
                progID = select_program_popup.ProgID
                self.ProgressBar.setVisible(True)
                self.ProgressBar.setMinimum(0)
                self.ProgressBar.setMaximum(0)
                msg = f"Retrieving OBs for program {progID}"
                self.GUITaskLabel.setText(msg)
                self.KPFCC = False
                self.clear_OB_selection()
                self.OBListHeader.setText(self.hdr)
                OBs = GetObservingBlocksByProgram.execute({'program': progID})
                msg = f"Retrieved {len(OBs)} OBs for program {progID}"
                self.GUITaskLabel.setText(msg)
                self.log.debug(msg)
                self.OBListModel.set_list(OBs)
                self.set_SortOrWeather()
#                 ConfirmationPopup('Retrieved OBs from Database', msg, info_only=True).exec_()
            else:
                self.log.debug("Cancel! Not pulling OBs from database.")
        self.ProgressBar.setMinimum(0)
        self.ProgressBar.setMaximum(100)
        self.ProgressBar.setValue(100)

    def load_OBs_from_KPFCC(self):
        '''This loads KPF-CCs in to a classical observing mode.
        '''
        self.log.debug(f"load_OBs_from_KPFCC")
        if not self.verify_overwrite_of_OB_list():
            return
        self.clear_OB_selection()
        self.KPFCC = False
        self.OBListHeader.setText(self.hdr)
        classical, cadence = GetScheduledPrograms.execute({'semester': 'current'})
        progIDs = set([p['ProjCode'] for p in cadence])
        self.OBListModel.clear_list()
        self.ProgressBar.setVisible(True)
        self.ProgressBar.setValue(0)
        self.GUITaskLabel.setText(f'Retrieving OBs from all {len(progIDs)} KPF-CC programs.')
        # Create progress bar if we have a lot of programs to query
#         usepbar = len(progIDs) > 5 
#         if usepbar:
#             progress = QtWidgets.QProgressDialog("Retrieving OBs from Database", "Cancel", 0, len(progIDs))
#             progress.setWindowModality(QtCore.Qt.WindowModal) # Make it modal (blocks interaction with parent)
#             progress.setAutoClose(True) # Dialog closes automatically when value reaches maximum
#             progress.setAutoReset(True) # Dialog resets automatically when value reaches maximum
        # Iterate of KPF-CC programIDs and retrieve their OBs from DB
        for i,progID in enumerate(progIDs):
            self.log.debug(f'Retrieving OBs for {progID}')
            programOBs = GetObservingBlocksByProgram.execute({'program': progID})
            self.OBListModel.extend(programOBs)
            self.log.debug(f'  Got {len(programOBs)} for {progID}, total KPF-CC OB count is now {len(self.OBListModel.OBs)}')
            self.ProgressBar.setValue(int((i+1)/len(progIDs)*100))
#             if usepbar:
#                 if progress.wasCanceled():
#                     self.log.error("Retrieval of OBs canceled by user.")
#                     break
#                 progress.setValue(i+1)
        self.GUITaskLabel.setText(f'Retrieved {len(self.OBListModel.OBs)} OBs from all {len(progIDs)} KPF-CC programs.')
        self.set_SortOrWeather()

    def load_OBs_from_schedule(self):
        self.log.debug(f"load_OBs_from_schedule")
        if self.verify_overwrite_of_OB_list() == False:
            return
        self.ProgressBar.setVisible(True)
        self.ProgressBar.setValue(0)
        self.KPFCC = True
        self.OBListHeader.setText('   StartTime '+self.hdr)
        # Form location to look for KPF-CC schedule files
        utnow = datetime.datetime.utcnow()
        date = utnow-datetime.timedelta(hours=20) # Switch dates at 10am HST, 2000UT
        date_str = date.strftime('%Y-%m-%d').lower()
        if self.clargs.mock_date == True:
            date_str = '2025-07-10'
            self.log.warning(f'Using schedule from {date_str} for testing')
        schedule_files = [self.schedule_path / f'{date_str}_{WB}.csv'
                          for WB in self.KPFCC_weather_bands]
        # Count what we need to load ahead of time for the progress bar
        schedule_file_contents = {}
        Nsched = 0
        pbar_msg = []
        for i,WB in enumerate(self.KPFCC_weather_bands):
            if schedule_files[i].exists():
                schedule_file_contents[WB] = Table.read(schedule_files[i], format='ascii.csv')
                nOBs = len(schedule_file_contents[WB])
                Nsched += nOBs
                pbar_msg.append(f'Schedule for weather band {WB} contains {nOBs} OBs')
            else:
                schedule_file_contents[WB] = []
                pbar_msg.append(f'Could not find schedule for weather band {WB}')
                self.log.error(f'No schedule file found at {schedule_files[i]}')
        self.log.debug(f"Pre-counted {Nsched} OBs to get for KPF-CC in all weather bands")
        GUImsg = [f"Loading {Nsched} OBs from schedule"]
        self.GUITaskLabel.setText('\n'.join(GUImsg))
        # Create progress bar if we have a lot of OBs to retrieve
#         usepbar = Nsched > 15
#         if usepbar:
#             pbar_title = f"Retrieving {Nsched} OBs for all weather bands\n\n"
#             if len(pbar_msg) > 0:
#                 pbar_title += '\n'.join(pbar_msg)
#             progress = QtWidgets.QProgressDialog(pbar_title, "Cancel", 0, Nsched)
#             progress.setWindowModality(QtCore.Qt.WindowModal) # Make it modal (blocks interaction with parent)
#             progress.setAutoClose(True) # Dialog closes automatically when value reaches maximum
#             progress.setAutoReset(True) # Dialog resets automatically when value reaches maximum
#             progress.setValue(0)
#             self.log.debug('Created progress bar')
        if Nsched == 0:
            ConfirmationPopup('Found no OBs in schedule', '\n'.join(pbar_msg), info_only=True).exec_()
        scheduledOBcount = 0
        retrievedOBcount = 0
        errs = []
        for i,WB in enumerate(self.KPFCC_weather_bands):
            nOBs_this_WB = len(schedule_file_contents[WB])
            self.log.debug(f'Getting {nOBs_this_WB} OBs for weather band {WB}')
            # Pre-load a slewcal OB for convienience
            if self.slewcalOB is not None:
                self.KPFCC_OBs[WB] = [self.slewcalOB]
                self.KPFCC_start_times[WB] = [0]
            else:
                self.KPFCC_OBs[WB] = []
                self.KPFCC_start_times[WB] = []
            for entry in schedule_file_contents[WB]:
                scheduledOBcount += 1
                if entry['unique_id'] in ['', None, 'None']:
                    errmsg = f"{entry['Target']} Failed: no id"
                    self.log.error(errmsg)
                    errs.append(errmsg)
                    self.GUITaskLabel.setText('\n'.join(GUImsg+errs))
                else:
                    result = GetObservingBlocks.execute({'OBid': entry['unique_id']})[0]
                    if isinstance(result, ObservingBlock):
                        self.KPFCC_OBs[WB].append(result)
                        start = entry['StartExposure'].split(':')
                        start_decimal = int(start[0]) + int(start[1])/60
                        self.KPFCC_start_times[WB].append(start_decimal)
                        retrievedOBcount += 1
                    else:
                        errmsg = f"{entry['Target']} Failed: {result[1]} ({result[0]})"
                        self.log.error(errmsg)
                        errs.append(errmsg)
                self.ProgressBar.setValue(int(scheduledOBcount/Nsched*100))
#                 if usepbar:
#                     if progress.wasCanceled():
#                         self.log.error("Retrieval of OBs canceled by user.")
#                         break
#                     progress.setValue(scheduledOBcount)
            # Append a slewcal OB for convienience
            if self.slewcalOB is not None:
                self.KPFCC_OBs[WB].append(self.slewcalOB)
                self.KPFCC_start_times[WB].append(24)
        msg = [f"Retrieved {retrievedOBcount} (out of {scheduledOBcount}) OBs for all weather bands"]
        self.GUITaskLabel.setText("".join(msg))
        msg.extend(errs)
#         ConfirmationPopup('Retrieved OBs from Database', '\n'.join(msg), info_only=True).exec_()
        self.refresh_history()
        self.set_SortOrWeather()
        self.set_weather_band(self.KPFCC_weather_band)

    def refresh_history(self):
        self.log.debug(f"refresh_history")
        date_str = 'today'
        if self.clargs.mock_date == True:
            date_str = '2025-07-10'
            self.log.warning(f'Using history from {date_str} for testing')
        history = GetExecutionHistory.execute({'utdate': date_str})
        self.OBListModel.refresh_history(history)
        self.HistoryListModel.refresh_history(history)

    ##-------------------------------------------
    ## Methods for Selected OB
    ##-------------------------------------------
    def select_OB(self, selected, deselected):
        self.log.debug(f"select_OB {selected} {deselected}")
        if len(selected.indexes()) > 0:
            self.SOBindex = selected.indexes()[0].row()
        else:
            self.SOBindex = -1
        self.update_SOB_display()

    def set_SOB_enabled(self):
        self.log.debug(f"set_SOB_enabled")
        cal_only = False
        enabled = False
        # Is an OB selected?
        OBselected = self.SOBindex >= 0
        if not OBselected:
            tool_tip = 'No OB selected.'
            caltt = tool_tip
        # Is a script currently running?
        elif self.SCRIPTNAME.ktl_keyword.ascii not in ['', 'None']:
            tool_tip = 'A script is already running'
            caltt = tool_tip
        # Is SCRIPTSTOP requested?
        elif self.SCRIPTSTOP.ktl_keyword.ascii == 'Yes':
            tool_tip = 'SCRIPTSTOP has been requested.'
            caltt = tool_tip
        # Is Target observable
        elif self.SOBobservable == False:
            enabled = True
            tool_tip = 'WARNING: Target is not observable.'
            caltt = tool_tip
        else:
            enabled = True
            tool_tip = ''
            SOB = self.OBListModel.OBs[self.SOBindex]
            cal_only = (len(SOB.Observations) == 0) and (len(SOB.Calibrations) > 0)
            caltt = {False: '', True: 'Slewcal disabled for Calibration OB'}[cal_only]
        self.log.debug(f"  {enabled} {tool_tip}")
        self.SOB_ShowButton.setEnabled(OBselected)
        self.SOB_ExecuteButton.setEnabled(enabled)
        self.SOB_ExecuteButton.setToolTip(tool_tip)
        self.SOB_ExecuteSlewCalButton.setEnabled(enabled and not cal_only)
        self.SOB_ExecuteSlewCalButton.setToolTip(caltt)
        self.SOB_RemoveFromList.setEnabled(enabled)

    def clear_SOB_Target(self):
        self.log.debug(f"clear_SOB_Target")
        self.SOB_TargetName.setText('--')
        self.SOB_GaiaID.setText('--')
        self.SOB_TargetRA.setText('--')
        self.SOB_TargetDec.setText('--')
        self.SOB_Mags.setText('--')
        self.SOB_AltAz.setText('--')
        self.SOB_AltAz.setStyleSheet("color:black")
        self.SOB_AltAz.setToolTip("")
        self.SOB_AzSlew.setText('--')
        self.SOB_ELSlew.setText('--')
        self.SOBobservable = False
        self.set_SOB_enabled()

    def set_SOB_Target(self, SOB):
        self.log.debug(f"set_SOB_Target")
        self.clear_SOB_Target()
        self.SOB_TargetName.setText(SOB.Target.get('TargetName'))
        self.SOB_GaiaID.setText(SOB.Target.get('GaiaID'))
        self.SOB_Mags.setText(f"G={SOB.Target.get('Gmag'):.2f}, J={SOB.Target.get('Jmag'):.2f}")
        # Display RA and Dec
        try:
            coord_string = SOB.Target.coord.to_string('hmsdms', sep=':', precision=2)
            RA_str, Dec_str = coord_string.split()
        except Exception as e:
            self.log.error('Failed to stringify coordinate')
            self.log.error(e)
            RA_str = SOB.Target.get('RA')
            Dec_str = SOB.Target.get('Dec')
            self.SOB_TargetRALabel.setText('RA (Epoch=?):')
            self.SOB_TargetDecLabel.setText('Dec (Epoch=?):')
        RAlabel = f"RA:"
        DecLabel = f"Dec:"
        # If proper motion values are set, try to propagate proper motions
        if abs(SOB.Target.PMRA.value) > 0.001 or abs(SOB.Target.PMDEC.value) > 0.001:
            try:
                now = Time(datetime.datetime.utcnow())
                coord_now = SOB.Target.coord.apply_space_motion(new_obstime=now)
                coord_now_string = coord_now.to_string('hmsdms', sep=':', precision=2)
                RA_str, Dec_str = coord_now_string.split()
                RAlabel = f"RA (epoch=now):"
                DecLabel = f"Dec (epoch=now):"
            except Exception as e:
                self.log.error('Failed to propagate proper motions for display')
                self.log.error(e)
        self.SOB_TargetRA.setText(RA_str)
        self.SOB_TargetDec.setText(Dec_str)
        self.SOB_TargetRALabel.setText(RAlabel)
        self.SOB_TargetDecLabel.setText(DecLabel)

        # Calculate AltAz Position
        if SOB.Target.coord is None:
            self.log.warning(f'SOB Target is not convertable to SkyCoord')
        else:
            AltAzSystem = AltAz(obstime=Time.now(), location=self.keck,
                                pressure=620*u.mbar, temperature=0*u.Celsius)
            tick = datetime.datetime.now()
            target_altz = SOB.Target.coord.transform_to(AltAzSystem)
            elapsed = (datetime.datetime.now()-tick).total_seconds()*1000
            self.log.debug(f'Calculated target AltAz coordinates in {elapsed:.0f}ms')
            self.SOB_AltAz.setText(f"{target_altz.alt.deg:.1f}, {target_altz.az.deg:.1f} deg")
            self.SOBobservable = above_horizon(target_altz.az.deg, target_altz.alt.deg)
            if self.SOBobservable:
                if target_altz.alt.deg > self.ADC_horizon:
                    self.SOB_AltAz.setStyleSheet("color:black")
                    self.SOB_AltAz.setToolTip("")
                else:
                    self.SOB_AltAz.setStyleSheet("color:orange")
                    self.SOB_AltAz.setToolTip(f"ADC correction is poor below EL~{self.ADC_horizon:.0f}")
            else:
                self.SOB_AltAz.setStyleSheet("color:red")
                self.SOB_AltAz.setToolTip("Below Keck horizon")
            if near_horizon(target_altz.az.deg, target_altz.alt.deg):
                # Calculate AZ Slew Distance
                #  Azimuth range for telescope is -125 to 0 to 325
                #  North wrap is -125 to -35
                #  South wrap is 235 to 325
                nwrap = self.DCS_AZ.binary <= -35
                swrap = self.DCS_AZ.binary >= 235
                tel_az = Angle(self.DCS_AZ.binary*u.radian).to(u.deg)
                dest_az = Angle(target_altz.az.deg*u.deg)
                dest_az.wrap_at(325*u.deg, inplace=True)
                slew = abs(tel_az - dest_az)
                slewmsg = f"{tel_az.value:.1f} to {dest_az.value:.1f} = {slew:.1f}"
                self.SOB_AzSlew.setText(slewmsg)
                # Calculate EL Slew Distance
                tel_el = Angle(self.DCS_EL.binary*u.radian).to(u.deg)
                dest_el = Angle(target_altz.alt.deg*u.deg)
                slew = abs(tel_el - dest_el)
                slewmsg = f"{tel_el.value:.1f} to {dest_el.value:.1f} = {slew:.1f}"
                self.SOB_ELSlew.setText(slewmsg)
            else:
                self.SOB_AzSlew.setText("--")
                self.SOB_ELSlew.setText("--")

    def update_SOB_display(self):
        self.log.debug(f"update_SOB_display: SOBindex = {self.SOBindex}")
        self.log.debug(f"OBList contains {len(self.OBListModel.OBs)} entries")
        self.update_counter = 0
        if self.SOBindex < 0:
            self.clear_SOB_Target()
            self.SOB_Observation1.setText('--')
            self.SOB_Observation2.setText('--')
            self.SOB_Observation3.setText('--')
            self.SOB_ExecutionTime.setText('--')
            self.SOB_NotesForObserver.setText('')
            self.SOB_NotesForObserver.setToolTip('')
            self.SOB_AddComment.setEnabled(False)
        else:
            SOB = self.OBListModel.OBs[self.SOBindex]
            self.SOB_NotesForObserver.setText(SOB.CommentToObserver)
            self.SOB_NotesForObserver.setToolTip(SOB.CommentToObserver)
            # Is OB from DB?
            if SOB.OBID == '':
                no_comment_msg = 'Can not submit comment without database ID.'
                self.SOB_AddComment.setEnabled(False)
                self.SOB_AddComment.setToolTip(no_comment_msg)
            else:
                self.SOB_AddComment.setEnabled(True)
                self.SOB_AddComment.setToolTip('')
            # Handle Target component
            if SOB.Target is None:
                self.clear_SOB_Target()
                self.SOBobservable = True
            else:
                self.set_SOB_Target(SOB)
            # Handle Calibrations and Observations components
            obs_and_cals = SOB.Calibrations + SOB.Observations
            n_per_line = int(np.ceil(len(obs_and_cals)/3))
            for i in [1,2,3]:
                field = getattr(self, f'SOB_Observation{i}')
                strings = [obs_and_cals.pop(0).summary() for j in range(n_per_line) if len(obs_and_cals) > 0]
                field.setText(', '.join(strings))
            # Calculate OB Duration
            duration = EstimateOBDuration.execute({'fast': self.fast}, OB=SOB)
            self.SOB_ExecutionTime.setText(f"{duration:.0f} min")
        self.set_SOB_enabled()

    def remove_SOB(self):
        self.clear_OB_selection()
        self.OBListModel.removeOB(self.SOBindex)

    def clear_OB_selection(self):
        self.log.debug(f"clear_OB_selection")
        self.OBListView.selectionModel().clearSelection()
        self.SOBindex = -1
        self.update_SOB_display()

    def show_SOB(self):
        if self.SOBindex < 0:
            return
        SOB = self.OBListModel.OBs[self.SOBindex]
        if SOB is None:
            return
        OBcontents_popup = OBContentsDisplay(SOB)
        OBcontents_popup.setWindowTitle(f"Full OB Contents: {SOB.summary()}")
        result = OBcontents_popup.exec_()
        if result == QtWidgets.QMessageBox.Ok:
            self.log.debug('Show popup: Ok')
        elif result == QtWidgets.QMessageBox.Open:
            self.log.info('Show popup: Open/Edit')
            OBedit_popup = EditableMessageBox(SOB)
            OBedit_popup.setWindowTitle(f"Editing OB: {SOB.summary()}")
            edit_result = OBedit_popup.exec_()
            if edit_result == QtWidgets.QMessageBox.Ok:
                self.log.info('Edit popup: Ok')
                if OBedit_popup.result.validate():
                    self.log.info('The edited OB has been validated')
                    self.OBListModel.updateOB(self.SOBindex, OBedit_popup.result)
                    self.update_SOB_display()
                else:
                    self.log.warning('Edits did not validate. Not changing OB.')
            elif edit_result == QtWidgets.QMessageBox.Cancel:
                self.log.debug('Edit popup: Cancel')

    def add_comment(self):
        if self.SOBindex < 0:
            self.log.warning('add_comment: No OB selected')
            return
        SOB = self.OBListModel.OBs[self.SOBindex]
        comment_box = ObserverCommentBox(SOB, self.Observer.text())
        if comment_box.exec():
            self.log.info(f"Submitting comment: {comment_box.comment}")
            self.log.info(f"From commentor: {comment_box.observer}")
            params = {'OBid': SOB.OBID,
                      'observer': comment_box.observer,
                      'comment': comment_box.comment,
                      }
            SubmitObserverComment.execute(params)
        else:
            self.log.debug("Cancel! Not submitting comment.")

    ##-------------------------------------------
    ## Methods to Execute an OB
    ##-------------------------------------------
    def prepare_execution_history_file(self):
        # Prepare KPFCC schedule execution records
        semester, start, end = get_semester_dates(datetime.datetime.now())
        logdir = Path(f'/s/sdata1701/KPFTranslator_logs/')
        self.execution_history_file = logdir / f'KPFCC_executions_{semester}.csv'
        if self.execution_history_file.exists() is False:
            with open(self.execution_history_file, 'w') as f:
                contents = ['# timestamp', 'decimalUT', 'executedID', 'OB summary',
                            'executed_line', 'scheduleUT',
                            'schedule_current_line', 'scheduleUT_current',
                            'schedule_next_line', 'scheduleUT_next',
                            'on_schedule']
                hdrline = ', '.join(contents)
                f.write(hdrline+'\n')

    def execute_SOB(self, slewcal=False):
        if self.SOBindex < 0:
            return
        self.log.debug(f"execute_SOB")
        SOB = self.OBListModel.OBs[self.SOBindex]
        msg = ["Do you really want to execute the current OB?", '',
               f"{SOB.summary()}"]
        result = ConfirmationPopup('Execute Science OB?', msg).exec_()
        if result == QtWidgets.QMessageBox.Yes:
            if SOB.Target is not None and self.OBListModel.telescope_interactions_allowed():
                SelectTarget.execute(SOB.Target.to_dict())
            if self.KPFCC == True:
                # Log execution
                now = datetime.datetime.utcnow()
                now_str = now.strftime('%Y-%m-%d %H:%M:%S UT')
                decimal_now = now.hour + now.minute/60 + now.second/3600
                start_time = self.OBListModel.start_times[self.SOBindex]
                start_current = self.OBListModel.start_times[self.OBListModel.currentOB]
                start_next = self.OBListModel.start_times[self.OBListModel.nextOB]
                on_schedule = self.SOBindex in [self.OBListModel.currentOB, self.OBListModel.nextOB]
                contents = [now_str, f'{decimal_now:.2f}', f'{SOB.OBID}',
                            f'{SOB.summary().replace(",", "_")}',
                            f'{self.SOBindex}', f'{start_time:.2f}',
                            f'{self.OBListModel.currentOB}', f'{start_current:.2f}',
                            f'{self.OBListModel.nextOB}', f'{start_next:.2f}',
                            f'{on_schedule}']
                line = ', '.join(contents)
                if not self.execution_history_file.exists():
                    self.prepare_execution_history_file()
                with open(self.execution_history_file, 'a') as f:
                    f.write(line+'\n')
                if not on_schedule:
                    self.log.schedule(f'Running OB {self.SOBindex} off schedule')
                    self.log.schedule(f'  Start time for this OB is {start_time:.2f} UT')
                    self.log.schedule(f'  Start time for scheduled OB is {start_current:.2f} UT')
                    self.log.schedule(f'  Start time for next OB is {start_next:.2f} UT')
            self.RunOB(SOB)
        else:
            self.log.debug('User opted not to execute OB')

    def execute_SOB_with_slewcal(self):
        self.execute_SOB(slewcal=True)

    def RunOB(self, SOB, slewcal=False):
        self.log.debug(f"RunOB")
        # Write to temporary file
        utnow = datetime.datetime.utcnow()
        now_str = utnow.strftime('%Y%m%dat%H%M%S')
        date = utnow-datetime.timedelta(days=1)
        date_str = date.strftime('%Y%b%d').lower()
        for handler in self.log.handlers:
            if isinstance(handler, logging.FileHandler):
                log_file_path = Path(handler.baseFilename).parent
        tmp_file_path = log_file_path / date_str
        if tmp_file_path.exists() is False:
            tmp_file_path.mkdir(mode=0o777, parents=False)
        tmp_file = tmp_file_path / f'executedOB_{now_str}.yaml'
        SOB.write_to(tmp_file)
        if slewcal == True:
            self.SLEWCALREQ.write(True)
            self.SLEWCALREQ.waitFor("== 'Yes", timeout=0.3)
        launch_command_in_xterm(f'RunOB -f {tmp_file}', capture_stdout=True,
                                window_title=f"RunOB {SOB.summary()}")


    ##--------------------------------------------------------------
    ## Methods for History Tab
    ##--------------------------------------------------------------
    def select_exposure(self, selected, deselected):
        self.log.debug(f"select_exposure {selected} {deselected}")
        if len(selected.indexes()) > 0:
            self.exp_index = selected.indexes()[0].row()
            exposure = self.HistoryListModel.exposures[self.exp_index]
            is_junk = exposure.get('junk') in ['True', True]
            if is_junk:
                self.MarkExposureJunk.setText('Mark Selected Exposure as Good')
            else:
                self.MarkExposureJunk.setText('Mark Selected Exposure as Junk')
        else:
            self.exp_index = -1


    def mark_exposure_junk(self):
        self.log.debug(f'mark_exposure_junk')
        if self.exp_index > 0:
            exposure = self.HistoryListModel.exposures[self.exp_index]
            is_junk = exposure.get('junk') in ['True', True]
            SetJunkStatus.execute({'id': exposure.get('id'),
                                   'timestamp': exposure.get('timestamp'),
                                   'junk': not is_junk})
            self.HistoryListModel.sort()


    ##--------------------------------------------------------------
    ## Generic Methods to Build an OB Component
    ##--------------------------------------------------------------
    def BuildOBC_set(self, input_object, input_class_name=None):
        if input_class_name is None:
            if type(input_object) == list:
                input_class_name = type(input_object[0]).__name__
            else:
                input_class_name = type(input_object).__name__
        self.log.debug(f"Running BuildOBC_set on a {input_class_name}")
        setattr(self, f'Build{input_class_name}', input_object)
        self.BuildOBC_render_text(input_class_name)

    def BuildOBC_render_text(self, input_class_name):
        self.log.debug(f"Running BuildOBC_render_text for {input_class_name}")
        thing = getattr(self, f'Build{input_class_name}')
        view = getattr(self, f'Build{input_class_name}View')
        edited_lines = view.document().toPlainText()
        # Record cursor position
        cursor = view.textCursor()
        cursor_position = cursor.position()
        if thing in [None, []]:
            lines = ''
        elif type(thing) == list:
            lines = ''
            for i,item in enumerate(thing):
                lines += f'# {input_class_name} {i+1}\n'
                lines += item.__repr__(prune=True, comment=True)
        else:
            lines = thing.__repr__(prune=True, comment=True)
        if edited_lines != lines:
            view.setPlainText(lines)
            # Restore cursor position
            try:
                cursor.setPosition(cursor_position)
                view.setTextCursor(cursor)
            except Exception as e:
                self.log.error(f'Failed to set cursor position in {view}')
                self.log.error(e)
        valid = getattr(self, f'Build{input_class_name}Valid')
        if thing in [None, []]:
            isvalid = False
        elif type(thing) == list:
            isvalid = np.all([item.validate() for item in thing])
        else:
            isvalid = thing.validate()
        color = {True: 'green', False: 'orange'}[isvalid]
        valid.setText(str(isvalid))
        valid.setStyleSheet(f"color:{color}")

    def BuildOBC_edit(self, input_class_name):
        self.log.debug(f"Running BuildOBC_edit for {input_class_name}")
        thing = getattr(self, f'Build{input_class_name}')
        view = getattr(self, f'Build{input_class_name}View')
        edited_lines = view.document().toPlainText()
        if edited_lines == '' and thing is None:
            return
        if type(thing) == list:
            lines = ''
            for i,item in enumerate(thing):
                lines += f'# {input_class_name} {i+1}\n'
                lines += item.__repr__(prune=False, comment=True)
        else:
            lines = thing.__repr__(prune=False, comment=True)
        if edited_lines != lines:
            try:
                new_data = yaml.safe_load(edited_lines)
                class_dict = {"Target": Target, "Observation": Observation, "Calibration": Calibration}
                if input_class_name == 'Target':
                    new_thing = class_dict[input_class_name](new_data)
                elif input_class_name in ['Observation', 'Calibration']:
                    new_thing = [class_dict[input_class_name](item) for item in new_data]
                self.BuildOBC_set(new_thing)
            except Exception as e:
                self.log.error(f'Failed to parse edited {input_class_name} text')
                self.log.error(e)
                self.log.error(f'Not changing contents')


    ##--------------------------------------------------------------
    ## Methods for the Build a Science OB Tab Target Section
    ##--------------------------------------------------------------
    def set_Target(self, target):
        self.BuildOBC_set(target)
        self.form_SciOB()

    def clear_Target(self):
        self.set_Target(Target({}))

    def edit_Target(self):
        self.BuildOBC_edit('Target')
        self.form_SciOB()

    def query_Simbad(self):
        self.log.debug(f"Running query_Simbad")
        target_name = self.QuerySimbadLineEdit.text().strip()
        self.log.debug(f"Querying: {target_name}")
        newtarg = self.BuildTarget.resolve_name(target_name)
        if newtarg is None:
            self.log.warning(f"Query failed for {target_name}")
        self.QuerySimbadLineEdit.setText('')
        self.set_Target(newtarg)


    ##--------------------------------------------------------------
    ## Methods for the Build a Science OB Tab Observations Section
    ##--------------------------------------------------------------
    def set_Observations(self, observations):
        self.BuildOBC_set(observations)
        self.form_SciOB()

    def clear_Observations(self):
        self.log.debug(f"Running clear_Observations")
        self.set_Observations([Observation({})])

    def edit_Observations(self):
        self.BuildOBC_edit('Observation')
        self.form_SciOB()


    ##--------------------------------------------------------------
    ## Methods for the Build a Science OB Tab Observing Block
    ##--------------------------------------------------------------
    def form_SciOB(self):
        self.log.debug(f"Running form_SciOB")
        semester, start, end = get_semester_dates(datetime.datetime.now())
        if self.SciOBProgramID.text() != '':
            OBdict = {'ProgramID': self.SciOBProgramID.text(),
                      'semester': semester,
                      'semid': f'{semester}_{self.SciOBProgramID.text()}'}
        else:
            OBdict = {}
        newOB = ObservingBlock(OBdict)
        newOB.Target = self.BuildTarget
        newOB.Observations = self.BuildObservation
        if newOB.__repr__() == self.SciObservingBlock.__repr__():
            self.log.debug('newOB and existing OB match')
            return
        self.SciObservingBlock = ObservingBlock(OBdict)
        self.SciObservingBlock.Target = self.BuildTarget
        self.SciObservingBlock.Observations = self.BuildObservation
        # Validate
        OBValid = self.SciObservingBlock.validate()
        color = {True: 'green', False: 'orange'}[OBValid]
        self.SciOBValid.setText(str(OBValid))
        self.SciOBValid.setStyleSheet(f"color:{color}")
        if OBValid:
            self.SciOBString.setText(self.SciObservingBlock.summary())
            duration = EstimateOBDuration.execute({}, OB=self.SciObservingBlock)
            self.SciOBEstimatedDuration.setText(f"{duration:.0f} min")
        else:
            self.SciOBString.setText('')
            self.SciOBEstimatedDuration.setText('')

    def send_SciOB_to_list(self):
        if self.SciObservingBlock.validate() != True:
            self.log.warning('OB is invalid, not sending to OB list')
            return
        targetname = self.SciObservingBlock.Target.TargetName
        self.log.info(f"Adding {targetname} to OB list")
        self.OBListModel.appendOB(self.SciObservingBlock)

    def save_SciOB_to_file(self):
        self.log.debug('save_SciOB_to_file')
        targname = self.SciObservingBlock.Target.get('TargetName')
        self.save_OB_to_file(self.SciObservingBlock,
                             default=f"{self.file_path}/{targname}.yaml")

    def load_SciOB_from_file(self):
        self.log.debug('load_SciOB_from_file')
        newOB = self.load_OB_from_file()
        if newOB.validate() == True:
            if newOB.ProgramID is not None:
                self.SciOBProgramID.setText(newOB.ProgramID)
            self.set_Target(newOB.Target)
            self.set_Observations(newOB.Observations)


    ##-------------------------------------------
    ## Methods for the Build a Calibration OB Tab
    ##-------------------------------------------
    def set_Calibrations(self, calibrations):
        self.BuildOBC_set(calibrations)
        self.form_CalOB()

    def clear_Calibrations(self):
        self.log.debug(f"Running clear_Calibrations")
        self.BuildOBC_set([], input_class_name='Calibration')
        self.ExampleCalibrations.setCurrentText('')

    def edit_Calibrations(self):
        self.BuildOBC_edit('Calibration')
        self.form_CalOB()

    def add_example_calibration(self, value):
        self.log.debug(f'add_example_calibration: {value}')
        for cal in self.example_calOB.Calibrations:
            if value == cal.get('Object'):
                self.log.debug(f'Adding {value} from example Cal OB')
                calibrations = copy.deepcopy(self.BuildCalibration)
                calibrations.append(cal)
                self.set_Calibrations(calibrations)

    def form_CalOB(self):
        self.log.debug(f"Running form_CalOB")
        semester, start, end = get_semester_dates(datetime.datetime.now())
        OBdict = {'ProgramID': 'ENG',
                  'semester': semester,
                  'semid': f'{semester}_ENG'}
        newOB = ObservingBlock(OBdict)
        newOB.Calibrations = self.BuildCalibration if self.BuildCalibration is not None else []
        if newOB.__repr__() == self.CalObservingBlock.__repr__():
            return
        self.CalObservingBlock = copy.deepcopy(newOB)
        OBValid = self.CalObservingBlock.validate()
        color = {True: 'green', False: 'orange'}[OBValid]
        self.CalOBValid.setText(str(OBValid))
        self.CalOBValid.setStyleSheet(f"color:{color}")
        if OBValid:
            self.CalOBString.setText(self.CalObservingBlock.summary())
            duration = EstimateOBDuration.execute({}, OB=self.CalObservingBlock)
            self.CalEstimatedDuration.setText(f"{duration:.0f} min")
        else:
            self.CalOBString.setText('')
            self.CalEstimatedDuration.setText('')

    def send_CalOB_to_list(self):
        if self.CalObservingBlock.validate() != True:
            self.log.warning('OB is invalid, not sending to OB list')
        else:
            self.OBListModel.appendOB(self.CalObservingBlock)

    def save_CalOB_to_file(self):
        self.log.debug('save_CalOB_to_file')
        self.save_OB_to_file(self.CalObservingBlock,
                             default=f"{self.file_path}/newcalibration.yaml")

    def save_SciOB_to_file(self):
        self.log.debug('save_SciOB_to_file')
        targname = self.SciObservingBlock.Target.get('TargetName')
        self.save_OB_to_file(self.SciObservingBlock,
                             default=f"{self.file_path}/{targname}.yaml")

    def load_CalOB_from_file(self):
        self.log.debug('load_CalOB_from_file')
        newOB = self.load_OB_from_file()
        if newOB.validate() == True:
            self.set_Calibrations(newOB.Calibrations)


    ##-------------------------------------------
    ## High Level app methods
    ##-------------------------------------------
    def exit(self):
        self.log.info("Exiting ...")
        sys.exit(0)


##-------------------------------------------------------------------------
## Define main()
##-------------------------------------------------------------------------
def main(clargs):
    application = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow(clargs)
    main_window.setupUi()
    main_window.show()
    return kPyQt.run(application)

##-------------------------------------------------------------------------
## if __name__ == '__main__':
##-------------------------------------------------------------------------
if __name__ == '__main__':
    ## Parse Command Line Arguments
    p = argparse.ArgumentParser(description='''
    ''')
    ## add flags
    p.add_argument("-v", "--verbose", dest="verbose",
        default=False, action="store_true",
        help="Be verbose! (default = False)")
    ## add options
    p.add_argument("--mock_date", dest="mock_date",
        default=False, action="store_true",
        help="Pull a fixed date for schedule and history (intended for testing).")
    p.add_argument("--loadschedule", dest="loadschedule",
        default=False, action="store_true",
        help="Load KPF-CC schedule on startup.")
    clargs = p.parse_args()

    guilog = create_GUI_log(verbose=clargs.verbose)
    guilog.info(f"-----------------------------")
    guilog.info(f"Starting KPF OB GUI")
    try:
        main(clargs)
    except Exception as e:
        guilog.error(e)
        guilog.error(traceback.format_exc())
    guilog.info(f"Exiting KPF OB GUI")

