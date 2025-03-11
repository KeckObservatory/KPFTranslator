#!/kroot/rel/default/bin/kpython3
import sys
import traceback
import time
import copy
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import re
import subprocess
import yaml
import datetime
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, Angle
from astropy.time import Time

import ktl                      # provided by kroot/ktl/keyword/python
import kPyQt                    # provided by kroot/kui/kPyQt
from PyQt5 import uic, QtWidgets, QtCore, QtGui

from kpf.OB_GUI.GUIcomponents import (OBListModel, ScrollMessageBox,
                                      EditableMessageBox, ObserverCommentBox,
                                      SelectProgramPopup)
from kpf.ObservingBlocks.Target import Target
from kpf.ObservingBlocks.Calibration import Calibration
from kpf.ObservingBlocks.Observation import Observation
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.scripts.EstimateOBDuration import EstimateOBDuration
from kpf.spectrograph.QueryFastReadMode import QueryFastReadMode


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
def create_GUI_log():
    log = logging.getLogger('KPF_OB_GUI')
    log.setLevel(logging.DEBUG)
    ## Set up console output
    LogConsoleHandler = logging.StreamHandler()
    LogConsoleHandler.setLevel(logging.DEBUG)
    LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s')
    LogConsoleHandler.setFormatter(LogFormat)
    log.addHandler(LogConsoleHandler)
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
    log.addHandler(LogFileHandler)
    return log


##-------------------------------------------------------------------------
## Keck Horizon
##-------------------------------------------------------------------------
def above_horizon(az, el):
    '''From https://www2.keck.hawaii.edu/inst/common/TelLimits.html
    Az 5.3 to 146.2, 33.3
    Az Elsewhere, 18
    '''
    if az >= 5.3 and az <= 146.2:
        horizon = 33.3
    else:
        horizon = 18
    return el > horizon

def near_horizon(az, el, margin=5):
    '''From https://www2.keck.hawaii.edu/inst/common/TelLimits.html
    Az 5.3 to 146.2, 33.3
    Az Elsewhere, 18
    '''
    if az >= 5.3 and az <= 146.2:
        horizon = 33.3 - margin
    else:
        horizon = 18 - margin
    return el > horizon


##-------------------------------------------------------------------------
## Define Application MainWindow
##-------------------------------------------------------------------------
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
        ui_file = Path(__file__).parent / 'KPF_OB_GUI.ui'
        uic.loadUi(f"{ui_file}", self)
        self.log = log
        self.file_path = Path('/s/sdata1701/OBs')
        self.log.debug('Initializing MainWindow')
        self.KPFCC = False
        self.BS_ObservingBlock = None
        self.BS_Target = Target({})
        self.BS_Observations = [Observation({})]
        self.BC_ObservingBlock = None
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


    def setupUi(self):
        self.log.debug('setupUi')
        self.setWindowTitle("KPF OB GUI")

        #-------------------------------------------------------------------
        # Menu Bar
        ActionExit = self.findChild(QtWidgets.QAction, 'actionExit')
        ActionExit.triggered.connect(self.exit)
        LoadOBsFromProgram = self.findChild(QtWidgets.QAction, 'action_LoadOBsFromProgram')
        LoadOBsFromProgram.triggered.connect(self.load_OBs_from_program)
        LoadOBFromFile = self.findChild(QtWidgets.QAction, 'action_LoadOBFromFile')
        LoadOBFromFile.triggered.connect(self.load_OB_from_file)

        #-------------------------------------------------------------------
        # Main Window

        # Program ID
        self.ProgID = self.findChild(QtWidgets.QLabel, 'ProgID')
        self.PROGNAME.stringCallback.connect(self.ProgID.setText)

        # Observer
        self.Observer = self.findChild(QtWidgets.QLabel, 'Observer')
        observer_kw = kPyQt.kFactory(ktl.cache('kpfexpose', 'OBSERVER'))
        observer_kw.stringCallback.connect(self.Observer.setText)

        # script name
        self.scriptname_value = self.findChild(QtWidgets.QLabel, 'scriptname_value')
        scriptname_kw = kPyQt.kFactory(ktl.cache('kpfconfig', 'SCRIPTNAME'))
        scriptname_kw.stringCallback.connect(self.update_scriptname_value)

        # script stop
