#!/kroot/rel/default/bin/kpython3
import sys
import os
import traceback
import time
import copy
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import json
import re
import yaml
import datetime
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, Angle
from astropy.time import Time

import ktl                      # provided by kroot/ktl/keyword/python
import kPyQt                    # provided by kroot/kui/kPyQt
from PyQt5 import uic, QtWidgets, QtCore, QtGui

from kpf.OB_GUI import above_horizon, near_horizon
from kpf.OB_GUI.GUIcomponents import (OBListModel, ConfirmationPopup, InputPopup,
                                      OBContentsDisplay, EditableMessageBox,
                                      ObserverCommentBox, SelectProgramPopup,
                                      launch_command_in_xterm)
from kpf.ObservingBlocks.Target import Target
from kpf.ObservingBlocks.Calibration import Calibration
from kpf.ObservingBlocks.Observation import Observation
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.ObservingBlocks.GetObservingBlocks import GetObservingBlocks, GetObservingBlocksByProgram
from kpf.ObservingBlocks.SubmitObserverComment import SubmitObserverComment
from kpf.scripts.EstimateOBDuration import EstimateOBDuration
from kpf.spectrograph.QueryFastReadMode import QueryFastReadMode
from kpf.spectrograph.SetObserver import SetObserver
from kpf.spectrograph.SetProgram import SetProgram
from kpf.magiq.RemoveTarget import RemoveTarget, RemoveAllTargets
from kpf.magiq.AddTarget import AddTarget
from kpf.magiq.SelectTarget import SelectTarget
from kpf.magiq.SetTargetList import SetTargetList
from kpf.utils.StartOfNight import StartOfNight
from kpf.utils.EndOfNight import EndOfNight
from kpf.schedule import get_semester_dates
from kpf.schedule.GetScheduledPrograms import GetScheduledPrograms
from kpf.fiu.ConfigureFIU import ConfigureFIU


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
logging.addLevelName(25, 'SCHEDULE')

def schedule(self, message, *args, **kwargs):
    if self.isEnabledFor(25):
        self._log(25, message, args, **kwargs)

logging.Logger.schedule = schedule