#         self.scriptstop_value = self.findChild(QtWidgets.QLabel, 'scriptstop_value')
#         scriptstop_kw = kPyQt.kFactory(self.kpfconfig['SCRIPTSTOP'])
#         scriptstop_kw.stringCallback.connect(self.update_scriptstop_value)
#         self.scriptstop_btn = self.findChild(QtWidgets.QPushButton, 'scriptstop_btn')
#         self.scriptstop_btn.clicked.connect(self.set_scriptstop)

        # full stop
#         self.fullstop_btn = self.findChild(QtWidgets.QPushButton, 'fullstop_btn')
#         self.fullstop_btn.clicked.connect(self.do_fullstop)

        # expose status
        self.expose_status_value = self.findChild(QtWidgets.QLabel, 'expose_status_value')
        expose_kw = kPyQt.kFactory(ktl.cache('kpfexpose', 'EXPOSE'))
        expose_kw.stringCallback.connect(self.update_expose_status_value)

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
        self.OBListHeader.setText(f"    {self.hdr}")

        self.ListOfOBs = self.findChild(QtWidgets.QListView, 'ListOfOBs')
        self.model = OBListModel(OBs=[])
        self.ListOfOBs.setModel(self.model)
        self.ListOfOBs.selectionModel().selectionChanged.connect(self.select_OB_from_GUI)

        # Selected Observing Block Details
        self.SOB_TargetName = self.findChild(QtWidgets.QLabel, 'SOB_TargetName')
        self.SOB_GaiaID = self.findChild(QtWidgets.QLabel, 'SOB_GaiaID')
        self.SOB_TargetRA = self.findChild(QtWidgets.QLabel, 'SOB_TargetRA')
        self.SOB_TargetDec = self.findChild(QtWidgets.QLabel, 'SOB_TargetDec')
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
        self.BS_OBString = self.findChild(QtWidgets.QLabel, 'BS_OBString')
        self.BS_OBString.setStyleSheet("background:white")
        self.BS_OBValid = self.findChild(QtWidgets.QLabel, 'BS_OBValid')
        self.BS_EstimatedDuration = self.findChild(QtWidgets.QLabel, 'BS_EstimatedDuration')
        self.BS_SendToOBList = self.findChild(QtWidgets.QPushButton, 'BS_SendToOBList')
        self.BS_SendToOBList.clicked.connect(self.BS_send_to_list)
        # Target
        self.BS_QuerySimbadLineEdit = self.findChild(QtWidgets.QLineEdit, 'BS_QuerySimbadLineEdit')
        self.BS_QuerySimbadButton = self.findChild(QtWidgets.QPushButton, 'BS_QuerySimbadButton')
        self.BS_QuerySimbadButton.clicked.connect(self.BS_query_simbad)
        self.BS_TargetValid = self.findChild(QtWidgets.QLabel, 'BS_TargetValid')
        self.BS_ClearTargetButton = self.findChild(QtWidgets.QPushButton, 'BS_ClearTargetButton')
        self.BS_ClearTargetButton.clicked.connect(self.BS_clear_target)
        self.BS_TargetView = self.findChild(QtWidgets.QPlainTextEdit, 'BS_TargetView')
        self.BS_TargetView.setPlainText(self.BS_Target.__repr__(prune=False, comment=True))
        self.BS_TargetView.setFont(QtGui.QFont('Courier New', 11))
        self.BS_edit_target()
        self.BS_TargetView.textChanged.connect(self.BS_edit_target)
        # Observations
        self.BS_ObservationsValid = self.findChild(QtWidgets.QLabel, 'BS_ObservationsValid')
        self.BS_ClearObservationsButton = self.findChild(QtWidgets.QPushButton, 'BS_ClearObservationsButton')
        self.BS_ClearObservationsButton.clicked.connect(self.BS_clear_observations)
        self.BS_ObservationsView = self.findChild(QtWidgets.QPlainTextEdit, 'BS_ObservationsView')
        self.BS_ObservationsView.setPlainText(Observation({}).__repr__(prune=False, comment=True))
        self.BS_ObservationsView.setFont(QtGui.QFont('Courier New', 11))
        self.BS_edit_observations()
        self.BS_ObservationsView.textChanged.connect(self.BS_edit_observations)

        #-------------------------------------------------------------------
        # Tab: Build Calibration OB
        # Observing Block
        self.BC_OBString = self.findChild(QtWidgets.QLabel, 'BC_OBString')
        self.BC_OBString.setStyleSheet("background:white")
        self.BC_OBValid = self.findChild(QtWidgets.QLabel, 'BC_OBValid')
        self.BC_EstimatedDuration = self.findChild(QtWidgets.QLabel, 'BC_EstimatedDuration')
        self.BC_SendToOBList = self.findChild(QtWidgets.QPushButton, 'BC_SendToOBList')
        self.BC_SendToOBList.clicked.connect(self.BC_send_to_list)
        # Calibrations
        self.BC_CalibrationsValid = self.findChild(QtWidgets.QLabel, 'BC_CalibrationsValid')
        self.BC_ClearCalibrationsButton = self.findChild(QtWidgets.QPushButton, 'BC_ClearCalibrationsButton')
        self.BC_ClearCalibrationsButton.clicked.connect(self.BC_clear_calibrations)
        self.BC_ExampleCalibrations = self.findChild(QtWidgets.QComboBox, 'BC_ExampleCalibrations')
        self.BC_ExampleCalibrations.addItems([''])
        self.BC_ExampleCalibrations.addItems([cal.get('Object') for cal in self.example_calOB.Calibrations])
        self.BC_ExampleCalibrations.currentTextChanged.connect(self.BC_add_example_calibration)
        self.BC_CalibrationsView = self.findChild(QtWidgets.QPlainTextEdit, 'BC_CalibrationsView')
        self.BC_CalibrationsView.setPlainText(self.example_calOB.Calibrations[2].__repr__(prune=False, comment=True))
        self.BC_CalibrationsView.setFont(QtGui.QFont('Courier New', 11))
        self.BC_edit_calibrations()
        self.BC_CalibrationsView.textChanged.connect(self.BC_edit_calibrations)


    ##-------------------------------------------
    ## Methods to display updates from keywords
    ##-------------------------------------------
    # Script Name
    def update_scriptname_value(self, value):
        '''Set label text and set color'''
        scriptname_string = value.replace('.py', '')
        self.log.debug(f"update_scriptname_value: {scriptname_string}")
        self.scriptname_value.setText(f"{scriptname_string}")
        if value in ['None', '']:
            self.scriptname_value.setStyleSheet("color:green")
        else:
            self.scriptname_value.setStyleSheet("color:orange")

    # Expose Status
    def update_expose_status_value(self, value):
        '''Set label text and set color'''