def create_GUI_log():
    guilog = logging.getLogger('KPF_OB_GUI')
    guilog.setLevel(logging.DEBUG)
    ## Set up console output
    LogConsoleHandler = logging.StreamHandler()
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
## Define Application MainWindow
##-------------------------------------------------------------------------
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
        ui_file = Path(__file__).parent / 'KPF_OB_GUI.ui'
        uic.loadUi(f"{ui_file}", self)
        self.log = guilog
        self.pid = os.getpid()
        self.log.info(f'Initializing OB GUI. PID={self.pid}')
        self.file_path = Path('/s/sdata1701/OBs')
        self.log.debug('Initializing MainWindow')
        self.KPFCC = False
        self.SciObservingBlock = None
        self.CalObservingBlock = None
        self.BuildTarget = Target({})
        self.BuildObservation = [Observation({})]
        self.BuildCalibration = [Calibration({})]
        # Example Calibrations
        self.example_cal_file = Path(__file__).parent.parent / 'ObservingBlocks' / 'exampleOBs' / 'Calibrations.yaml'
        if self.example_cal_file.exists():
            self.example_calOB = ObservingBlock(self.example_cal_file)
        else:
            self.example_calOB = ObservingBlock({})
        # Keywords
        self.dcs = 'dcs1'
        self.log.debug('Cacheing keyword services')
        self.DCS_AZ = ktl.cache(self.dcs, 'AZ')
        self.DCS_AZ.monitor()
        self.DCS_EL = ktl.cache(self.dcs, 'EL')
        self.DCS_EL.monitor()
        self.kpfconfig = ktl.cache('kpfconfig')
        self.EXPOSE = kPyQt.kFactory(ktl.cache('kpfexpose', 'EXPOSE'))
        self.ELAPSED = kPyQt.kFactory(ktl.cache('kpfexpose', 'ELAPSED'))
        self.EXPOSURE = kPyQt.kFactory(ktl.cache('kpfexpose', 'EXPOSURE'))
        self.READOUTPCT_G = kPyQt.kFactory(ktl.cache('kpfgreen', 'READOUTPCT'))
        self.READOUTPCT_R = kPyQt.kFactory(ktl.cache('kpfred', 'READOUTPCT'))
        self.SLEWCALREQ = kPyQt.kFactory(ktl.cache('kpfconfig', 'SLEWCALREQ'))
        self.red_acf_file_kw = kPyQt.kFactory(ktl.cache('kpfred', 'ACFFILE'))
        self.green_acf_file_kw = kPyQt.kFactory(ktl.cache('kpfgreen', 'ACFFILE'))
        self.PROGNAME = kPyQt.kFactory(ktl.cache('kpfexpose', 'PROGNAME'))
        # Selected OB
        self.SOBindex = None
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
        self.enable_telescope = False
        self.enable_magiq = False
        # Get KPF Programs on schedule
        classical, cadence = GetScheduledPrograms.execute({'semester': 'current'})
        program_IDs = list(set([f"{p['ProjCode']}" for p in classical]))
        self.program_strings = []
        for progID in sorted(program_IDs):
            dates = [e['Date'] for e in classical if e['ProjCode'] == progID]
            self.program_strings.append(f"{progID} on {', '.join(dates)}")
        # Prepare KPFCC schedule execution records
        semester, start, end = get_semester_dates(datetime.datetime.now())
        logdir = Path(f'/s/sdata1701/KPFTranslator_logs/')
        execution_history_file = logdir / f'KPFCC_executions_{semester}.csv'
        if execution_history_file.exists() is False:
            with open(execution_history_file, 'w') as f:
                contents = ['# timestamp', 'decimalUT', 'executedID',
                            'executed_line', 'scheduleUT',
                            'schedule_current_line', 'scheduleUT_current',
                            'schedule_next_line', 'scheduleUT_next',
                            'on_schedule']
                hdrline = ', '.join(contents)
                f.write(hdrline)
        # KPF-CC Settings and Values
        self.schedule_path = Path(f'/s/sdata1701/Schedules/')
        self.default_schedule = self.schedule_path / 'default.json'
        self.KPFCC_weather_bands = [1, 2, 3]
        self.KPFCC_weather_band = 1
        self.KPFCC_OBs = {}
        self.KPFCC_start_times = {}


    def setupUi(self):
        self.log.debug('setupUi')
        self.setWindowTitle("KPF OB GUI")

        #-------------------------------------------------------------------
        # Menu Bar: File
        ActionExit = self.findChild(QtWidgets.QAction, 'actionExit')
        ActionExit.triggered.connect(self.exit)

        #-------------------------------------------------------------------
        # Menu Bar: Load OBs
        LoadOBsFromProgram = self.findChild(QtWidgets.QAction, 'action_LoadOBsFromProgram')
        LoadOBsFromProgram.triggered.connect(self.load_OBs_from_program)
        LoadOBFromFile = self.findChild(QtWidgets.QAction, 'action_LoadOBFromFile')
        LoadOBFromFile.triggered.connect(self.load_OB_from_file)
        LoadKPFCCSchedule = self.findChild(QtWidgets.QAction, 'actionLoad_KPF_CC_Schedule')
        LoadKPFCCSchedule.triggered.connect(self.load_KPFCC_schedule)
        LoadOBsFromKPFCC = self.findChild(QtWidgets.QAction, 'actionLoad_KPF_CC_OBs')
        LoadOBsFromKPFCC.triggered.connect(self.load_OBs_from_KPFCC)

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
        # Menu Bar: FIU
        self.ConfigureFIU_Observing = self.findChild(QtWidgets.QAction, 'actionConfigure_FIU_for_Observing')
        self.ConfigureFIU_Observing.triggered.connect(self.configure_FIU_observing)
        self.ConfigureFIU_Calibrations = self.findChild(QtWidgets.QAction, 'actionConfigure_FIU_for_Calibrations')
        self.ConfigureFIU_Calibrations.triggered.connect(self.configure_FIU_calibrations)
        self.ConfigureFIU_Stow = self.findChild(QtWidgets.QAction, 'actionConfigure_FIU_to_Stow_Position')
        self.ConfigureFIU_Stow.triggered.connect(self.configure_FIU_stow)

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
        INSTRUME = kPyQt.kFactory(ktl.cache(self.dcs, 'INSTRUME'))
        INSTRUME.stringCallback.connect(self.update_selected_instrument)
        INSTRUME.primeCallback()

        # script name
        self.scriptname_value = self.findChild(QtWidgets.QLabel, 'scriptname_value')
        scriptname_kw = kPyQt.kFactory(ktl.cache('kpfconfig', 'SCRIPTNAME'))
        scriptname_kw.stringCallback.connect(self.update_scriptname_value)

        # script stop
        self.scriptstop_value = self.findChild(QtWidgets.QLabel, 'scriptstop_value')
        self.SCRIPTSTOP = kPyQt.kFactory(ktl.cache('kpfconfig', 'SCRIPTSTOP'))
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
        object_kw = kPyQt.kFactory(ktl.cache('kpfexpose', 'OBJECT'))
        object_kw.stringCallback.connect(self.ObjectValue.setText)

        # lamps
        self.LampsValue = self.findChild(QtWidgets.QLabel, 'LampsValue')
        lamps_kw = kPyQt.kFactory(ktl.cache('kpflamps', 'LAMPS'))
        lamps_kw.stringCallback.connect(self.LampsValue.setText)

        # time since last cal
        self.slewcaltime_value = self.findChild(QtWidgets.QLabel, 'slewcaltime_value')
        slewcaltime_kw = kPyQt.kFactory(self.kpfconfig['SLEWCALTIME'])
        slewcaltime_kw.stringCallback.connect(self.update_slewcaltime_value)

        # readout mode
        self.read_mode = self.findChild(QtWidgets.QLabel, 'readout_mode_value')
        self.red_acf_file_kw.stringCallback.connect(self.update_acffile)
        self.green_acf_file_kw.stringCallback.connect(self.update_acffile)

        # disabled detectors
        self.disabled_detectors_value = self.findChild(QtWidgets.QLabel, 'disabled_detectors_value')
        self.disabled_detectors_value.setText('')
        cahk_enabled_kw = kPyQt.kFactory(self.kpfconfig['CA_HK_ENABLED'])
        cahk_enabled_kw.stringCallback.connect(self.update_ca_hk_enabled)
        green_enabled_kw = kPyQt.kFactory(self.kpfconfig['GREEN_ENABLED'])
        green_enabled_kw.stringCallback.connect(self.update_green_enabled)
        red_enabled_kw = kPyQt.kFactory(self.kpfconfig['RED_ENABLED'])
        red_enabled_kw.stringCallback.connect(self.update_red_enabled)
        expmeter_enabled_kw = kPyQt.kFactory(self.kpfconfig['EXPMETER_ENABLED'])
        expmeter_enabled_kw.stringCallback.connect(self.update_expmeter_enabled)

        # Universal Time
        self.UTValue = self.findChild(QtWidgets.QLabel, 'UTValue')
        UT_kw = kPyQt.kFactory(ktl.cache(self.dcs, 'UT'))
        UT_kw.stringCallback.connect(self.update_UT)

        # Sidereal Time
        self.SiderealTimeValue = self.findChild(QtWidgets.QLabel, 'SiderealTimeValue')
        LST_kw = kPyQt.kFactory(ktl.cache(self.dcs, 'LST'))
        LST_kw.stringCallback.connect(self.update_LST)

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

        self.ListOfOBs = self.findChild(QtWidgets.QListView, 'ListOfOBs')
        self.model = OBListModel(OBs=[])
        self.ListOfOBs.setModel(self.model)
        self.ListOfOBs.selectionModel().selectionChanged.connect(self.select_OB_from_GUI)

        # Selected Observing Block Details
        self.SOB_TargetName = self.findChild(QtWidgets.QLabel, 'SOB_TargetName')
        self.SOB_GaiaID = self.findChild(QtWidgets.QLabel, 'SOB_GaiaID')
        self.SOB_TargetRA = self.findChild(QtWidgets.QLabel, 'SOB_TargetRA')
        self.SOB_TargetRALabel = self.findChild(QtWidgets.QLabel, 'TargetRALabel')
        self.SOB_TargetDec = self.findChild(QtWidgets.QLabel, 'SOB_TargetDec')
        self.SOB_TargetDecLabel = self.findChild(QtWidgets.QLabel, 'TargetDecLabel')
        self.SOB_Jmag = self.findChild(QtWidgets.QLabel, 'SOB_Jmag')
        self.SOB_Gmag = self.findChild(QtWidgets.QLabel, 'SOB_Gmag')
        self.SOB_Observation1 = self.findChild(QtWidgets.QLabel, 'SOB_Observation1')
        self.SOB_Observation2 = self.findChild(QtWidgets.QLabel, 'SOB_Observation2')
        self.SOB_Observation3 = self.findChild(QtWidgets.QLabel, 'SOB_Observation3')

        # Calculated Values
        self.SOB_ExecutionTime = self.findChild(QtWidgets.QLabel, 'SOB_ExecutionTime')
        self.SOB_EL = self.findChild(QtWidgets.QLabel, 'SOB_EL')
        self.SOB_Az = self.findChild(QtWidgets.QLabel, 'SOB_Az')
        self.SOB_Airmass = self.findChild(QtWidgets.QLabel, 'SOB_Airmass')
        self.SOB_AzSlew = self.findChild(QtWidgets.QLabel, 'SOB_AzSlew')
        self.SOB_ELSlew = self.findChild(QtWidgets.QLabel, 'SOB_ELSlew')

        # SOB Execution
        self.SOB_CommentToObserver = self.findChild(QtWidgets.QLabel, 'CommentToObserver')
        self.SOB_CommentToObserverLabel = self.findChild(QtWidgets.QLabel, 'CommentToObserverLabel')
        self.SOB_ShowButton = self.findChild(QtWidgets.QPushButton, 'SOB_ShowButton')
        self.SOB_ShowButton.clicked.connect(self.show_SOB)
        self.SOB_AddComment = self.findChild(QtWidgets.QPushButton, 'SOB_AddComment')
        self.SOB_AddComment.clicked.connect(self.add_comment)
        self.SOB_ExecuteButton = self.findChild(QtWidgets.QPushButton, 'SOB_ExecuteButton')
        self.SOB_ExecuteButton.clicked.connect(self.execute_SOB)
        self.SOB_RemoveFromList = self.findChild(QtWidgets.QPushButton, 'SOB_RemoveFromList')
        self.SOB_RemoveFromList.clicked.connect(self.remove_SOB)
        self.SlewCal = self.findChild(QtWidgets.QCheckBox, 'SlewCal')
        self.SlewCal.stateChanged.connect(self.SlewCal_state_change)
        self.SLEWCALREQ.stringCallback.connect(self.update_SlewCalReq)
        self.update_SOB_display()

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


    ##-------------------------------------------
    ## Methods to display updates from keywords
    ##-------------------------------------------
    # SCRIPTSTOP
    def update_scriptstop_value(self, value):
        '''Set label text and set color'''
        self.log.debug(f'update_scriptstop_value: {value}')
        self.scriptstop_value.setText(f"{value}")
        if value == 'Yes':
            self.scriptstop_value.setStyleSheet("color:red")
            self.scriptstop_btn.setText('CLEAR STOP')
            msg = 'Disabled because STOP has been requested.'
            self.SOB_ExecuteButton.setEnabled(False)
            self.SOB_ExecuteButton.setToolTip(msg)
        elif value == 'No':
            self.scriptstop_value.setStyleSheet("color:green")
            self.scriptstop_btn.setText('Request Script STOP')
            self.SOB_ExecuteButton.setEnabled(self.SOBindex is not None)
            self.SOB_ExecuteButton.setToolTip('')

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


    # Script Name
    def update_scriptname_value(self, value):
        '''Set label text and set color'''
        scriptname_string = value.replace('.py', '')
        self.log.debug(f"update_scriptname_value: {scriptname_string}")
        self.scriptname_value.setText(f"{scriptname_string}")
        if value in ['None', '']:
            self.scriptname_value.setStyleSheet("color:green")
            self.ConfigureFIU_Observing.setEnabled(True)
            self.ConfigureFIU_Calibrations.setEnabled(True)
            self.ConfigureFIU_Stow.setEnabled(True)
        else:
            self.scriptname_value.setStyleSheet("color:orange")
            self.ConfigureFIU_Observing.setEnabled(False)
            self.ConfigureFIU_Calibrations.setEnabled(False)
            self.ConfigureFIU_Stow.setEnabled(False)

    # Expose Status
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
            self.RunStartOfNight.setEnabled(self.SelectedInstrument.text() != 'OSIRIS')
            self.SetObserverNames.setEnabled(True)
            self.SetProgramID.setEnabled(True)
            self.RunEndOfNight.setEnabled(self.SelectedInstrument.text() != 'OSIRIS')
        elif status in ['Start', 'InProgress', 'Readout']:
            self.expose_status_value.setStyleSheet("color:orange")
            self.RunStartOfNight.setEnabled(False)
            self.SetObserverNames.setEnabled(False)
            self.SetProgramID.setEnabled(False)
            self.RunEndOfNight.setEnabled(False)

    def update_selected_instrument(self, value):
        self.SelectedInstrument.setText(value)
        if value in ['KPF', 'KPF-CC']:
            self.SelectedInstrument.setStyleSheet("color:green")
            self.SelectedInstrument.setToolTip('')
            self.enable_telescope = True
        else:
            self.SelectedInstrument.setStyleSheet("color:red")
            self.SelectedInstrument.setToolTip('Telescope moves and Magiq integration disabled')
            self.enable_telescope = False

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

    def update_acffile(self, value):
        self.fast = QueryFastReadMode.execute({})
        if self.fast is True:
            self.read_mode.setText('Fast')
            self.read_mode.setStyleSheet("color:orange")
        else:
            self.read_mode.setText('Normal')
            self.read_mode.setStyleSheet("color:green")

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

    def update_UT(self, value):
        self.UTValue.setText(value[:-3])

    def update_LST(self, value):
        self.SiderealTimeValue.setText(value[:-3])
        self.update_counter += 1
        if self.update_counter > 60:
            self.update_SOB_display()

    def update_SlewCalReq(self, value):
        self.log.debug(f"update_SlewCalReq: {value} {(value == 'Yes')}")
        if self.SlewCal.isChecked() != (value == 'Yes'):
            self.SlewCal.setChecked((value == 'Yes'))

    def SlewCal_state_change(self, value):
        self.log.debug(f"SlewCal_state_change: {value} {(value == 2)}")
        if (self.SLEWCALREQ.read() == 'Yes') != (value == 2):
            self.log.info(f'Modifying kpfconfig.SLEWCALREQ = {(value == 2)}')
            self.kpfconfig['SLEWCALREQ'].write((value == 2))

    ##-------------------------------------------
    ## Methods to get data from DB or Schedule
    ##-------------------------------------------
    def load_OB_from_file(self):
        self.log.debug(f"load_OBs_from_files")
        files, filefilter = QtWidgets.QFileDialog.getOpenFileNames(self, 
                                       'Open Files', f"{self.file_path}",
                                       "OB Files (*yaml);;All Files (*)")
        if files:
            for file in files:
                file = Path(file)
                if file.exists():
                    print(f"Opening: {str(file)}")
                    newOB = ObservingBlock(file)
                    if newOB.validate() == True:
                        self.model.OBs.append(newOB)
            self.model.layoutChanged.emit()
            self.set_SortOrWeather()

    def set_SortOrWeather(self):
        if self.KPFCC == True:
            self.SortOrWeatherLabel.setText('Weather Band:')
            self.SortOrWeatherLabel.setEnabled(True)
            self.SortOrWeather.clear()
            self.SortOrWeather.addItems([str(w) for w in self.KPFCC_weather_bands])
            self.SortOrWeather.currentTextChanged.connect(self.set_weather_band)
            self.SortOrWeather.setEnabled(True)
        else:
            self.SortOrWeatherLabel.setText('Sort List By:')
            self.SortOrWeatherLabel.setEnabled(True)
            self.SortOrWeather.clear()
            self.SortOrWeather.addItems(['', 'Name', 'RA', 'Dec', 'Gmag', 'Jmag'])
            self.SortOrWeather.currentTextChanged.connect(self.sort_OB_list)
            self.SortOrWeather.setEnabled(True)

    def verify_overwrite_of_OB_list(self):
        if len(self.model.OBs) == 0:
            return True
        else:
            msg = 'Loading OBs from a new program will clear the current list of OBs. Continue?'
            result = ConfirmationPopup('Overwrite OB List?', msg).exec_()
            if result == QtWidgets.QMessageBox.Yes:
                self.log.debug('Confirmed overwrite')
                return True
            else:
                self.log.debug("Cancel! Not overwriting OB list.")
                return False

    def load_OBs_from_KPFCC(self):
        if self.verify_overwrite_of_OB_list():
            self.load_OBs('KPF-CC')

    def load_OBs_from_program(self):
        if self.verify_overwrite_of_OB_list():
            select_program_popup = SelectProgramPopup(self.program_strings)
            if select_program_popup.exec():
                self.load_OBs(select_program_popup.ProgID)
            else:
                self.log.debug("Cancel! Not pulling OBs from database.")

    def load_KPFCC_schedule(self):
        if self.verify_overwrite_of_OB_list():
            self.KPFCC = True
            self.set_SortOrWeather()
            utnow = datetime.datetime.utcnow()
            date = utnow-datetime.timedelta(days=1)
            date_str = date.strftime('%Y%b%d').lower()
            schedule_files = [self.schedule_path / f'{date_str}_w{w}.json' for w in [1, 2, 3]]
            # Count what we need to load ahead of time for the progress bar
            contents = []
            for i,WB in enumerate([1,2,3]):
                if schedule_files[i].exists():
                    with open(schedule_files[i], 'r') as f:
                        contents += json.loads(f.read())
            Nsched = len(contents)
            print(f"Pre-counted {Nsched} OBs to get for KPF-CC in all weather bands")
            usepbar = Nsched > 15 # Create progress bar if we have a lot of OBs to retrieve
            if usepbar:
                progress = QtWidgets.QProgressDialog("Retrieving OBs from Database", "Cancel", 0, Nsched)
                progress.setWindowModality(QtCore.Qt.WindowModal) # Make it modal (blocks interaction with parent)
                progress.setAutoClose(True) # Dialog closes automatically when value reaches maximum
                progress.setAutoReset(True) # Dialog resets automatically when value reaches maximum

            OBcount = 0
            errmsg = []
            for i,WB in enumerate([1,2,3]):
                self.KPFCC_OBs[WB] = []
                self.KPFCC_start_times[WB] = []
                if schedule_files[i].exists():
                    with open(schedule_files[i], 'r') as f:
                        contents = json.loads(f.read())
                else:
                    self.log.error(f'No schedule file found at {schedule_files[i]}')
                    errmsg.append(f'No schedule file found at {schedule_files[i]}')
                    contents = []
                for entry in contents:
                    OBcount += 1
                    try:
                        thisOB = GetObservingBlocks.execute({'OBid': entry['id']})[0]
                        self.KPFCC_OBs[WB].append(thisOB)
                        start = entry['start_exp'].split(':')
                        start_decimal = int(start[0]) + int(start[1])/60
                        self.KPFCC_start_times[WB].append(start_decimal)
                    except Exception as e:
                        self.log.error(f'Unable to load OB: {entry["id"]}')
                        self.log.error(e)
                    if usepbar:
                        if progress.wasCanceled():
                            self.log.error("Retrieval of OBs canceled by user.")
                            break
                        progress.setValue(OBcount+1)
                self.log.info(f"Retrieved {len(self.KPFCC_OBs[WB])} for weather band {WB}")
            msg = [f"Retrieved {OBcount} (out of {Nsched}) KPF-CC OBs for all weather bands"]
            msg.extend(errmsg)
            msg = '\n'.join(msg)
            ConfirmationPopup('Retrieved OBs from Database', msg, info_only=True).exec_()
            self.set_weather_band(self.KPFCC_weather_band)

    def load_OBs(self, value):
        self.log.info(f"load_OBs: '{value}'")
        self.clear_OB_selection()
        self.KPFCC = False
        self.OBListHeader.setText(self.hdr)
        if value == '':
            self.model.OBs = []
            self.model.start_times = None
            self.model.layoutChanged.emit()
            self.set_SortOrWeather()
        elif value == 'KPF-CC':
            self.KPFCC = True
            classical, cadence = GetScheduledPrograms.execute({'semester': 'current'})
            progIDs = set([p['ProjCode'] for p in cadence])
            self.model.OBs = []
            usepbar = len(progIDs) > 5 # Create progress bar if we have a lot of programs to query
            if usepbar:
                progress = QtWidgets.QProgressDialog("Retrieving OBs from Database", "Cancel", 0, len(progIDs))
                progress.setWindowModality(QtCore.Qt.WindowModal) # Make it modal (blocks interaction with parent)
                progress.setAutoClose(True) # Dialog closes automatically when value reaches maximum
                progress.setAutoReset(True) # Dialog resets automatically when value reaches maximum
            for i,progID in enumerate(progIDs):
                self.log.debug(f'Retrieving OBs for {progID}')
                programOBs = GetObservingBlocksByProgram.execute({'program': progID})
                self.model.OBs.extend(programOBs)
                self.log.debug(f'  Got {len(programOBs)} for {progID}, total KPF-CC OB count is now {len(self.model.OBs)}')
                if usepbar:
                    if progress.wasCanceled():
                        self.log.error("Retrieval of OBs canceled by user.")
                        break
                    progress.setValue(i+1)
            self.OBListHeader.setText('    StartTime '+self.hdr)
            self.model.layoutChanged.emit()
            self.set_SortOrWeather()
        else:
            OBs = GetObservingBlocksByProgram.execute({'program': value})
            self.model.OBs = OBs
            self.model.start_times = None
            self.model.layoutChanged.emit()
            self.set_SortOrWeather()
            msg = f"Retrieved {len(OBs)} OBs for program {value}"
            ConfirmationPopup('Retrieved OBs from Database', msg, info_only=True).exec_()
        # This select/deselect operation caches something in the AltAz 
        # calculation which happens the first time an OB is selected. This
        # just makes the GUI more "responsive" as the loading of the OBs when
        # program ID is chosen contains all of the slow caching of values
        # instead of having it happen on the first click.
        if len(self.model.OBs) > 0:
            self.select_OB(0)
            self.select_OB(None)
        self.update_star_list()

    def update_star_list(self):
        star_list = [OB.Target.to_star_list() for OB in self.model.OBs
                     if OB.Target is not None]
        print('\n'.join(star_list))
        if self.enable_telescope and self.enable_magiq:
            RemoveAllTargets.execute({})
            SetTargetList.execute({'StarList': '\n'.join(star_list)})

    def set_weather_band(self, value):
        self.log.info(f"Setting Weather Band '{value}'")
        self.SortOrWeather.setCurrentText(str(value))
        try:
            WB = int(value)
            assert WB in [1, 2, 3]
            self.KPFCC_weather_band = WB
            self.model.OBs = self.KPFCC_OBs[WB]
            self.model.start_times = self.KPFCC_start_times[WB]
            self.model.sort('time')
            self.OBListHeader.setText('    StartTime '+self.hdr)
            self.model.layoutChanged.emit()
            # This select/deselect operation caches something in the AltAz 
            # calculation which happens the first time an OB is selected. This
            # just makes the GUI more "responsive" as the loading of the OBs when
            # program ID is chosen contains all of the slow caching of values
            # instead of having it happen on the first click.
            if len(self.model.OBs) > 0:
                self.select_OB(0)
                self.select_OB(None)
            self.update_star_list()
        except:
            self.log.warning(f'set_weather_band got "{value}" ({type(value)})')

    ##-------------------------------------------
    ## Methods for Observing Menu
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
            stdout, stderr = launch_command_in_xterm('StartOfNight')
            for line in stdout.split('\n'):
                self.log.debug(f'STDOUT: {line}')
            for line in stderr.split('\n'):
                self.log.debug(f'STDERR: {line}')
        else:
            self.log.debug('Confirmation is no, not running script')

    def configure_FIU(self, mode):
        if mode not in ['Stowed', 'Alignment', 'Acquisition', 'Observing', 'Calibration']:
            self.log.error(f"Desired FIU mode {mode} is not allowed")
            return
        stdout, stderr = launch_command_in_xterm(f'ConfigureFIU {mode}')
        for line in stdout.split('\n'):
            self.log.debug(f'STDOUT: {line}')
        for line in stderr.split('\n'):
            self.log.debug(f'STDERR: {line}')

    def configure_FIU_observing(self):
        self.log.info('running configure_FIU_observing')
        self.configure_FIU('Observing')

    def configure_FIU_calibrations(self):
        self.log.info('running configure_FIU_calibrations')
        self.configure_FIU('Calibration')

    def configure_FIU_stow(self):
        self.log.info('running configure_FIU_stow')
        self.configure_FIU('Stowed')

    def set_observer(self):
        self.log.debug(f"action set_observer")
        observer_input = InputPopup('Set observer names', 'Observer names:')
        if observer_input.exec_():
            if self.EXPOSE.ktl_keyword.ascii == 'Ready':
                SetObserver.execute({'observer': observer_input.result.strip()})
            else:
                msg = 'Unable to set observer while exposure is in progress'
                ConfirmationPopup('Unable to set observer', msg, info_only=True, warning=True).exec_()

    def set_programID(self):
        self.log.debug(f"action set_programID")
        program_input = InputPopup('Set program ID', 'Program ID:')
        if program_input.exec_():
            if self.EXPOSE.ktl_keyword.ascii == 'Ready':
                SetProgram.execute({'progname': program_input.result.strip()})
            else:
                msg = 'Unable to set program while exposure is in progress'
                ConfirmationPopup('Unable to set program', msg, info_only=True, warning=True).exec_()

    def run_end_of_night(self):
        self.log.debug(f"action run_end_of_night")
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
            stdout, stderr = launch_command_in_xterm(f'EndOfNight')
            for line in stdout.split('\n'):
                self.log.debug(f'STDOUT: {line}')
            for line in stderr.split('\n'):
                self.log.debug(f'STDERR: {line}')
        else:
            self.log.debug('Confirmation is no, not running script')


    ##-------------------------------------------
    ## Methods for OB List
    ##-------------------------------------------
    def select_OB_from_GUI(self, selected, deselected):
        if len(selected.indexes()) > 0:
            ind = selected.indexes()[0].row()
            self.select_OB(ind)
        else:
            self.SOBindex = None
            self.update_SOB_display()

    def select_OB(self, ind):
        self.SOBindex = ind
        self.log.debug(f"Selection changed to {self.SOBindex}")
        self.update_SOB_display()

    def set_SOB_enabled(self, enabled):
        if enabled == False:
            self.SOB_CommentToObserver.setText('')
        self.SOB_CommentToObserverLabel.setEnabled(enabled)
        self.SOB_ShowButton.setEnabled(enabled)
        # Only enable observer comment if we have a database ID
        if self.SOBindex is None or self.SOBindex < 0:
            OBID_exists = False
        else:
            SOB = self.model.OBs[self.SOBindex]
            OBID_exists = SOB.OBID not in ['', None]
        if OBID_exists:
            self.SOB_AddComment.setToolTip('')
        else:
            no_comment_msg = 'Can not submit comment without database ID'
            self.SOB_AddComment.setToolTip(no_comment_msg)
        self.SOB_AddComment.setEnabled(enabled and OBID_exists)
        self.SOB_ExecuteButton.setEnabled(enabled)
        self.SOB_RemoveFromList.setEnabled(enabled)

    def clear_SOB_Target(self):
        self.SOB_TargetName.setText('--')
        self.SOB_GaiaID.setText('--')
        self.SOB_TargetRA.setText('--')
        self.SOB_TargetDec.setText('--')
        self.SOB_Jmag.setText('--')
        self.SOB_Gmag.setText('--')
        self.SOB_EL.setText('--')
        self.SOB_EL.setStyleSheet("color:black")
        self.SOB_EL.setToolTip("")
        self.SOB_Az.setText('--')
        self.SOB_Airmass.setText('--')
        self.SOB_AzSlew.setText('--')
        self.SOB_ELSlew.setText('--')
        self.SOBobservable = False
        self.SOB_ExecuteButton.setEnabled(self.SOBobservable)

    def set_SOB_Target(self, SOB):
        self.clear_SOB_Target()
        self.SOB_TargetName.setText(SOB.Target.get('TargetName'))
        self.SOB_GaiaID.setText(SOB.Target.get('GaiaID'))
        self.SOB_Jmag.setText(f"{SOB.Target.get('Jmag'):.2f}")
        self.SOB_Gmag.setText(f"{SOB.Target.get('Gmag'):.2f}")
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
            self.SOB_EL.setText(f"{target_altz.alt.deg:.1f} deg")
            self.SOB_Az.setText(f"{target_altz.az.deg:.1f} deg")
            self.SOBobservable = above_horizon(target_altz.az.deg, target_altz.alt.deg)
            self.SOB_ExecuteButton.setEnabled(self.SOBobservable)
            if self.SOBobservable:
                self.SOB_Airmass.setText(f"{target_altz.secz:.2f}")
                if target_altz.alt.deg > self.ADC_horizon:
                    self.SOB_EL.setStyleSheet("color:black")
                    self.SOB_EL.setToolTip("")
                else:
                    self.SOB_EL.setStyleSheet("color:orange")
                    self.SOB_EL.setToolTip(f"ADC correction is poor below EL~{self.ADC_horizon:.0f}")
            else:
                self.SOB_Airmass.setText("--")
                self.SOB_EL.setStyleSheet("color:red")
                self.SOB_EL.setToolTip("Below Keck horizon")
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
        self.update_counter = 0
        if self.SOBindex is None:
            self.set_SOB_enabled(False)
            self.clear_SOB_Target()
            self.SOB_Observation1.setText('--')
            self.SOB_Observation2.setText('--')
            self.SOB_Observation3.setText('--')
            self.SOB_ExecutionTime.setText('--')
            self.SOB_CommentToObserver.setText('')
            self.SOB_CommentToObserver.setToolTip('')
        else:
            SOB = self.model.OBs[self.SOBindex]
            self.SOB_CommentToObserver.setText(SOB.CommentToObserver)
            self.SOB_CommentToObserver.setToolTip(SOB.CommentToObserver)
            self.set_SOB_enabled(True)
            # Handle Target component
            if SOB.Target is None:
                self.clear_SOB_Target()
                self.SOBobservable = True
                self.SOB_ExecuteButton.setEnabled(self.SOBobservable)
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
            self.SOB_ExecutionTime.setText(f"{duration/60:.0f} min")

    def sort_OB_list(self, value):
        self.model.sort(value)
        self.model.layoutChanged.emit()
        self.clear_OB_selection()

    def clear_OB_selection(self):
        self.ListOfOBs.selectionModel().clearSelection()
        self.SOBindex = None
        self.update_SOB_display()


    ##-------------------------------------------
    ## Methods operating on a single OB
    ##-------------------------------------------
    def show_SOB(self):
        if self.SOBindex is None:
            return
        SOB = self.model.OBs[self.SOBindex]
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
                    self.model.OBs[self.SOBindex] = OBedit_popup.result
                    self.model.layoutChanged.emit()
                    self.update_SOB_display()
                else:
                    self.log.warning('Edits did not validate. Not changing OB.')
            elif edit_result == QtWidgets.QMessageBox.Cancel:
                self.log.debug('Edit popup: Cancel')


    def add_comment(self):
        if self.SOBindex is None:
            print('add_comment: No OB selected')
            return
        SOB = self.model.OBs[self.SOBindex]
        comment_box = ObserverCommentBox(SOB, self.Observer.text())
        if comment_box.exec():
            print(f"Submitting comment: {comment_box.comment}")
            print(f"From commentor: {comment_box.observer}")
            params = {'OBid': SOB.OBID,
                      'observer': comment_box.observer,
                      'comment': comment_box.comment,
                      }
            SubmitObserverComment.execute(params)
        else:
            print("Cancel! Not submitting comment.")


    def execute_SOB(self):
        SOB = self.model.OBs[self.SOBindex]
        if SOB is not None:
            self.log.debug(f"execute_SOB")
            msg = ["Do you really want to execute the current OB?", '',
                   f"{SOB.summary()}"]
            result = ConfirmationPopup('Execute Science OB?', msg).exec_()
            if result == QtWidgets.QMessageBox.Yes:
                if self.KPFCC == True:
                    # Log execution
                    now = datetime.datetime.utcnow()
                    now_str = now.strftime('%Y-%m-%d %H:%M:%S UT')
                    decimal_now = now.hour + now.minute/60 + now.second/3600
                    start_time = self.model.start_time[self.SOBindex]
                    start_current = self.model.start_time[self.model.CurrentOB]
                    start_next = self.model.start_time[self.model.NextOB]
                    on_schedule = self.SOBindex in [self.model.CurrentOB, self.model.NextOB]
                    contents = [now_str, f'{decimal_now:.2f}', f'{SOB.OBID}',
                                f'{self.SOBindex}', f'{start_time:.2f}',
                                f'{self.model.CurrentOB}', f'{start_current:.2f}',
                                f'{self.model.NextOB}', f'{start_next:.2f}',
                                f'{on_schedule}']
                    line = ', '.join(contents)
                    if not on_schedule:
                        self.log.schedule(f'Running OB {self.SOBindex} off schedule')
                        self.log.schedule(f'  Start time for this OB is {start_time:.2f} UT')
                        self.log.schedule(f'  Start time for scheduled OB is {start_current:.2f} UT')
                        self.log.schedule(f'  Start time for next OB is {start_next:.2f} UT')
                self.RunOB(SOB)
                self.model.OBs[self.SOBindex].executed = True
                self.model.layoutChanged.emit()
            else:
                self.log.debug('User opted not to execute OB')


    def RunOB(self, SOB):
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
        tmp_file = tmp_file_path / f'test_executedOB_{now_str}.yaml'
        SOB.write_to(tmp_file)
        stdout, stderr = launch_command_in_xterm(f'RunOB -f {tmp_file}')
        for line in stdout.split('\n'):
            self.log.debug(f'STDOUT: {line}')
        for line in stderr.split('\n'):
            self.log.debug(f'STDERR: {line}')

    def remove_SOB(self):
        removed = self.model.OBs.pop(self.SOBindex)
        self.clear_OB_selection()
        self.model.layoutChanged.emit()
        if removed.Target is not None:
            targetname = removed.Target.TargetName
            self.log.info(f"Removing {targetname} from star list and OB list")
            if self.enable_telescope and self.enable_magiq:
                RemoveTarget.execute({'target': targetname})


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
                print(f'Failed to set cursor position in {view}')
                print(e)
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
                print(f'Failed to parse edited {input_class_name} text')
                print(e)
                print(f'Not changing contents')


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
        print(f"Querying: {target_name}")
        newtarg = self.BuildTarget.resolve_name(target_name)
        if newtarg is None:
            print(f"Query failed for {target_name}")
        self.QuerySimbadLineEdit.setText('')
        print(newtarg.__repr__())
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
            print('newOB and existing OB match')
#             print(newOB.__repr__())
#             print()
#             print(self.SciObservingBlock.__repr__())
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
            duration = EstimateOBDuration.execute({'fast': self.fast}, OB=self.SciObservingBlock)
            self.SciOBEstimatedDuration.setText(f"{duration/60:.0f} min")
        else:
            self.SciOBString.setText('')
            self.SciOBEstimatedDuration.setText('')

    def send_SciOB_to_list(self):
        if self.SciObservingBlock.validate() != True:
            print('OB is invalid, not sending to OB list')
        elif self.KPFCC == False:
            self.model.OBs.append(self.SciObservingBlock)
            self.model.layoutChanged.emit()
        elif self.KPFCC == True:
            self.model.OBs.append(self.SciObservingBlock)
            self.model.start_times.append(24)
            self.model.sort('time')
            self.model.layoutChanged.emit()
            self.set_SortOrWeather()
        targetname = self.SciObservingBlock.Target.TargetName
        self.log.info(f"Adding {targetname} to star list and OB list")
        if self.enable_telescope and self.enable_magiq:
            AddTarget.execute(self.SciObservingBlock.Target.to_dict())

    def save_SciOB_to_file(self):
        print(self.SciObservingBlock.__repr__())
        targname = self.SciObservingBlock.Target.get('TargetName')
        default_path_and_name = f"{self.file_path}/{targname}.yaml"
        result = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File',
                                             f"{default_path_and_name}",
                                             "OB Files (*yaml);;All Files (*)")
        if result:
            save_file = result[0]
            if save_file != '':
                # save fname as path to use in future
                self.file_path = Path(save_file).parent
                self.log.info(f'Saving science OB to file: {save_file}')
                self.SciObservingBlock.write_to(save_file)
        else:
            self.log.info('No output file chosen')

    def load_SciOB_from_file(self):
        file, filefilter = QtWidgets.QFileDialog.getOpenFileName(self, 
                                     "Open File", f"{self.file_path}",
                                     "OB Files (*yaml);;All Files (*)")
        if file:
            file = Path(file)
            if file.exists():
                self.file_path = file.parent
                print(f"Opening: {str(file)}")
                newOB = ObservingBlock(file)
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
            duration = EstimateOBDuration.execute({'fast': self.fast}, OB=self.CalObservingBlock)
            self.CalEstimatedDuration.setText(f"{duration/60:.0f} min")
        else:
            self.CalOBString.setText('')
            self.CalEstimatedDuration.setText('')

    def send_CalOB_to_list(self):
        if self.CalObservingBlock.validate() != True:
            print('OB is invalid, not sending to OB list')
        elif self.KPFCC == False:
            self.model.OBs.append(self.CalObservingBlock)
            self.model.layoutChanged.emit()
        elif self.KPFCC == True:
            self.model.OBs.append(self.CalObservingBlock)
            self.model.start_times.append(24)
            self.model.sort('time')
            self.model.layoutChanged.emit()
            self.set_SortOrWeather()

    def save_CalOB_to_file(self):
        default_path_and_name = f"{self.file_path}/newcalibration.yaml"
        result = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File',
                                             f"{default_path_and_name}",
                                             "OB Files (*yaml);;All Files (*)")
        if result:
            save_file = result[0]
            if save_file != '':
                # save fname as path to use in future
                self.file_path = Path(save_file).parent
                self.log.info(f'Saving calibration OB to file: {save_file}')
                self.CalObservingBlock.write_to(save_file)
        else:
            self.log.info('No output file chosen')

    def load_CalOB_from_file(self):
        file, filefilter = QtWidgets.QFileDialog.getOpenFileName(self, 
                                     "Open File", f"{self.file_path}",
                                     "OB Files (*yaml);;All Files (*)")
        if file:
            file = Path(file)
            if file.exists():
                self.file_path = file.parent
                print(f"Opening: {str(file)}")
                newOB = ObservingBlock(file)
                if newOB.validate() == True:
                    self.set_Calibrations(newOB.Calibrations)


    def exit(self):
        self.log.info("Exiting ...")
        sys.exit(0)


##-------------------------------------------------------------------------
## Define main()
##-------------------------------------------------------------------------
def main():
    application = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.setupUi()
    main_window.show()
    return kPyQt.run(application)

##-------------------------------------------------------------------------
## if __name__ == '__main__':
##-------------------------------------------------------------------------
if __name__ == '__main__':
    guilog = create_GUI_log()
    guilog.info(f"Starting KPF OB GUI")
    try:
        main()
    except Exception as e:
        guilog.error(e)
        guilog.error(traceback.format_exc())
    guilog.info(f"Exiting KPF OB GUI")