#         self.log.debug(f'update_expose_status_value: {value}')
        self.expose_status_value.setText(f"{value}")
        if value == 'Ready':
            self.expose_status_value.setStyleSheet("color:green")
        elif value in ['Start', 'InProgress', 'Readout']:
            self.expose_status_value.setStyleSheet("color:orange")


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
            log.info(f'Modifying kpfconfig.SLEWCALREQ = {(value == 2)}')
            self.kpfconfig['SLEWCALREQ'].write((value == 2))

    ##-------------------------------------------
    ## Methods to get data from DB or Schedule
    ##-------------------------------------------
    def load_OB_from_file(self):
        self.log.debug(f"load_OBs_from_file")
        result = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File',
                                       f"{self.file_path}",
                                       "OB Files (*yaml);;All Files (*)")
        if result:
            chosen_file = result[0]
            if chosen_file != '':
                self.file_path = Path(chosen_file).parent
                print(f"Opening: {chosen_file}")
                newOB = ObservingBlock(chosen_file)
                if newOB.validate() == True:
                    self.model.OBs.append(newOB)
                    self.model.layoutChanged.emit()

    def get_progIDs(self):
        progIDs = ['', 'KPF-CC']
        # Go get list of available program IDs for Instrument=KPF
        return progIDs + ['E123', 'E456', 'CPS 2024B']

    def set_SortOrWeather(self):
        if self.KPFCC == True:
            self.SortOrWeatherLabel.setText('Weather Band:')
            self.SortOrWeatherLabel.setEnabled(True)
            self.SortOrWeather.clear()
            self.SortOrWeather.addItems(['1', '2', '3'])
            self.SortOrWeather.currentTextChanged.connect(self.set_weather_band)
            self.SortOrWeather.setEnabled(True)
        else:
            self.SortOrWeatherLabel.setText('Sort List By:')
            self.SortOrWeatherLabel.setEnabled(True)
            self.SortOrWeather.clear()
            self.SortOrWeather.addItems(['', 'Name', 'RA', 'Dec', 'Gmag', 'Jmag'])
            self.SortOrWeather.currentTextChanged.connect(self.sort_OB_list)
            self.SortOrWeather.setEnabled(True)

    def load_OBs_from_program(self):
        select_program_popup = SelectProgramPopup(self.get_progIDs())
        if select_program_popup.exec():
            if len(self.model.OBs) == 0:
                self.set_ProgID(select_program_popup.ProgID)
            else:
                confirmation_popup = QtWidgets.QMessageBox()
                confirmation_popup.setIcon(QtWidgets.QMessageBox.Question)
                confirmation_popup.setWindowTitle("Overwrite OB List?")
                msg = 'Loading OBs from a new program will clear the current list of OBs. Continue?'
                confirmation_popup.setText(msg)
                confirmation_popup.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
                if confirmation_popup.exec():
                    self.set_ProgID(select_program_popup.ProgID)
                else:
                    print("Cancel! Not overwriting OB list.")
        else:
            print("Cancel! Not pulling OBs from database.")


    def set_ProgID(self, value):
        self.log.info(f"set_ProgID: '{value}'")
        self.clear_OB_selection()
        self.KPCC = False
        if value == '':
            self.OBListHeader.setText(hdr)
            self.model.OBs = []
            self.model.start_times = None
            self.model.layoutChanged.emit()
            self.set_SortOrWeather()
        elif value == 'CPS 2024B':
            self.OBListHeader.setText(f"    {self.hdr}")
            files = [f for f in Path('/s/sdata1701/OBs/jwalawender/OBs_v2/howard/2024B').glob('*.yaml')]
            self.model.OBs = []
            for i,file in enumerate(files[:30]):
                try:
                    self.model.OBs.append(ObservingBlock(file))
                except:
                    print(f"Failed file {i+1}: {file}")
            print(f"Read in {len(self.model.OBs)} files")
            self.model.start_times = None
            self.model.layoutChanged.emit()
            self.set_SortOrWeather()
        elif value == 'KPF-CC':
            self.KPFCC = True
            self.OBListHeader.setText('    StartTime '+self.hdr)
            files = [f for f in Path('/s/sdata1701/OBs/jwalawender/OBs_v2/howard/2024B').glob('*.yaml')]
            self.model.OBs = []
            self.model.start_times = []
            for i,file in enumerate(files[:30]):
                try:
                    self.model.OBs.append(ObservingBlock(file))
                    import random
                    obstime = random.randrange(5, 17, step=1) + random.random()
                    self.model.start_times.append(obstime)
                except:
                    print(f"Failed file {i+1}: {file}")
            print(f"Read in {len(self.model.OBs)} files")
            self.model.sort('time')
            self.model.layoutChanged.emit()
            self.set_SortOrWeather()
        else:
            self.OBListHeader.setText(f"    {self.hdr}")
            self.model.OBs = [ObservingBlock('/s/sdata1701/OBs/jwalawender/OBs_v2/219134.yaml'),
                              ObservingBlock('/s/sdata1701/OBs/jwalawender/OBs_v2/157279.yaml'),
                              ObservingBlock('/s/sdata1701/OBs/jwalawender/OBs_v2/Calibrations/EtalonTest.yaml'),
                              ]
            self.model.start_times = None
            self.model.layoutChanged.emit()
            self.set_SortOrWeather()
        self.ProgID.setText(value)
        # This select/deselect operation caches something in the AltAz 
        # calculation which happens the first time an OB is selected. This
        # just makes the GUI more "responsive" as the loading of the OBs when
        # program ID is chosen contains all of the slow caching of values
        # instead of having it happen on the first click.
        if len(self.model.OBs) > 0:
            self.select_OB(0)
            self.select_OB(None)

    def set_weather_band(self, value):
        self.SortOrWeather.setCurrentText(value)


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
        self.SOB_AddComment.setEnabled(enabled)
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
        if abs(SOB.Target.PMRA.value) > 0.0001 or abs(SOB.Target.PMDEC.value) > 0.0001:
            try:
                now = Time(datetime.datetime.utcnow())
                coord_now = SOB.Target.coord.apply_space_motion(new_obstime=now)
                coord_now_string = coord_now.to_string('hmsdms', sep=':', precision=2)
                self.SOB_TargetRA.setText(coord_now_string.split()[0])
                self.SOB_TargetDec.setText(coord_now_string.split()[1])
            except:
                self.SOB_TargetRA.setText(SOB.Target.get('RA'))
                self.SOB_TargetDec.setText(SOB.Target.get('Dec'))
        else:
            self.SOB_TargetRA.setText(SOB.Target.get('RA'))
            self.SOB_TargetDec.setText(SOB.Target.get('Dec'))
        self.SOB_Jmag.setText(f"{SOB.Target.get('Jmag'):.2f}")
        self.SOB_Gmag.setText(f"{SOB.Target.get('Gmag'):.2f}")

        # Calculate AltAz Position
        if SOB.Target.coord is None:
            log.warning(f'SOB Target is not convertable to SkyCoord')
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
        else:
            SOB = self.model.OBs[self.SOBindex]
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
        OBcontents_popup = ScrollMessageBox(SOB)
        OBcontents_popup.setWindowTitle(f"Full OB Contents: {SOB.summary()}")
        result = OBcontents_popup.exec_()
        if result == QtWidgets.QMessageBox.Ok:
            log.debug('Show popup: Ok')
        elif result == QtWidgets.QMessageBox.Cancel:
            log.info('Show popup: Edit')
            OBedit_popup = EditableMessageBox(SOB)
            OBedit_popup.setWindowTitle(f"Editing OB: {SOB.summary()}")
            edit_result = OBedit_popup.exec_()
            if edit_result == QtWidgets.QMessageBox.Ok:
                log.info('Edit popup: Ok')
                if OBedit_popup.result.validate():
                    log.info('The edited OB has been validated')
                    self.model.OBs[self.SOBindex] = OBedit_popup.result
                    self.model.layoutChanged.emit()
                    self.update_SOB_display()
                else:
                    log.warning('Edits did not validate. Not changing OB.')
            elif edit_result == QtWidgets.QMessageBox.Cancel:
                log.debug('Edit popup: Cancel')


    def add_comment(self):
        if self.SOBindex is None:
            print('add_comment: No OB selected')
            return
        SOB = self.model.OBs[self.SOBindex]
        comment_box = ObserverCommentBox(SOB, self.Observer.text())
        if comment_box.exec():
            print(f"Submitting comment: {comment_box.comment}")
            print(f"From commentor: {comment_box.observer}")
        else:
            print("Cancel! Not submitting comment.")


    def execute_SOB(self):
        SOB = self.model.OBs[self.SOBindex]
        if SOB is not None:
            self.log.debug(f"execute_SOB")
            executeOB_popup = QtWidgets.QMessageBox()
            executeOB_popup.setWindowTitle('Execute Science OB Confirmation')
            executeOB_popup.setText("Do you really want to execute the current OB?")
            executeOB_popup.setIcon(QtWidgets.QMessageBox.Critical)
            executeOB_popup.setStandardButtons(QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes) 
            result = executeOB_popup.exec_()
            if result == QtWidgets.QMessageBox.Yes:
                self.RunOB(SOB)
                self.model.OBs[self.SOBindex].executed = True
                self.model.layoutChanged.emit()
            else:
                log.debug('User opted not to execute OB')


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
        RunOB_cmd = f'kpfdo RunOB -f {tmp_file} ; echo "Done!" ; sleep 30'
        # Pop up an xterm with the script running
        cmd = ['xterm', '-title', 'RunOB', '-name', 'RunOB',
               '-fn', '10x20', '-bg', 'black', '-fg', 'white',
               '-e', f'{RunOB_cmd}']
        print(RunOB_cmd)
        print(' '.join(cmd))
#         proc = subprocess.Popen(cmd)

    def remove_SOB(self):
        self.model.OBs.pop(self.SOBindex)
        self.clear_OB_selection()
        self.model.layoutChanged.emit()

    ##-------------------------------------------
    ## Methods for the Build a Science OB Tab
    ##-------------------------------------------
    def BS_edit_target(self):
        BST_edited_lines = self.BS_TargetView.document().toPlainText()
        try:
            new_dict = yaml.safe_load(BST_edited_lines)
            self.BS_Target = Target(new_dict)
        except Exception as e:
            print(e)
            self.BS_Target = None
        TargetValid = False if self.BS_Target is None else self.BS_Target.validate()
        color = {True: 'green', False: 'orange'}[TargetValid]
        self.BS_TargetValid.setText(str(TargetValid))
        self.BS_TargetValid.setStyleSheet(f"color:{color}")
        self.BS_form_OB()

    def BS_query_simbad(self):
        target_name = self.BS_QuerySimbadLineEdit.text().strip()
        print(f"Querying: {target_name}")
        self.BS_Target = self.BS_Target.resolve_name(target_name)
        self.BS_TargetView.setPlainText(self.BS_Target.__repr__(prune=False, comment=True))
        TargetValid = False if self.BS_Target is None else self.BS_Target.validate()
        color = {True: 'green', False: 'orange'}[TargetValid]
        self.BS_TargetValid.setText(str(TargetValid))
        self.BS_TargetValid.setStyleSheet(f"color:{color}")

    def BS_refresh_target_comments(self):
        out = self.BS_Target.__repr__(prune=False, comment=True)
        cursor = self.BS_TargetView.textCursor()
        cursor_position = cursor.position()
        self.BS_TargetView.setPlainText(out)
        try:
            # Restore cursor position
            cursor.setPosition(cursor_position)
            self.BS_TargetView.setTextCursor(cursor)
        except:
            pass
        self.BS_form_OB()

    def BS_clear_target(self):
        self.BS_Target = Target({})
        self.BS_TargetView.setPlainText(self.BS_Target.__repr__(prune=False, comment=True))
        self.BS_form_OB()

    def BS_edit_observations(self):
        BSO_edited_lines = self.BS_ObservationsView.document().toPlainText()
        try:
            new_dict = yaml.safe_load(BSO_edited_lines)
            self.BS_Observations = [Observation(entry) for entry in new_dict]
            ObservationsValid = np.all([entry.validate() for entry in self.BS_Observations])
        except Exception as e:
            print(e)
            self.BS_Observations = [Observation({})]
            ObservationsValid = False
        color = {True: 'green', False: 'orange'}[ObservationsValid]
        self.BS_ObservationsValid.setText(str(ObservationsValid))
        self.BS_ObservationsValid.setStyleSheet(f"color:{color}")
        self.BS_form_OB()

    def BS_refresh_observation_comments(self):
        out = []
        for i,obs in enumerate(self.BS_Observations):
            out.append(f'# Observation {i+1}\n')
            out.append(obs.__repr__(prune=False, comment=True))
        cursor = self.BS_ObservationsView.textCursor()
        cursor_position = cursor.position()
        self.BS_ObservationsView.setPlainText(''.join(out))
        try:
            # Restore cursor position
            cursor.setPosition(cursor_position)
            self.BS_ObservationsView.setTextCursor(cursor)
        except:
            pass
        self.BS_form_OB()

    def BS_clear_observations(self):
        self.BS_Observations = [Observation({})]
        self.BS_ObservationsView.setPlainText(Observation({}).__repr__(prune=False, comment=True))
        self.BS_form_OB()

    def BS_form_OB(self):
        newOB = ObservingBlock({})
        newOB.Target = self.BS_Target
        newOB.Observations = self.BS_Observations
        if newOB.__repr__() == self.BS_ObservingBlock.__repr__():
            return
        self.BS_ObservingBlock = ObservingBlock({})
        self.BS_ObservingBlock.Target = self.BS_Target
        self.BS_ObservingBlock.Observations = self.BS_Observations
        self.BS_refresh_observation_comments()
        self.BS_refresh_target_comments()
        OBValid = self.BS_ObservingBlock.validate()
        color = {True: 'green', False: 'orange'}[OBValid]
        self.BS_OBValid.setText(str(OBValid))
        self.BS_OBValid.setStyleSheet(f"color:{color}")
        if OBValid:
            self.BS_OBString.setText(self.BS_ObservingBlock.summary())
            duration = EstimateOBDuration.execute({'fast': self.fast}, OB=self.BS_ObservingBlock)
            self.BS_EstimatedDuration.setText(f"{duration/60:.0f} min")
        else:
            self.BS_OBString.setText('')
            self.BS_EstimatedDuration.setText('')

    def BS_send_to_list(self):
        if self.BS_ObservingBlock.validate() != True:
            print('OB is invalid, not sending to OB list')
        elif self.KPFCC == False:
            self.model.OBs.append(self.BS_ObservingBlock)
            self.model.layoutChanged.emit()
        elif self.KPFCC == True:
            self.model.OBs.append(self.BS_ObservingBlock)
            self.model.start_times.append(24)
            self.model.sort('time')
            self.model.layoutChanged.emit()
            self.set_SortOrWeather()


    ##-------------------------------------------
    ## Methods for the Build a Calibration OB Tab
    ##-------------------------------------------
    def BC_edit_calibrations(self):
        BCC_edited_lines = self.BC_CalibrationsView.document().toPlainText()
        try:
            new_dict = yaml.safe_load(BCC_edited_lines)
            calibrations = [Calibration(entry) for entry in new_dict]
            CalibrationsValid = np.all([entry.validate() for entry in calibrations])
        except Exception as e:
            print(e)
            CalibrationsValid = False
        color = {True: 'green', False: 'orange'}[CalibrationsValid]
        self.BC_CalibrationsValid.setText(str(CalibrationsValid))
        self.BC_CalibrationsValid.setStyleSheet(f"color:{color}")
        if CalibrationsValid:
            self.BC_form_OB(calibrations)


    def BC_refresh_calibration_text(self):
        out = []
        for i,cal in enumerate(self.BC_ObservingBlock.Calibrations):
            out.append(f'# Calibration {i+1}\n')
            out.append(cal.__repr__(prune=False, comment=True))
        cursor = self.BC_CalibrationsView.textCursor()
        cursor_position = cursor.position()
        self.BC_CalibrationsView.setPlainText(''.join(out))
        try:
            # Restore cursor position
            cursor.setPosition(cursor_position)
            self.BC_CalibrationsView.setTextCursor(cursor)
        except:
            pass

    def BC_clear_calibrations(self):
        calibrations = []
        self.BC_CalibrationsView.setPlainText('')
        self.BC_form_OB(calibrations)

    def BC_add_example_calibration(self, value):
        log.debug(f'BC_add_example_calibration: {value}')
        for cal in self.example_calOB.Calibrations:
            if value == cal.get('Object'):
                log.debug(f'Adding {value} from example Cal OB')
                calibrations = copy.deepcopy(self.BC_ObservingBlock.Calibrations)
                calibrations.append(cal)
                self.BC_form_OB(calibrations)

    def BC_form_OB(self, calibrations):
        newOB = ObservingBlock({})
        newOB.Calibrations = calibrations
        if newOB.__repr__() == self.BC_ObservingBlock.__repr__():
            return
        self.BC_ObservingBlock = copy.deepcopy(newOB)
        OBValid = self.BC_ObservingBlock.validate()
        color = {True: 'green', False: 'orange'}[OBValid]
        self.BC_OBValid.setText(str(OBValid))
        self.BC_OBValid.setStyleSheet(f"color:{color}")
        if OBValid:
            self.BC_OBString.setText(self.BC_ObservingBlock.summary())
            duration = EstimateOBDuration.execute({'fast': self.fast}, OB=self.BC_ObservingBlock)
            self.BC_EstimatedDuration.setText(f"{duration/60:.0f} min")
        else:
            self.BC_OBString.setText('')
            self.BC_EstimatedDuration.setText('')
        self.BC_refresh_calibration_text()

    def BC_send_to_list(self):
        if self.BC_ObservingBlock.validate() != True:
            print('OB is invalid, not sending to OB list')
        elif self.KPFCC == False:
            self.model.OBs.append(self.BC_ObservingBlock)
            self.model.layoutChanged.emit()
        elif self.KPFCC == True:
            self.model.OBs.append(self.BC_ObservingBlock)
            self.model.start_times.append(24)
            self.model.sort('time')
            self.model.layoutChanged.emit()
            self.set_SortOrWeather()


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
    log = create_GUI_log()
    log.info(f"Starting KPF OB GUI")
    try:
        main()
    except Exception as e:
        log.error(e)
        log.error(traceback.format_exc())
    log.info(f"Exiting KPF OB GUI")

