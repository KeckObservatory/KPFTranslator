#!/kroot/rel/default/bin/kpython3
import sys
import traceback
import time
from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler
import re
import subprocess
import yaml
import datetime
from copy import deepcopy
from astropy.coordinates import SkyCoord

import ktl                      # provided by kroot/ktl/keyword/python
import kPyQt                    # provided by kroot/kui/kPyQt
from PyQt5 import uic
from PyQt5.QtWidgets import (QApplication, QMainWindow,
                             QLabel, QPushButton, QLineEdit, QComboBox,
                             QCheckBox, QMessageBox, QFileDialog)

from kpf.utils import BuildOBfromQuery
from kpf.utils import SendEmail
from kpf.utils.EstimateOBDuration import EstimateCalOBDuration, EstimateSciOBDuration

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
    LogFileName = logdir / 'GUI.log'
    LogFileHandler = TimedRotatingFileHandler(LogFileName,
                                              when='D',
                                              utc=True,  interval=30,
                                              atTime=datetime.time(0, 0, 0))
    LogFileHandler.setLevel(logging.DEBUG)
    LogFileHandler.setFormatter(LogFormat)
    log.addHandler(LogFileHandler)
    return log


def main():
    application = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.setupUi()
    main_window.show()
    return kPyQt.run(application)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        QMainWindow.__init__(self, *args, **kwargs)
        ui_file = Path(__file__).parent / 'KPF_OB_GUI.ui'
        uic.loadUi(f"{ui_file}", self)
        self.log = log
        self.log.debug('Initializing MainWindow')
        # Initial OB settings
        self.name_query_text = ''
        self.gaia_query_text = ''
        self.target_names = None
        self.twomass_params = None
        self.gaia_params = None
        self.disabled_detectors = []
        self.OB = {'Template_Name': 'kpf_sci',
                   'Template_Version': 0.6,
                   'TriggerCaHK': True,
                   'TriggerGreen': True,
                   'TriggerRed': True,
                   'GuideMode': 'auto',
                   'GuideCamGain': 'high',
                   'GuideFPS': 100,
                   'SEQ_Observations': [
                        {'Object': '',
                         'nExp': '1',
                         'ExpTime': '10',
                         'ExpMeterMode': 'monitor',
                         'AutoExpMeter': False,
                         'ExpMeterExpTime': '0.5', 
                         'TakeSimulCal': True,
                         'AutoNDFilters': False,
                         'CalND1': 'OD 0.1',
                         'CalND2': 'OD 0.1'},
                    ]
                   }
        self.calOB = {'Template_Name': 'kpf_cal',
                      'Template_Version': 0.6,
                      'TriggerCaHK': False,
                      'TriggerGreen': True,
                      'TriggerRed': True,
                      'TriggerExpMeter': False,
                      'SEQ_Darks': [
                          {'Object': 'bias',
                           'nExp': 1,
                           'ExpTime': 0},
                          {'Object': 'dark',
                           'nExp': 1,
                           'ExpTime': 300},
                       ],
                      'SEQ_Calibrations': [
                          {'CalSource': 'EtalonFiber',
                           'Object': '',
                           'CalND1': 'OD 0.1',
                           'CalND2': 'OD 0.1',
                           'nExp': 1,
                           'ExpTime': 1,
                           'SSS_Science': True,
                           'SSS_Sky': True,
                           'TakeSimulCal': True,
                           'FF_FiberPos': 'Blank',
                           'ExpMeterExpTime': 1},
                       ],
                      }
        self.dark_seq1_enabled = True
        self.dark_seq2_enabled = False
        self.cal_seq1_enabled = True
        self.lamps_that_need_warmup = ['FF_FIBER', 'BRDBANDFIBER', 'TH_DAILY',
                                       'TH_GOLD', 'U_DAILY', 'U_GOLD']
        # Keywords
        self.log.debug('Cacheing keyword services')
        self.kpfconfig = ktl.cache('kpfconfig')
        self.kpflamps = ktl.cache('kpflamps')
        self.kpfexpose = ktl.cache('kpfexpose')
        # Slew Cal Time Colors/Warnings
        self.good_slew_cal_time = 1.0 # hours
        self.bad_slew_cal_time = 2.0 # hours
        # Path to OB files
        self.file_path = Path('/s/starlists')
        self.starlist_file_name = ''


    def setupUi(self):
        self.log.debug('setupUi')
        self.setWindowTitle("KPF OB GUI")

        # Program ID
        self.progID = self.findChild(QLabel, 'progID')
        progname_kw = kPyQt.kFactory(self.kpfexpose['PROGNAME'])
        progname_kw.stringCallback.connect(self.update_progname_value)

        # Observer
        self.Observer = self.findChild(QLabel, 'Observer')
        observer_kw = kPyQt.kFactory(self.kpfexpose['OBSERVER'])
        observer_kw.stringCallback.connect(self.update_observer_value)

        # script name
        self.scriptname_value = self.findChild(QLabel, 'scriptname_value')
        scriptname_kw = kPyQt.kFactory(self.kpfconfig['SCRIPTNAME'])
        scriptname_kw.stringCallback.connect(self.update_scriptname_value)

        # script pause
#         self.scriptpause_value = self.findChild(QLabel, 'scriptpause_value')
#         scriptpause_kw = kPyQt.kFactory(self.kpfconfig['SCRIPTPAUSE'])
#         scriptpause_kw.stringCallback.connect(self.update_scriptpause_value)

#         self.scriptpause_btn = self.findChild(QPushButton, 'scriptpause_btn')
#         self.scriptpause_btn.clicked.connect(self.set_scriptpause)

        # script stop
        self.scriptstop_value = self.findChild(QLabel, 'scriptstop_value')
        scriptstop_kw = kPyQt.kFactory(self.kpfconfig['SCRIPTSTOP'])
        scriptstop_kw.stringCallback.connect(self.update_scriptstop_value)

        self.scriptstop_btn = self.findChild(QPushButton, 'scriptstop_btn')
        self.scriptstop_btn.clicked.connect(self.set_scriptstop)

        # full stop
        self.fullstop_btn = self.findChild(QPushButton, 'fullstop_btn')
        self.fullstop_btn.clicked.connect(self.do_fullstop)

        # expose status
        self.expose_status_value = self.findChild(QLabel, 'expose_status_value')
        expose_kw = kPyQt.kFactory(self.kpfexpose['EXPOSE'])
        expose_kw.stringCallback.connect(self.update_expose_status_value)

        # object
        self.object_current_value = self.findChild(QLabel, 'object_current_value')
        object_kw = kPyQt.kFactory(self.kpfexpose['OBJECT'])
        object_kw.stringCallback.connect(self.object_current_value.setText)

        # lamps
        self.lamps_value = self.findChild(QLabel, 'lamps_value')
        lamps_kw = kPyQt.kFactory(self.kpflamps['LAMPS'])
        lamps_kw.stringCallback.connect(self.lamps_value.setText)

        # time since last cal
        self.slewcaltime_value = self.findChild(QLabel, 'slewcaltime_value')
        slewcaltime_kw = kPyQt.kFactory(self.kpfconfig['SLEWCALTIME'])
        slewcaltime_kw.stringCallback.connect(self.update_slewcaltime_value)

        # request slew cal
#         self.slewcalreq_value = self.findChild(QLabel, 'slewcalreq_value')
#         slewcalreq_kw = kPyQt.kFactory(self.kpfconfig['SLEWCALREQ'])
#         slewcalreq_kw.stringCallback.connect(self.update_slewcalreq_value)

        # slew cal file
        self.slewcalfile_value = self.findChild(QLabel, 'slewcalfile_value')
        slewcalfile_kw = kPyQt.kFactory(self.kpfconfig['SLEWCALFILE'])
        slewcalfile_kw.stringCallback.connect(self.update_slewcalfile_value)

        self.disabled_detectors_value = self.findChild(QLabel, 'disabled_detectors_value')
        self.disabled_detectors_value.setText('')
        cahk_enabled_kw = kPyQt.kFactory(self.kpfconfig['CA_HK_ENABLED'])
        cahk_enabled_kw.stringCallback.connect(self.update_ca_hk_enabled)
        green_enabled_kw = kPyQt.kFactory(self.kpfconfig['GREEN_ENABLED'])
        green_enabled_kw.stringCallback.connect(self.update_green_enabled)
        red_enabled_kw = kPyQt.kFactory(self.kpfconfig['RED_ENABLED'])
        red_enabled_kw.stringCallback.connect(self.update_red_enabled)
        expmeter_enabled_kw = kPyQt.kFactory(self.kpfconfig['EXPMETER_ENABLED'])
        expmeter_enabled_kw.stringCallback.connect(self.update_expmeter_enabled)

        ##----------------------
        ## Construct OB
        ##----------------------
        # Load OB from File
        self.load_from_file_btn = self.findChild(QPushButton, 'load_from_file_btn')
        self.load_from_file_btn.clicked.connect(self.run_load_from_file)

        # Generic Name Query
        self.name_query_input = self.findChild(QLineEdit, 'name_query_input')
        self.name_query_input.textChanged.connect(self.set_name_query_input)

        self.query_name_btn = self.findChild(QPushButton, 'query_name_btn')
        self.query_name_btn.clicked.connect(self.run_query_name)

        # Gaia DR3 Query
        self.gaia_query_input = self.findChild(QLineEdit, 'gaia_id_query_input')
        self.gaia_query_input.textChanged.connect(self.set_gaia_query_input)

        self.query_gaia_btn = self.findChild(QPushButton, 'query_gaia_btn')
        self.query_gaia_btn.clicked.connect(self.run_query_gaia)

        ##----------------------
        ## Export or Execute OB
        ##----------------------
        self.write_to_file_btn = self.findChild(QPushButton, 'write_to_file_btn')
        self.write_to_file_btn.clicked.connect(self.run_write_to_file)

        self.executeOB = self.findChild(QPushButton, 'executeOB')
        self.executeOB_tooltip = "Execute the OB as defined in the fields below"
        self.executeOB.setToolTip(self.executeOB_tooltip)
        self.executeOB.clicked.connect(self.run_executeOB)

        self.executeOB_slewcal = self.findChild(QPushButton, 'executeOB_slewcal')
        self.executeOB_slewcal_tooltip = "Execute a quick calibration, then the OB as defined in the fields below"
        self.executeOB_slewcal.setToolTip(self.executeOB_slewcal_tooltip)
        self.executeOB_slewcal.clicked.connect(self.run_executeOB_slewcal)

        self.collect_guider_cube = self.findChild(QPushButton, 'collect_guider_cube')
        self.collect_guider_cube.clicked.connect(self.run_collect_guider_cube)

        self.execute_slewcal_only = self.findChild(QPushButton, 'execute_slewcal_only')
        self.execute_slewcal_only_tooltip = "Execute a quick calibration without triggering OB"
        self.execute_slewcal_only.setToolTip(self.execute_slewcal_only_tooltip)
        self.execute_slewcal_only.clicked.connect(self.run_execute_slewcal_only)

        self.OBDuration = self.findChild(QLabel, 'OBDuration')
        duration_tooltip = ('Duration is an estimate and assumes nothing about '
                            'the current instrument state. As a result, many '
                            'OBs will take slightly less time than the estimate.')
        self.OBDuration.setToolTip(duration_tooltip)

        ##----------------------
        ## Science OB Tab
        ##----------------------
        # Star List
        self.star_list_line = self.findChild(QLabel, 'star_list_line')
        self.star_list_line.setText('Unable to form star list line without Gaia coordinates')
        self.star_list_line.setStyleSheet("background-color:white; font-family:monospace")

        self.append_to_star_list_btn = self.findChild(QPushButton, 'append_to_star_list_btn')
        self.append_to_star_list_btn.clicked.connect(self.run_append_to_star_list)

        # Target Name
        self.TargetName = self.findChild(QLineEdit, 'TargetName')
        self.TargetName.textChanged.connect(self.set_target_name)

        # Target Info Labels
        self.GaiaID = self.findChild(QLabel, 'GaiaID')
        self.twoMASSID = self.findChild(QLabel, 'twoMASSID')
        self.Parallax = self.findChild(QLabel, 'Parallax')
        self.RadialVelocity = self.findChild(QLabel, 'RadialVelocity')
        self.Gmag = self.findChild(QLabel, 'Gmag')
        self.Jmag = self.findChild(QLabel, 'Jmag')
        self.Teff = self.findChild(QLabel, 'Teff')

        # Guider Setup
        self.GuideMode = self.findChild(QComboBox, 'GuideMode')
        self.GuideMode.addItems(["auto", "manual", "off"])
        self.update_OB('GuideMode', self.OB['GuideMode'])
        self.GuideMode.currentTextChanged.connect(self.set_guide_mode)
        
        self.GuideCamGain = self.findChild(QComboBox, 'GuideCamGain')
        self.GuideCamGain.addItems(["high", "medium", "low"])
        self.update_OB('GuideCamGain', self.OB['GuideCamGain'])
        self.GuideCamGain.currentTextChanged.connect(self.set_guide_gain)
        self.GuideFPS = self.findChild(QLineEdit, 'GuideFPS')
        self.update_OB('GuideFPS', self.OB['GuideFPS'])
        self.GuideFPS.textChanged.connect(self.set_fps)
        if self.OB['GuideMode'] == 'auto':
            self.GuideFPS.setEnabled(False)

        # Spectrograph Setup
        self.TriggerCaHK = self.findChild(QCheckBox, 'TriggerCaHK')
        self.update_OB('TriggerCaHK', self.OB.get('TriggerCaHK'))
        self.TriggerCaHK.stateChanged.connect(self.TriggerCaHK_state_change)
        self.TriggerGreen = self.findChild(QCheckBox, 'TriggerGreen')
        self.update_OB('TriggerGreen', self.OB.get('TriggerGreen'))
        self.TriggerGreen.stateChanged.connect(self.TriggerGreen_state_change)
        self.TriggerRed = self.findChild(QCheckBox, 'TriggerRed')
        self.update_OB('TriggerRed', self.OB.get('TriggerRed'))
        self.TriggerRed.stateChanged.connect(self.TriggerRed_state_change)

        # First Observation Sequence Setup
        self.ObjectEdit = self.findChild(QLineEdit, 'ObjectEdit')
        self.ObjectEdit.textChanged.connect(self.set_object)
        self.update_OB('Object', self.OB['SEQ_Observations'][0]['Object'])

        self.nExpEdit = self.findChild(QLineEdit, 'nExpEdit')
        self.nExpEdit.textChanged.connect(self.set_nExp)
        self.update_OB('nExp', self.OB['SEQ_Observations'][0]['nExp'])

        self.ExpTimeEdit = self.findChild(QLineEdit, 'ExpTimeEdit')
        self.ExpTimeEdit.textChanged.connect(self.set_exptime)
        self.update_OB('ExpTime', self.OB['SEQ_Observations'][0]['ExpTime'])

        self.ExpMeterMode = self.findChild(QComboBox, 'ExpMeterMode')
        self.ExpMeterMode.addItems(["monitor"])
        self.update_OB('ExpMeterMode', self.OB['SEQ_Observations'][0]['ExpMeterMode'])
        self.ExpMeterMode.currentTextChanged.connect(self.set_expmeter_mode)

        self.ExpMeterExpTimeEdit = self.findChild(QLineEdit, 'ExpMeterExpTimeEdit')
        self.ExpMeterExpTimeEdit.textChanged.connect(self.set_expmeter_exptime)
        self.update_OB('ExpMeterExpTime', self.OB['SEQ_Observations'][0]['ExpMeterExpTime'])

        self.AutoEMExpTime = self.findChild(QCheckBox, 'AutoEMExpTime')
        self.AutoEMExpTime.stateChanged.connect(self.AutoEMExpTime_state_change)

        self.TakeSimulCal = self.findChild(QCheckBox, 'TakeSimulCal')
        self.TakeSimulCal.stateChanged.connect(self.TakeSimulCal_state_change)

        self.CalND1 = self.findChild(QComboBox, 'CalND1')
        self.CalND1.addItems(["OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0", "OD 3.0", "OD 4.0"])
        self.update_OB('CalND1', self.OB['SEQ_Observations'][0]['CalND1'])
        self.CalND1.currentTextChanged.connect(self.set_CalND1)

        self.CalND2 = self.findChild(QComboBox, 'CalND2')
        self.CalND2.addItems(["OD 0.1", "OD 0.3", "OD 0.5", "OD 0.8", "OD 1.0", "OD 4.0"])
        self.update_OB('CalND2', self.OB['SEQ_Observations'][0]['CalND2'])
        self.CalND2.currentTextChanged.connect(self.set_CalND2)

        self.AutoNDFilters = self.findChild(QCheckBox, 'AutoNDFilters')
        self.update_OB('AutoNDFilters', self.OB['SEQ_Observations'][0]['AutoNDFilters'])
        self.AutoNDFilters.stateChanged.connect(self.AutoNDFilters_state_change)

        # Do this after the CalND and AutoNDFilters objects have been created
        self.update_OB('TakeSimulCal', self.OB['SEQ_Observations'][0]['TakeSimulCal'])

        self.other_names = self.findChild(QLabel, 'other_names')

        ##----------------------
        ## Calibration OB Tab
        ##----------------------
        ## Export or Execute Cal OB
        self.write_calOB_to_file = self.findChild(QPushButton, 'write_to_file_btn_for_cal')
        self.write_calOB_to_file.clicked.connect(self.run_write_calOB_to_file)
        self.load_calOB_from_file_btn = self.findChild(QPushButton, 'load_from_file_btn_for_cal')
        self.load_calOB_from_file_btn.clicked.connect(self.run_load_calOB_from_file)

        self.executecalOB = self.findChild(QPushButton, 'executeOB_for_cal')
        self.executecalOB_tooltip = "Execute the Cal OB as defined in the fields below"
        self.executecalOB.setToolTip(self.executecalOB_tooltip)
        self.executecalOB.clicked.connect(self.run_executecalOB)
        calOB_tooltip = ('OB will be executed without an intensity monitor '
                         'measurement. If one is needed, use the command line.')
        self.executecalOB.setToolTip(calOB_tooltip)

        self.CalOBDuration = self.findChild(QLabel, 'CalOBDuration')
        self.CalOBDuration.setToolTip(duration_tooltip)

        ## Build Cal OB
        self.TriggerCaHK_cal = self.findChild(QCheckBox, 'TriggerCaHK_cal')
        self.update_calOB('TriggerCaHK', self.calOB.get('TriggerCaHK'))
        self.TriggerCaHK_cal.stateChanged.connect(self.TriggerCaHK_cal_state_change)
        self.TriggerGreen_cal = self.findChild(QCheckBox, 'TriggerGreen_cal')
        self.update_calOB('TriggerGreen', self.calOB.get('TriggerGreen'))
        self.TriggerGreen_cal.stateChanged.connect(self.TriggerGreen_cal_state_change)
        self.TriggerRed_cal = self.findChild(QCheckBox, 'TriggerRed_cal')
        self.update_calOB('TriggerRed', self.calOB.get('TriggerRed'))
        self.TriggerRed_cal.stateChanged.connect(self.TriggerRed_cal_state_change)
        self.TriggerExpMeter_cal = self.findChild(QCheckBox, 'TriggerExpMeter_cal')
        self.update_calOB('TriggerExpMeter', self.calOB.get('TriggerExpMeter'))
        self.TriggerExpMeter_cal.stateChanged.connect(self.TriggerExpMeter_cal_state_change)

        # Dark Sequence 1
        self.enable_dark_seq1 = self.findChild(QCheckBox, 'enable_dark_seq1')
        self.enable_dark_seq1.setChecked(self.dark_seq1_enabled)
        self.enable_dark_seq1.stateChanged.connect(self.enable_dark_seq1_state_change)

        self.Object_dark_seq1 = self.findChild(QLineEdit, 'Object_dark_seq1')
        self.Object_dark_seq1.textChanged.connect(self.set_Object_dark_seq1)
        self.update_calOB('dark1_Object', self.calOB['SEQ_Darks'][0]['Object'])
        self.Object_dark_seq1_label = self.findChild(QLabel, 'Object_dark_seq1_label')
        self.Object_dark_seq1_note = self.findChild(QLabel, 'Object_dark_seq1_note')

        self.nExp_dark_seq1 = self.findChild(QLineEdit, 'nExp_dark_seq1')
        self.nExp_dark_seq1.textChanged.connect(self.set_nExp_dark_seq1)
        self.update_calOB('dark1_nExp', self.calOB['SEQ_Darks'][0]['nExp'])
        self.nExp_dark_seq1_label = self.findChild(QLabel, 'nExp_dark_seq1_label')
        self.nExp_dark_seq1_note = self.findChild(QLabel, 'nExp_dark_seq1_note')

        self.ExpTime_dark_seq1 = self.findChild(QLineEdit, 'ExpTime_dark_seq1')
        self.ExpTime_dark_seq1.textChanged.connect(self.set_ExpTime_dark_seq1)
        self.update_calOB('dark1_ExpTime', self.calOB['SEQ_Darks'][0]['ExpTime'])
        self.ExpTime_dark_seq1_label = self.findChild(QLabel, 'ExpTime_dark_seq1_label')
        self.ExpTime_dark_seq1_note = self.findChild(QLabel, 'ExpTime_dark_seq1_note')

        # Dark Sequence 2
        self.enable_dark_seq2 = self.findChild(QCheckBox, 'enable_dark_seq2')
        self.enable_dark_seq2.setChecked(self.dark_seq2_enabled)
        self.enable_dark_seq2.stateChanged.connect(self.enable_dark_seq2_state_change)

        self.Object_dark_seq2 = self.findChild(QLineEdit, 'Object_dark_seq2')
        self.Object_dark_seq2.textChanged.connect(self.set_Object_dark_seq2)
        self.update_calOB('dark2_Object', self.calOB['SEQ_Darks'][1]['Object'])
        self.Object_dark_seq2_label = self.findChild(QLabel, 'Object_dark_seq2_label')
        self.Object_dark_seq2_note = self.findChild(QLabel, 'Object_dark_seq2_note')

        self.nExp_dark_seq2 = self.findChild(QLineEdit, 'nExp_dark_seq2')
        self.nExp_dark_seq2.textChanged.connect(self.set_nExp_dark_seq2)
        self.update_calOB('dark2_nExp', self.calOB['SEQ_Darks'][1]['nExp'])
        self.nExp_dark_seq2_label = self.findChild(QLabel, 'nExp_dark_seq2_label')
        self.nExp_dark_seq2_note = self.findChild(QLabel, 'nExp_dark_seq2_note')

        self.ExpTime_dark_seq2 = self.findChild(QLineEdit, 'ExpTime_dark_seq2')
        self.ExpTime_dark_seq2.textChanged.connect(self.set_ExpTime_dark_seq2)
        self.update_calOB('dark2_ExpTime', self.calOB['SEQ_Darks'][1]['ExpTime'])
        self.ExpTime_dark_seq2_label = self.findChild(QLabel, 'ExpTime_dark_seq2_label')
        self.ExpTime_dark_seq2_note = self.findChild(QLabel, 'ExpTime_dark_seq2_note')

        self.enable_dark_seq2_state_change(2 if self.dark_seq2_enabled is True else 0)

        # Cal Sequence 1
        self.enable_cal_seq1 = self.findChild(QCheckBox, 'enable_cal_seq1')
        self.enable_cal_seq1.setChecked(self.cal_seq1_enabled)
        self.enable_cal_seq1.stateChanged.connect(self.enable_cal_seq1_state_change)

        self.Object_cal_seq1 = self.findChild(QLineEdit, 'Object_cal_seq1')
        self.Object_cal_seq1.textChanged.connect(self.set_Object_cal_seq1)
        self.update_calOB('cal1_Object', self.calOB['SEQ_Calibrations'][0]['Object'])
        self.Object_cal_seq1_label = self.findChild(QLabel, 'Object_cal_seq1_label')
        self.Object_cal_seq1_note = self.findChild(QLabel, 'Object_cal_seq1_note')

        self.CalSource_cal_seq1 = self.findChild(QComboBox, 'CalSource_cal_seq1')
        self.CalSource_cal_seq1.addItems(['WideFlat', 'BrdbandFiber', 'U_gold',
                                          'U_daily', 'Th_daily', 'Th_gold',
                                          'LFCFiber', 'EtalonFiber',
                                          'SoCal-CalFib', 'SoCal-SciSky'])
        self.CalSource_cal_seq1.currentTextChanged.connect(self.set_CalSource_cal_seq1)
        self.update_calOB('cal1_CalSource', self.calOB['SEQ_Calibrations'][0]['CalSource'])
        self.CalSource_cal_seq1_label = self.findChild(QLabel, 'CalSource_cal_seq1_label')

        self.warm_up_warning = self.findChild(QLabel, 'warm_up_warning')

        self.CalND1_cal_seq1 = self.findChild(QComboBox, 'CalND1_cal_seq1')
        self.CalND1_cal_seq1.addItems(["OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0", "OD 3.0", "OD 4.0"])
        self.CalND1_cal_seq1.currentTextChanged.connect(self.set_CalND1_cal_seq1)
        self.update_calOB('cal1_CalND1', self.calOB['SEQ_Calibrations'][0]['CalND1'])
        self.CalND1_cal_seq1_label = self.findChild(QLabel, 'CalND1_cal_seq1_label')

        self.CalND2_cal_seq1 = self.findChild(QComboBox, 'CalND2_cal_seq1')
        self.CalND2_cal_seq1.addItems(["OD 0.1", "OD 0.3", "OD 0.5", "OD 0.8", "OD 1.0", "OD 4.0"])
        self.CalND2_cal_seq1.currentTextChanged.connect(self.set_CalND2_cal_seq1)
        self.update_calOB('cal1_CalND2', self.calOB['SEQ_Calibrations'][0]['CalND2'])
        self.CalND2_cal_seq1_label = self.findChild(QLabel, 'CalND2_cal_seq1_label')

        self.nExp_cal_seq1 = self.findChild(QLineEdit, 'nExp_cal_seq1')
        self.nExp_cal_seq1.textChanged.connect(self.set_nExp_cal_seq1)
        self.update_calOB('cal1_nExp', self.calOB['SEQ_Calibrations'][0]['nExp'])
        self.nExp_cal_seq1_label = self.findChild(QLabel, 'nExp_cal_seq1_label')
        self.nExp_cal_seq1_note = self.findChild(QLabel, 'nExp_cal_seq1_note')

        self.ExpTime_cal_seq1 = self.findChild(QLineEdit, 'ExpTime_cal_seq1')
        self.ExpTime_cal_seq1.textChanged.connect(self.set_ExpTime_cal_seq1)
        self.update_calOB('cal1_ExpTime', self.calOB['SEQ_Calibrations'][0]['ExpTime'])
        self.ExpTime_cal_seq1_label = self.findChild(QLabel, 'ExpTime_cal_seq1_label')
        self.ExpTime_cal_seq1_note = self.findChild(QLabel, 'ExpTime_cal_seq1_note')

        self.SSS_Science_cal_seq1 = self.findChild(QCheckBox, 'SSS_Science_cal_seq1')
        self.SSS_Science_cal_seq1.stateChanged.connect(self.SSS_Science_cal_seq1_state_change)
        self.update_calOB('cal1_SSS_Science', self.calOB['SEQ_Calibrations'][0]['SSS_Science'])

        self.SSS_Sky_cal_seq1 = self.findChild(QCheckBox, 'SSS_Sky_cal_seq1')
        self.SSS_Sky_cal_seq1.stateChanged.connect(self.SSS_Sky_cal_seq1_state_change)
        self.update_calOB('cal1_SSS_Sky', self.calOB['SEQ_Calibrations'][0]['SSS_Sky'])

        self.TakeSimulCal_cal_seq1 = self.findChild(QCheckBox, 'TakeSimulCal_cal_seq1')
        self.TakeSimulCal_cal_seq1.stateChanged.connect(self.TakeSimulCal_cal_seq1_state_change)
        self.update_calOB('cal1_TakeSimulCal', self.calOB['SEQ_Calibrations'][0]['TakeSimulCal'])

        self.FF_FiberPos_cal_seq1 = self.findChild(QComboBox, 'FF_FiberPos_cal_seq1')
        self.FF_FiberPos_cal_seq1.addItems(["Blank", "6 mm f/5", "7.5 mm f/4",
                                            "10 mm f/3", "13.2 mm f/2.3", "Open"])
        self.FF_FiberPos_cal_seq1.currentTextChanged.connect(self.set_FF_FiberPos_cal_seq1)
        self.update_calOB('cal1_FF_FiberPos', self.calOB['SEQ_Calibrations'][0]['FF_FiberPos'])
        self.FF_FiberPos_cal_seq1_label = self.findChild(QLabel, 'FF_FiberPos_cal_seq1_label')
        self.FF_FiberPos_cal_seq1.setEnabled(self.calOB['SEQ_Calibrations'][0]['CalSource'] == 'WideFlat')
        self.FF_FiberPos_cal_seq1_label.setEnabled(self.calOB['SEQ_Calibrations'][0]['CalSource'] == 'WideFlat')

        self.ExpMeterExpTime_cal_seq1 = self.findChild(QLineEdit, 'ExpMeterExpTime_cal_seq1')
        self.ExpMeterExpTime_cal_seq1.textChanged.connect(self.set_ExpMeterExpTime_cal_seq1)
        self.update_calOB('cal1_ExpMeterExpTime', self.calOB['SEQ_Calibrations'][0]['ExpMeterExpTime'])
        self.ExpMeterExpTime_cal_seq1_label = self.findChild(QLabel, 'ExpMeterExpTime_cal_seq1_label')
        self.ExpMeterExpTime_cal_seq1_note = self.findChild(QLabel, 'ExpMeterExpTime_cal_seq1_note')

    ##-------------------------------------------
    ## Methods relating to updates from keywords
    ##-------------------------------------------
    # Progname
    def update_progname_value(self, value):
        value = str(value).strip()
        self.log.debug(f'update_progname_value: {value}')
        self.progID.setText(value)

    # Observer
    def update_observer_value(self, value):
        value = str(value).strip()
        self.log.debug(f'update_observer_value: {value}')
        self.Observer.setText(value)

    # Script Name
    def update_scriptname_value(self, value):
        '''Set label text and set color'''
        self.log.debug(f'update_scriptname_value: {value}')
        self.scriptname_value.setText(value)
        if value in ['None', '']:
            self.scriptname_value.setStyleSheet("color:green")
        else:
            self.scriptname_value.setStyleSheet("color:orange")

    # Expose Status
    def update_expose_status_value(self, value):
        '''Set label text and set color'''
        self.log.debug(f'update_expose_status_value: {value}')
        self.expose_status_value.setText(value)
        if value == 'Ready':
            self.expose_status_value.setStyleSheet("color:green")
        elif value in ['Start', 'InProgress', 'Readout']:
            self.expose_status_value.setStyleSheet("color:orange")

    # SCRIPTPAUSE
#     def update_scriptpause_value(self, value):
#         '''Set label text and set color'''
#         self.log.debug(f"update_scriptpause_value: {value}")
#         self.scriptpause_value.setText(value)
#         if value == 'Yes':
#             self.scriptpause_value.setStyleSheet("color:orange")
#             self.scriptpause_btn.setText('RESUME')
#         elif value == 'No':
#             self.scriptpause_value.setStyleSheet("color:green")
#             self.scriptpause_btn.setText('PAUSE')

#     def set_scriptpause(self, value):
#         self.log.debug(f'set_scriptpause: {value}')
#         current_kw_value = self.kpfconfig['SCRIPTPAUSE'].read()
#         if current_kw_value == 'Yes':
#             self.kpfconfig['SCRIPTPAUSE'].write('No')
#             self.scriptpause_btn.setText('PAUSE')
#         elif current_kw_value == 'No':
#             self.kpfconfig['SCRIPTPAUSE'].write('Yes')
#             self.scriptpause_btn.setText('RESUME')

    # SCRIPTSTOP
    def update_scriptstop_value(self, value):
        '''Set label text and set color'''
        self.log.debug(f'update_scriptstop_value: {value}')
        self.scriptstop_value.setText(value)
        if value == 'Yes':
            self.scriptstop_value.setStyleSheet("color:red")
            self.scriptstop_btn.setText('CLEAR STOP')
            msg = 'Disabled because STOP has been requested.'
            self.executeOB.setEnabled(False)
            self.executeOB.setToolTip(msg)
            self.executeOB_slewcal.setEnabled(False)
            self.executeOB_slewcal.setToolTip(msg)
            self.execute_slewcal_only.setEnabled(False)
            self.execute_slewcal_only.setToolTip(msg)
        elif value == 'No':
            self.scriptstop_value.setStyleSheet("color:green")
            self.scriptstop_btn.setText('Request Script STOP')
            self.executeOB.setEnabled(True)
            self.executeOB.setToolTip(self.executeOB_tooltip)
            self.executeOB_slewcal.setEnabled(True)
            self.executeOB_slewcal.setToolTip(self.executeOB_slewcal_tooltip)
            self.execute_slewcal_only.setEnabled(True)
            self.execute_slewcal_only.setToolTip(self.execute_slewcal_only_tooltip)

    def set_scriptstop(self, value):
        self.log.debug(f'button clicked set_scriptstop: {value}')
        current_kw_value = self.kpfconfig['SCRIPTSTOP'].read()
        if current_kw_value == 'Yes':
            self.kpfconfig['SCRIPTSTOP'].write('No')
            self.scriptstop_btn.setText('CLEAR STOP')
        elif current_kw_value == 'No':
            self.kpfconfig['SCRIPTSTOP'].write('Yes')
            self.scriptstop_btn.setText('Request Script STOP')

    def do_fullstop(self, value):
        self.log.warning(f"button clicked do_fullstop: {value}")
        fullstop_popup = QMessageBox()
        fullstop_popup.setWindowTitle('Full Stop Confirmation')
        msg = ["Do you wish to stop the current exposure and script?",
               "",
               "The current exposure will read out then script cleanup will take place."]
        fullstop_popup.setText("\n".join(msg))
        fullstop_popup.setIcon(QMessageBox.Critical)
        fullstop_popup.setStandardButtons(QMessageBox.No | QMessageBox.Yes) 
        fullstop_popup.buttonClicked.connect(self.fullstop_popup_clicked)
        fullstop_popup.exec_()

    def fullstop_popup_clicked(self, i):
        self.log.debug(f"fullstop_popup_clicked: {i.text()}")
        if i.text() == '&Yes':
            # Set SCRIPTSTOP
            self.kpfconfig['SCRIPTSTOP'].write('Yes')
            self.log.warning(f"Sent kpfconfig.SCRIPTSTOP=Yes")
            # Stop current exposure
            if self.kpfexpose['EXPOSE'].read() == 'InProgress':
                self.kpfexpose['EXPOSE'].write('End')
                self.log.warning(f"Sent kpfexpose.EXPOSE=End")
                self.log.debug('Waiting for kpfexpose.EXPOSE to be Readout')
                readout = self.kpfexpose['EXPOSE'].waitFor("=='Readout'", timeout=10)
                self.log.debug(f"Reached readout? {readout}")
        else:
            self.log.debug('Confirmation is no, not stopping script')

    # Slew Cal Timer
    def update_slewcaltime_value(self, value):
        '''Updates value in QLabel and sets color'''
#         self.log.debug(f'update_slewcaltime_value: {value}')
        value = float(value)
        self.slewcaltime_value.setText(f"{value:.1f} hrs")
        if value < self.good_slew_cal_time:
            self.slewcaltime_value.setStyleSheet("color:green")
        elif value >= self.good_slew_cal_time and value <= self.bad_slew_cal_time:
            self.slewcaltime_value.setStyleSheet("color:orange")
        elif value > self.bad_slew_cal_time:
            self.slewcaltime_value.setStyleSheet("color:red")

    # Slew cal request
    def update_slewcalreq_value(self, value):
        '''Set label text and set color'''
        self.log.debug(f'update_slewcalreq_value: {value}')
        self.slewcalreq_value.setText(value)
        if value == 'Yes':
            self.slewcalreq_value.setStyleSheet("color:orange")
        elif value == 'No':
            self.slewcalreq_value.setStyleSheet("color:green")

    # Slew cal file
    def update_slewcalfile_value(self, value):
        self.log.debug(f'update_slewcalfile_value: {value}')
        output_text = f"{Path(value).name}"
        match_expected = re.match('SlewCal_(.+)\.yaml', output_text)
        if match_expected is not None:
            output_text = match_expected.group(1)
        self.slewcalfile_value.setText(output_text)

    def update_ca_hk_enabled(self, value):
        self.log.debug(f"update_ca_hk_enabled: {value}")
        if value in ['Yes', True]:
            if 'Ca_HK' in self.disabled_detectors:
                self.disabled_detectors.pop(self.disabled_detectors.index('Ca_HK'))
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
        if len(self.disabled_detectors) > 0:
            self.disabled_detectors_value.setText(",".join(self.disabled_detectors))
            self.disabled_detectors_value.setStyleSheet("color:red")

    ##-------------------------------------------
    ## Methods relating modifying OB fields
    ##-------------------------------------------
    def run_query_name(self):
        self.log.debug(f'run_query_name: {self.name_query_text}')

    def run_query_gaia(self):
        self.log.debug(f'run_query_gaia')
        # Will this query overwrite any values?
        target_OB_keys = ['2MASSID', 'Parallax', 'RadialVelocity',
                          'Gmag', 'Jmag', 'Teff']
        currently_used = [v for v in target_OB_keys if v in self.OB.keys()]
        if len(currently_used) > 0:
            overwrite_popup = QMessageBox()
            overwrite_popup.setWindowTitle('OB Data Overwrite Confirmation')
            msg = ("This query may overwrite data in the current OB.\n"
                   "Do you wish to continue and use Gaia catalog values?")
            overwrite_popup.setText(msg)
            overwrite_popup.setIcon(QMessageBox.Critical)
            overwrite_popup.setStandardButtons(QMessageBox.No | QMessageBox.Yes) 
            overwrite_popup.buttonClicked.connect(self.run_overwrite_popup_clicked)
            overwrite_popup.exec_()
        else:
            self.execute_query_gaia()

    def run_overwrite_popup_clicked(self, i):
        self.log.debug(f"run_overwrite_popup_clicked: {i.text()}")
        if i.text() == '&Yes':
            self.execute_query_gaia()
        else:
            print('Skipping Gaia query')

    def execute_query_gaia(self):
        self.log.debug(f"execute_query_gaia: {self.gaia_query_text}")
        # Perform Query and Update OB
        gaiaid = self.gaia_query_text
        self.update_OB('GaiaID', gaiaid)
        if len(gaiaid.split(' ')) == 2:
            gaiaid = gaiaid.split(' ')[1]
        self.target_names = BuildOBfromQuery.get_names_from_gaiaid(gaiaid)
        if self.target_names is None:
            self.log.error(f'Failed to retrieve target names using {gaiaid}')
            self.GaiaID.setToolTip(f'Failed to retrieve target names using {gaiaid}')
            return
        else:
            for key in ['TargetName', '2MASSID']:
                self.update_OB(key, self.target_names[key])
            self.log.debug(f"other names: {self.target_names['all']}")
            self.other_names.setText(', '.join(self.target_names['all']))
            self.TargetName.setToolTip(', '.join(self.target_names['all']))
            self.GaiaID.setToolTip(', '.join(self.target_names['all']))
        self.twomass_params = BuildOBfromQuery.get_Jmag(self.target_names['2MASSID'])
        if self.twomass_params is not None:
            for key in self.twomass_params:
                self.update_OB(key, self.twomass_params[key])
        self.gaia_params = BuildOBfromQuery.get_gaia_parameters(gaiaid)
        if self.gaia_params is not None:
            for key in self.gaia_params:
                self.update_OB(key, self.gaia_params[key])
        self.form_star_list_line()

    def set_name_query_input(self, value):
        value = value.strip()
        self.name_query_input = value

    def set_gaia_query_input(self, value):
        value = value.strip()
        self.gaia_query_text = value

    def set_gaia_id(self, value):
        value = str(value)
        value = value.strip()
        self.log.debug(f"set_gaia_id: {value}")
        includes_prefix = re.match('DR3 (\d+)', value)
        if includes_prefix is not None:
            value = includes_prefix.group(1)
        self.update_OB('GaiaID', f"DR3 {value}")
        self.GaiaID.setText(f"DR3 {value}")

    def set_target_name(self, value):
        self.log.debug(f"set_target_name: {value}")
        self.update_OB('TargetName', value)
        self.TargetName.setText(f"{value}")

    def set_guide_mode(self, value):
        self.log.debug(f"set_guide_mode: {value}")
        self.update_OB('GuideMode', value)

    def set_guide_gain(self, value):
        self.log.debug(f"set_guide_gain: {value}")
        self.update_OB('GuideCamGain', value)

    def set_fps(self, value):
        self.log.debug(f"set_fps: {value}")
        self.update_OB('GuideFPS', value)

    def set_object(self, value):
        self.log.debug(f"set_object: {value}")
        self.update_OB('Object', value)

    def set_nExp(self, value):
        self.log.debug(f"set_nExp: {value}")
        self.update_OB('nExp', value)

    def set_exptime(self, value):
        self.log.debug(f"set_exptime: {value}")
        self.update_OB('ExpTime', value)

    def set_expmeter_mode(self, value):
        self.log.debug(f"set_expmeter_mode: {value}")
        self.update_OB('ExpMeterMode', value)

    def set_expmeter_exptime(self, value):
        self.log.debug(f"set_expmeter_exptime: {value}")
        self.update_OB('ExpMeterExpTime', value)

    def set_CalND1(self, value):
        self.log.debug(f"set_CalND1: {value}")
        self.update_OB('CalND1', value)

    def set_CalND2(self, value):
        self.log.debug(f"set_CalND2: {value}")
        self.update_OB('CalND2', value)

    # Handle Checkboxes
    def TriggerCaHK_state_change(self, value):
        self.log.debug(f"TriggerCaHK_state_change: {value}")
        self.update_OB('TriggerCaHK', (value == 2))

    def TriggerGreen_state_change(self, value):
        self.log.debug(f"TriggerGreen_state_change: {value}")
        self.update_OB('TriggerGreen', (value == 2))

    def TriggerRed_state_change(self, value):
        self.log.debug(f"TriggerRed_state_change: {value}")
        self.update_OB('TriggerRed', (value == 2))

    def AutoEMExpTime_state_change(self, value):
        self.log.debug(f"AutoEMExpTime_state_change: {value}")
        self.update_OB('AutoExpMeter', (value == 2))

    def TakeSimulCal_state_change(self, value):
        self.log.debug(f"TakeSimulCal_state_change: {value}")
        self.update_OB('TakeSimulCal', (value == 2))

    def AutoNDFilters_state_change(self, value):
        self.log.debug(f"AutoNDFilters_state_change: {value}")
        self.update_OB('AutoNDFilters', (value == 2))

    def update_OB(self, key, value):
        self.log.debug(f"update_OB: {key} = {value}")
        seq_keys = ['Object', 'nExp', 'ExpTime', 'ExpMeterMode',
                    'AutoExpMeter', 'ExpMeterExpTime', 'TakeSimulCal',
                    'AutoNDFilters', 'CalND1', 'CalND2']
        if key in seq_keys:
            self.OB['SEQ_Observations'][0][key] = value
        else:
            self.OB[key] = value

        if key == 'TargetName':
            self.OB[key] = f"{value}"
            self.TargetName.setText(f"{value}")
            self.form_star_list_line()
        elif key == 'GaiaID':
            self.GaiaID.setText(f"{value}")
        elif key == '2MASSID':
            self.twoMASSID.setText(f"{value}")
        elif key == 'Parallax':
            self.Parallax.setText(f"{value}")
        elif key == 'RadialVelocity':
            self.RadialVelocity.setText(f"{value}")
        elif key == 'Gmag':
            self.Gmag.setText(f"{value}")
        elif key == 'Jmag':
            self.Jmag.setText(f"{value}")
        elif key == 'Teff':
            self.Teff.setText(f"{value}")
        elif key == 'GuideMode':
            if value == False: value = 'off'
            self.GuideMode.setCurrentText(value)
            self.GuideCamGain.setEnabled((value not in ['auto', 'off']))
            self.GuideFPS.setEnabled((value not in ['auto', 'off']))
        elif key == 'GuideCamGain':
            self.GuideCamGain.setCurrentText(value)
        elif key == 'GuideFPS':
            self.GuideFPS.setText(f"{value}")
        elif key == 'TriggerCaHK':
            self.TriggerCaHK.setChecked(value)
            self.estimate_OB_duration()
        elif key == 'TriggerGreen':
            self.TriggerGreen.setChecked(value)
            self.estimate_OB_duration()
        elif key == 'TriggerRed':
            self.TriggerRed.setChecked(value)
            self.estimate_OB_duration()
        elif key == 'Object':
            self.ObjectEdit.setText(f"{value}")
        elif key == 'nExp':
            self.nExpEdit.setText(f"{value}")
            self.estimate_OB_duration()
        elif key == 'ExpTime':
            self.ExpTimeEdit.setText(f"{value}")
            self.estimate_OB_duration()
        elif key == 'ExpMeterMode':
            self.ExpMeterMode.setCurrentText(value)
        elif key == 'AutoExpMeter':
            self.ExpMeterExpTimeEdit.setEnabled(not value)
        elif key == 'ExpMeterExpTime':
            self.ExpMeterExpTimeEdit.setText(f"{float(value):.1f}")
        elif key == 'TakeSimulCal':
            self.TakeSimulCal.setChecked(value)
            self.TakeSimulCal.setText(f"{value}")
            auto_nd = self.OB['SEQ_Observations'][0].get('AutoNDFilters', False)
            self.CalND1.setEnabled(value and not auto_nd)
            self.CalND2.setEnabled(value and not auto_nd)
        elif key == 'AutoNDFilters':
            self.CalND1.setEnabled(value)
            self.CalND2.setEnabled(value)
        elif key == 'CalND1':
            self.CalND1.setCurrentText(value)
        elif key == 'CalND2':
            self.CalND2.setCurrentText(value)


    ##-------------------------------------------
    ## Methods relating to importing or exporting OB
    ##-------------------------------------------
    def verify_OB(self):
        self.log.error('verify_OB Not implemented')

    def run_write_to_file(self):
        self.log.debug(f"run_write_to_file")
        result = QFileDialog.getSaveFileName(self, 'Save File',
                                             f"{self.file_path}",
                                             "OB Files (*yaml);;All Files (*)")
        if result:
            save_file = result[0]
            if save_file != '':
                # save fname as path to use in future
                self.file_path = Path(save_file).parent
                self.write_to_this_file(save_file)

    def write_to_this_file(self, save_file):
        self.log.debug(f"write_to_this_file: {save_file}")
        lines = BuildOBfromQuery.OBdict_to_lines(self.OB)
        with open(save_file, 'w') as f:
            for line in lines:
                f.write(line+'\n')

    def form_star_list_line(self):
        self.log.debug(f"form_star_list_line")
        if self.gaia_params is not None:
            starlist = BuildOBfromQuery.form_starlist_line(self.OB['TargetName'],
                                                           self.gaia_params['RA_ICRS'],
                                                           self.gaia_params['DE_ICRS'],
                                                           vmag=self.OB['Gmag']
                                                           )
            self.star_list_line.setText(starlist)
            return starlist
        else:
            msg = 'Unable to form star list line without Gaia coordinates'
            self.star_list_line.setText(msg)
            print(msg)
            return None

    def run_append_to_star_list(self):
        self.log.debug(f"run_append_to_star_list")
        if self.form_star_list_line() is None:
            # Don't bother with dialog if we can't form a star list entry
            return None
        result = QFileDialog.getSaveFileName(self, 'Star List File',
                                             f"{self.file_path}",
                                             "txt Files (*txt);;All Files (*)")
        if result:
            starlist_file = result[0]
            if starlist_file != '':
                # save fname as path to use in future
                starlist_file = Path(starlist_file)
                self.file_path = starlist_file.parent
                self.starlist_file_name = starlist_file.name
                self.append_to_starlist_file(starlist_file)

    def append_to_starlist_file(self, starlist_file):
        self.log.debug(f"append_to_starlist_file: {starlist_file}")
        line = self.form_star_list_line()
        if line is not None:
            with open(starlist_file, 'a') as f:
                f.write(line+'\n')

    def run_load_from_file(self):
        self.log.debug(f"run_load_from_file")
        result = QFileDialog.getOpenFileName(self, "Open OB File",
                                             f"{self.file_path}",
                                             "OB Files (*yaml);;All Files (*)")
        self.log.debug(f'  Got result: {result}')
        if result:
            fname = result[0]
            if fname != '' and Path(fname).exists():
                try:
                    self.log.debug(f"  Opening: {fname}")
                    with open(fname, 'r') as f:
                        contents = yaml.safe_load(f)
                    self.log.debug('  Read in YAML')
                    self.log.debug(contents)
                    for key in contents:
                        value = contents[key]
                        self.log.debug(f"  {key}: {value} ({type(value)})")
                        if key == 'GaiaID':
                            self.set_gaia_id(value)
                        elif key == 'SEQ_Observations':
                            for seq_key in value[0]:
                                seq_value = value[0][seq_key]
                                self.log.debug(f"  SEQ_Observations: {seq_key}: {seq_value} ({type(seq_value)})")
                                self.update_OB(seq_key, seq_value)
                        else:
                            self.update_OB(key, value)
                    # Re-run this last to make sure ND filters get greyed out or not properly
                    if 'TakeSimulCal' in contents['SEQ_Observations'][0].keys():
                        self.update_OB('TakeSimulCal', contents['SEQ_Observations'][0]['TakeSimulCal'])
                    if 'AutoExpMeter' in contents['SEQ_Observations'][0].keys():
                        self.update_OB('AutoExpMeter', contents['SEQ_Observations'][0]['AutoExpMeter'])
                    # save fname as path to use in future
                    self.file_path = Path(fname).parent
                    # Clear other names and star list line
                    self.other_names.setText('')
                    msg = 'Unable to form star list line without Gaia coordinates'
                    self.star_list_line.setText(msg)
                except Exception as e:
                    log.error(f"Unable to load file: {fname}")
                    log.error(f"{e}")
                    load_failed_popup = QMessageBox()
                    load_failed_popup.setWindowTitle('Unable to load file')
                    load_failed_popup.setText(f"Unable to load file\n{fname}")
                    load_failed_popup.setIcon(QMessageBox.Critical)
                    load_failed_popup.setStandardButtons(QMessageBox.Ok) 
                    load_failed_popup.exec_()

    def estimate_OB_duration(self):
        log.debug(f"Estimating OB duration")
        OB_for_calc = deepcopy(self.OB)
        OB_for_calc['SEQ_Observations'][0]['nExp'] = int(OB_for_calc['SEQ_Observations'][0]['nExp'])
        OB_for_calc['SEQ_Observations'][0]['ExpTime'] = float(OB_for_calc['SEQ_Observations'][0]['ExpTime'])
#         if len(OB_for_calc['SEQ_Darks']) > 2:
#             OB_for_calc['SEQ_Darks'] = OB_for_calc['SEQ_Darks'][:2]
#         if self.dark_seq2_enabled is False and len(OB_for_calc['SEQ_Darks']) == 2:
#             OB_for_calc['SEQ_Darks'].pop(1)
#         if self.dark_seq1_enabled is False and len(OB_for_calc['SEQ_Darks']) >= 1:
#             OB_for_calc['SEQ_Darks'].pop(0)
#         if self.cal_seq1_enabled is False and len(OB_for_calc['SEQ_Calibrations']) >= 1:
#             OB_for_calc['SEQ_Calibrations'].pop(0)
        duration = EstimateSciOBDuration.execute(OB_for_calc)
        self.OBDuration.setText(f"Estimated Duration: {duration/60:.0f} min")

    ##-------------------------------------------
    ## Execute an OB (with or without slewcal)
    ##-------------------------------------------
    def run_executeOB(self):
        self.log.debug(f"run_executeOB")
        run_executeOB_popup = QMessageBox()
        run_executeOB_popup.setWindowTitle('Run Science OB Confirmation')
        run_executeOB_popup.setText("Do you really want to execute the current OB?")
        run_executeOB_popup.setIcon(QMessageBox.Critical)
        run_executeOB_popup.setStandardButtons(QMessageBox.No | QMessageBox.Yes) 
        run_executeOB_popup.buttonClicked.connect(self.run_executeOB_popup_clicked)
        run_executeOB_popup.exec_()

    def run_executeOB_popup_clicked(self, i):
        self.log.debug(f"run_executeOB_popup_clicked: {i.text()}")
        if i.text() == '&Yes':
            print("Setting kpfconfig.SLEWCALREQ=No")
            self.kpfconfig['SLEWCALREQ'].write('No')
            time.sleep(0.1)
            print(f'Triggering RunSciOB')
            self.RunSciOB()
        else:
            print('Not executing OB')

    def run_executeOB_slewcal(self):
        self.log.debug(f"run_executeOB_slewcal")
        run_executeOB_slewcal_popup = QMessageBox()
        run_executeOB_slewcal_popup.setWindowTitle('Run Science OB Confirmation')
        run_executeOB_slewcal_popup.setText("Do you really want to execute the current OB?")
        run_executeOB_slewcal_popup.setIcon(QMessageBox.Critical)
        run_executeOB_slewcal_popup.setStandardButtons(QMessageBox.No | QMessageBox.Yes) 
        run_executeOB_slewcal_popup.buttonClicked.connect(self.run_executeOB_slewcal_popup_clicked)
        run_executeOB_slewcal_popup.exec_()

    def run_executeOB_slewcal_popup_clicked(self, i):
        self.log.debug(f"run_executeOB_slewcal_popup_clicked: {i.text()}")
        if i.text() == '&Yes':
            print("Setting kpfconfig.SLEWCALREQ=Yes")
            self.kpfconfig['SLEWCALREQ'].write('Yes')
            time.sleep(0.1)
            print(f'Triggering RunSciOB')
            self.RunSciOB()
        else:
            print('Not executing OB')

    def RunSciOB(self):
        self.log.debug(f"RunSciOB")
        self.verify_OB()

        # Write to temporary file
        utnow = datetime.datetime.utcnow()
        now_str = utnow.strftime('%Y%m%dat%H%M%S')
        date = utnow-datetime.timedelta(days=1)
        date_str = date.strftime('%Y%b%d').lower()
        tmp_file = Path(f'/s/sdata1701/KPFTranslator_logs/{date_str}/executedOB_{now_str}.yaml').expanduser()
        self.write_to_this_file(tmp_file)

#         RunSciOB_cmd = 'echo "Hello World" ; sleep 10'
        RunSciOB_cmd = f'kpfdo RunSciOB -f {tmp_file} ; echo "Done!" ; sleep 30'
        # Pop up an xterm with the script running
        cmd = ['xterm', '-title', 'RunSciOB', '-name', 'RunSciOB',
               '-fn', '10x20', '-bg', 'black', '-fg', 'white',
               '-e', f'{RunSciOB_cmd}']
        proc = subprocess.Popen(cmd)

    ##-------------------------------------------
    ## Execute a Slewcal Only
    ##-------------------------------------------
    def run_execute_slewcal_only(self):
        self.log.debug(f"run_executeOB")
        run_execute_slewcal_only_popup = QMessageBox()
        run_execute_slewcal_only_popup.setWindowTitle('Run Slew Cal Confirmation')
        msg = ["Do you really want to run a slew cal?",
               "",
               "This will take approximately a few minutes to complete",
               "and will block other operations during that time."]
        run_execute_slewcal_only_popup.setText("\n".join(msg))
        run_execute_slewcal_only_popup.setIcon(QMessageBox.Critical)
        run_execute_slewcal_only_popup.setStandardButtons(QMessageBox.No | QMessageBox.Yes) 
        run_execute_slewcal_only_popup.buttonClicked.connect(self.run_execute_slewcal_only_popup_clicked)
        run_execute_slewcal_only_popup.exec_()

    def run_execute_slewcal_only_popup_clicked(self, i):
        self.log.debug(f"run_execute_slewcal_only_popup_clicked: {i.text()}")
        if i.text() == '&Yes':
            self.log.info('Beginning slew cal')
            self.do_execute_slewcal_only()
        else:
            self.log.debug('Not executing slew cal')

    def do_execute_slewcal_only(self):
        self.log.debug(f"execute_slewcal_only")
        slewcal_file = self.kpfconfig['SLEWCALFILE'].read()
        execute_slewcal_only_cmd = f'kpfdo ExecuteSlewCal -f {slewcal_file} ; echo "Done!" ; sleep 20'
        self.log.debug(f'Executing: {execute_slewcal_only_cmd}')
        # Pop up an xterm with the script running
        cmd = ['xterm', '-title', 'ExecuteSlewCal', '-name', 'ExecuteSlewCal',
               '-fn', '10x20', '-bg', 'black', '-fg', 'white',
               '-e', f'{execute_slewcal_only_cmd}']
        proc = subprocess.Popen(cmd)


    ##-------------------------------------------
    ## Collect a Guider Cube
    ##-------------------------------------------
    def run_collect_guider_cube(self):
        self.log.debug(f"run_collect_guider_cube")
        run_collect_guider_cube_popup = QMessageBox()
        run_collect_guider_cube_popup.setWindowTitle('Run Collect Guider Cube Confirmation')
        msg = ["Do you really want to collect a guider cube?",
               "",
               "This will take approximately 1 minute to complete",
               "and will block other operations during that time."]
        run_collect_guider_cube_popup.setText("\n".join(msg))
        run_collect_guider_cube_popup.setIcon(QMessageBox.Critical)
        run_collect_guider_cube_popup.setStandardButtons(QMessageBox.No | QMessageBox.Yes) 
        run_collect_guider_cube_popup.buttonClicked.connect(self.run_collect_guider_cube_popup_clicked)
        run_collect_guider_cube_popup.exec_()

    def run_collect_guider_cube_popup_clicked(self, i):
        self.log.debug(f"run_collect_guider_cube_popup_clicked: {i.text()}")
        if i.text() == '&Yes':
            self.log.info('Beginning guide cube collection')
            self.do_collect_guider_cube()
        else:
            self.log.debug('Not executing guide cube collection')

    def do_collect_guider_cube(self):
        self.log.debug(f"collect_guider_cube")
        collect_guider_cube_cmd = f'kpfdo TakeGuiderCube 30 ; echo "Done!" ; sleep 10'
        # Pop up an xterm with the script running
        cmd = ['xterm', '-title', 'TakeGuiderCube', '-name', 'TakeGuiderCube',
               '-fn', '10x20', '-bg', 'black', '-fg', 'white',
               '-e', f'{collect_guider_cube_cmd}']
        proc = subprocess.Popen(cmd)
        targname = kpt.cache('dcs1', 'TARGNAME')
        SendEmail.execute({'To': 'jwalawender@keck.hawaii.edu',
                           'Subject': f"TakeGuiderCube executed",
                           'Message': f"TARGNAME={targname.read()}"})

    ##----------------------
    ## Methods related to Calibration OB tab
    ##----------------------
    def TriggerCaHK_cal_state_change(self, value):
        self.log.debug(f"TriggerCaHK_cal_state_change: {value}")
        self.update_calOB('TriggerCaHK', (value == 2))

    def TriggerGreen_cal_state_change(self, value):
        self.log.debug(f"TriggerGreen_cal_state_change: {value}")
        self.update_calOB('TriggerGreen', (value == 2))

    def TriggerRed_cal_state_change(self, value):
        self.log.debug(f"TriggerRed_cal_state_change: {value}")
        self.update_calOB('TriggerRed', (value == 2))

    def TriggerExpMeter_cal_state_change(self, value):
        self.log.debug(f"TriggerExpMeter_cal_state_change: {value}")
        self.update_calOB('TriggerExpMeter', (value == 2))

    def enable_dark_seq1_state_change(self, value):
        self.log.debug(f"enable_dark_seq1_state_change: {value} {type(value)}")
        self.dark_seq1_enabled = (int(value) == 2)
        self.enable_dark_seq1.setChecked(self.dark_seq1_enabled)
        self.Object_dark_seq1.setEnabled(int(value) == 2)
        self.Object_dark_seq1_label.setEnabled(int(value) == 2)
        self.Object_dark_seq1_note.setEnabled(int(value) == 2)
        self.nExp_dark_seq1.setEnabled(int(value) == 2)
        self.nExp_dark_seq1_label.setEnabled(int(value) == 2)
        self.nExp_dark_seq1_note.setEnabled(int(value) == 2)
        self.ExpTime_dark_seq1.setEnabled(int(value) == 2)
        self.ExpTime_dark_seq1_label.setEnabled(int(value) == 2)
        self.ExpTime_dark_seq1_note.setEnabled(int(value) == 2)
        self.estimate_calOB_duration()

    def set_Object_dark_seq1(self, value):
        self.log.debug(f"set_Object_dark_seq1: {value}")
        self.update_calOB('dark1_Object', value)

    def set_nExp_dark_seq1(self, value):
        self.log.debug(f"set_nExp_dark_seq1: {value}")
        self.update_calOB('dark1_nExp', value)

    def set_ExpTime_dark_seq1(self, value):
        self.log.debug(f"set_ExpTime_dark_seq1: {value}")
        self.update_calOB('dark1_ExpTime', value)

    def enable_dark_seq2_state_change(self, value):
        self.log.debug(f"enable_dark_seq2_state_change: {value} {type(value)}")
        self.dark_seq2_enabled = (int(value) == 2)
        self.enable_dark_seq2.setChecked(self.dark_seq2_enabled)
        self.Object_dark_seq2.setEnabled(int(value) == 2)
        self.Object_dark_seq2_label.setEnabled(int(value) == 2)
        self.Object_dark_seq2_note.setEnabled(int(value) == 2)
        self.nExp_dark_seq2.setEnabled(int(value) == 2)
        self.nExp_dark_seq2_label.setEnabled(int(value) == 2)
        self.nExp_dark_seq2_note.setEnabled(int(value) == 2)
        self.ExpTime_dark_seq2.setEnabled(int(value) == 2)
        self.ExpTime_dark_seq2_label.setEnabled(int(value) == 2)
        self.ExpTime_dark_seq2_note.setEnabled(int(value) == 2)
        self.estimate_calOB_duration()

    def set_Object_dark_seq2(self, value):
        self.log.debug(f"set_Object_dark_seq2: {value}")
        self.update_calOB('dark2_Object', value)

    def set_nExp_dark_seq2(self, value):
        self.log.debug(f"set_nExp_dark_seq2: {value}")
        self.update_calOB('dark2_nExp', value)

    def set_ExpTime_dark_seq2(self, value):
        self.log.debug(f"set_ExpTime_dark_seq2: {value}")
        self.update_calOB('dark2_ExpTime', value)

    def enable_cal_seq1_state_change(self, value):
        self.log.debug(f"enable_cal_seq1_state_change: {value} {type(value)}")
        self.cal_seq1_enabled = (int(value) == 2)
        self.enable_cal_seq1.setChecked(self.cal_seq1_enabled)
        self.Object_cal_seq1.setEnabled(int(value) == 2)
        self.Object_cal_seq1_label.setEnabled(int(value) == 2)
        self.Object_cal_seq1_note.setEnabled(int(value) == 2)
        self.CalSource_cal_seq1.setEnabled(int(value) == 2)
        self.CalSource_cal_seq1_label.setEnabled(int(value) == 2)
        self.CalND1_cal_seq1.setEnabled(int(value) == 2)
        self.CalND1_cal_seq1_label.setEnabled(int(value) == 2)
        self.CalND2_cal_seq1.setEnabled(int(value) == 2)
        self.CalND2_cal_seq1_label.setEnabled(int(value) == 2)
        self.nExp_cal_seq1.setEnabled(int(value) == 2)
        self.nExp_cal_seq1_label.setEnabled(int(value) == 2)
        self.nExp_cal_seq1_note.setEnabled(int(value) == 2)
        self.ExpTime_cal_seq1.setEnabled(int(value) == 2)
        self.ExpTime_cal_seq1_label.setEnabled(int(value) == 2)
        self.ExpTime_cal_seq1_note.setEnabled(int(value) == 2)
        self.SSS_Science_cal_seq1.setEnabled(int(value) == 2)
        self.SSS_Science_cal_seq1_label.setEnabled(int(value) == 2)
        self.SSS_Sky_cal_seq1.setEnabled(int(value) == 2)
        self.SSS_Sky_cal_seq1_label.setEnabled(int(value) == 2)
        self.TakeSimulCal_cal_seq1.setEnabled(int(value) == 2)
        self.TakeSimulCal_cal_seq1_label.setEnabled(int(value) == 2)
        self.FF_FiberPos_cal_seq1.setEnabled(int(value) == 2)
        self.FF_FiberPos_cal_seq1_label.setEnabled(int(value) == 2)
        self.ExpMeterExpTime_cal_seq1.setEnabled(int(value) == 2)
        self.ExpMeterExpTime_cal_seq1_label.setEnabled(int(value) == 2)
        self.estimate_calOB_duration()

    def set_Object_cal_seq1(self, value):
        self.log.debug(f"set_Object_cal_seq1: {value}")
        self.update_calOB('cal1_Object', value)

    def set_CalSource_cal_seq1(self, value):
        self.log.debug(f"set_CalSource_cal_seq1: {value}")
        self.update_calOB('cal1_CalSource', value)

    def set_CalND1_cal_seq1(self, value):
        self.log.debug(f"set_CalND1_cal_seq1: {value}")
        self.update_calOB('cal1_CalND1', value)

    def set_CalND2_cal_seq1(self, value):
        self.log.debug(f"set_CalND2_cal_seq1: {value}")
        self.update_calOB('cal1_CalND2', value)

    def set_nExp_cal_seq1(self, value):
        self.log.debug(f"set_nExp_cal_seq1: {value}")
        self.update_calOB('cal1_nExp', value)

    def set_ExpTime_cal_seq1(self, value):
        self.log.debug(f"set_ExpTime_cal_seq1: {value}")
        self.update_calOB('cal1_ExpTime', value)

    def SSS_Science_cal_seq1_state_change(self, value):
        self.log.debug(f"SSS_Science_cal_seq1_state_change: {value}")
        self.update_calOB('cal1_SSS_Science', (value == 2))

    def SSS_Sky_cal_seq1_state_change(self, value):
        self.log.debug(f"SSS_Sky_cal_seq1_state_change: {value}")
        self.update_calOB('cal1_SSS_Sky', (value == 2))

    def TakeSimulCal_cal_seq1_state_change(self, value):
        self.log.debug(f"TakeSimulCal_cal_seq1_state_change: {value}")
        self.update_calOB('cal1_TakeSimulCal', (value == 2))

    def set_FF_FiberPos_cal_seq1(self, value):
        self.log.debug(f"set_FF_FiberPos_cal_seq1: {value}")
        self.update_calOB('cal1_FF_FiberPos', value)

    def set_ExpMeterExpTime_cal_seq1(self, value):
        self.log.debug(f"set_ExpMeterExpTime_cal_seq1: {value}")
        self.update_calOB('cal1_ExpMeterExpTime', value)

    def update_calOB(self, key, value):
        self.log.debug(f"update_calOB: {key} = {value}")
        dark_seq_keys = ['dark1_Object', 'dark1_nExp', 'dark1_ExpTime',
                         'dark2_Object', 'dark2_nExp', 'dark2_ExpTime']
        cal_seq_keys = ['cal1_CalSource', 'cal1_Object', 'cal1_CalND1',
                        'cal1_CalND2', 'cal1_nExp', 'cal1_ExpTime',
                        'cal1_SSS_Science', 'cal1_SSS_Sky', 'cal1_TakeSimulCal',
                        'cal1_FF_FiberPos', 'cal1_ExpMeterExpTime']
        if key in dark_seq_keys:
            keyid = int(key[4])
            darkkey = key[6:]
            self.log.debug(f"  SEQ_Darks[{keyid-1}]: {darkkey} = {value}")
            if len(self.calOB['SEQ_Darks']) < keyid+1:
                self.calOB['SEQ_Darks'].append({})
            if keyid == 1 and darkkey == 'Object':
                self.Object_dark_seq1.setText(f"{value}")
                self.calOB['SEQ_Darks'][keyid-1][darkkey] = value
            elif keyid == 1 and darkkey == 'nExp':
                self.nExp_dark_seq1.setText(f"{value}")
                try:
                    int_val = int(value)
                except:
                    int_val = 0
                self.calOB['SEQ_Darks'][keyid-1][darkkey] = int_val
            elif keyid == 1 and darkkey == 'ExpTime':
                self.ExpTime_dark_seq1.setText(f"{value}")
                try:
                    float_val = float(value)
                except:
                    float_val = 0
                self.calOB['SEQ_Darks'][keyid-1][darkkey] = float_val
            elif keyid == 2 and darkkey == 'Object':
                self.Object_dark_seq2.setText(f"{value}")
                self.calOB['SEQ_Darks'][keyid-1][darkkey] = value
            elif keyid == 2 and darkkey == 'nExp':
                self.nExp_dark_seq2.setText(f"{value}")
                try:
                    int_val = int(value)
                except:
                    int_val = 0
                self.calOB['SEQ_Darks'][keyid-1][darkkey] = int_val
            elif keyid == 2 and darkkey == 'ExpTime':
                self.ExpTime_dark_seq2.setText(f"{value}")
                try:
                    float_val = float(value)
                except:
                    float_val = 0
                self.calOB['SEQ_Darks'][keyid-1][darkkey] = float_val
            else:
                self.calOB['SEQ_Darks'][keyid-1][darkkey] = value
        elif key in cal_seq_keys:
            keyid = int(key[3])
            calkey = key[5:]
            self.log.debug(f"  SEQ_Calibrations[{keyid-1}]: {calkey} = {value}")
            if keyid == 1 and calkey == 'Object':
                self.Object_cal_seq1.setText(f"{value}")
                self.calOB['SEQ_Calibrations'][keyid-1][calkey] = value
            elif keyid == 1 and calkey == 'CalSource':
                self.CalSource_cal_seq1.setCurrentText(f"{value}")
                self.FF_FiberPos_cal_seq1.setEnabled(value == 'WideFlat')
                self.FF_FiberPos_cal_seq1_label.setEnabled(value == 'WideFlat')
                if value.upper() in self.lamps_that_need_warmup:
                    self.warm_up_warning.setText('Requires warm up')
                    self.warm_up_warning.setStyleSheet("color:orange")
                else:
                    self.warm_up_warning.setText('')
                    self.warm_up_warning.setStyleSheet("color:black")
                self.calOB['SEQ_Calibrations'][keyid-1][calkey] = value
            elif keyid == 1 and calkey == 'CalND1':
                self.CalND1_cal_seq1.setCurrentText(f"{value}")
                self.calOB['SEQ_Calibrations'][keyid-1][calkey] = value
            elif keyid == 1 and calkey == 'CalND2':
                self.CalND2_cal_seq1.setCurrentText(f"{value}")
                self.calOB['SEQ_Calibrations'][keyid-1][calkey] = value
            elif keyid == 1 and calkey == 'nExp':
                self.nExp_cal_seq1.setText(f"{value}")
                try:
                    int_val = int(value)
                except:
                    int_val = 0
                self.calOB['SEQ_Calibrations'][keyid-1][calkey] = int_val
            elif keyid == 1 and calkey == 'ExpTime':
                self.ExpTime_cal_seq1.setText(f"{value}")
                try:
                    float_val = float(value)
                except:
                    float_val = 0
                self.calOB['SEQ_Calibrations'][keyid-1][calkey] = float_val
            elif keyid == 1 and calkey == 'SSS_Science':
                self.SSS_Science_cal_seq1.setChecked(value)
                self.SSS_Science_cal_seq1.setText(f"{(value in [2, True])}")
                self.calOB['SEQ_Calibrations'][keyid-1][calkey] = value
            elif keyid == 1 and calkey == 'SSS_Sky':
                self.SSS_Sky_cal_seq1.setChecked(value)
                self.SSS_Sky_cal_seq1.setText(f"{(value in [2, True])}")
                self.calOB['SEQ_Calibrations'][keyid-1][calkey] = value
            elif keyid == 1 and calkey == 'TakeSimulCal':
                self.TakeSimulCal_cal_seq1.setChecked(value)
                self.TakeSimulCal_cal_seq1.setText(f"{(value in [2, True])}")
                self.calOB['SEQ_Calibrations'][keyid-1][calkey] = value
            elif keyid == 1 and calkey == 'ExpMeterExpTime':
                self.ExpMeterExpTime_cal_seq1.setText(f"{value}")
                try:
                    float_val = float(value)
                except:
                    float_val = 0
                self.calOB['SEQ_Calibrations'][keyid-1][calkey] = float_val
            else:
                self.calOB['SEQ_Calibrations'][keyid-1][calkey] = value
        else:
            self.calOB[key] = value

        if key == 'TriggerCaHK':
            self.TriggerCaHK_cal.setChecked(value)
        elif key == 'TriggerGreen':
            self.TriggerGreen_cal.setChecked(value)
        elif key == 'TriggerRed':
            self.TriggerRed_cal.setChecked(value)
        elif key == 'TriggerExpMeter':
            self.TriggerExpMeter_cal.setChecked(value)
            self.ExpMeterExpTime_cal_seq1.setEnabled(value)
            self.ExpMeterExpTime_cal_seq1_label.setEnabled(value)
            self.ExpMeterExpTime_cal_seq1_note.setEnabled(value)

        if key not in ['dark1_Object', 'dark2_Object', 'cal1_Object',
                       'cal1_CalND1', 'cal1_CalND2', 'cal1_FF_FiberPos',
                       'cal1_ExpMeterExpTime', 'cal1_SSS_Science',
                       'cal1_SSS_Sky', 'cal1_TakeSimulCal']:
            self.estimate_calOB_duration()

    def estimate_calOB_duration(self):
        log.debug(f"Estimating OB duration")
        OB_for_calc = deepcopy(self.calOB)
        if len(OB_for_calc['SEQ_Darks']) > 2:
            OB_for_calc['SEQ_Darks'] = OB_for_calc['SEQ_Darks'][:2]
        if self.dark_seq2_enabled is False and len(OB_for_calc['SEQ_Darks']) == 2:
            OB_for_calc['SEQ_Darks'].pop(1)
        if self.dark_seq1_enabled is False and len(OB_for_calc['SEQ_Darks']) >= 1:
            OB_for_calc['SEQ_Darks'].pop(0)
        if self.cal_seq1_enabled is False and len(OB_for_calc['SEQ_Calibrations']) >= 1:
            OB_for_calc['SEQ_Calibrations'].pop(0)
        duration = EstimateCalOBDuration.execute(OB_for_calc)
        self.CalOBDuration.setText(f"Estimated Duration: {duration/60:.0f} min")

    def calOB_to_lines(self):
        lines = [f"# Built using KPF OB GUI tool",
                 f"Template_Name: kpf_cal",
                 f"Template_Version: 0.6",
                 f"",
                 f"TriggerCaHK: {self.calOB.get('TriggerCaHK')}",
                 f"TriggerGreen: {self.calOB.get('TriggerGreen')}",
                 f"TriggerRed: {self.calOB.get('TriggerRed')}",
                 f"TriggerExpMeter: {self.calOB.get('TriggerExpMeter')}"]
        if self.dark_seq1_enabled or self.dark_seq2_enabled:
            lines.append("SEQ_Darks:")
        if self.dark_seq1_enabled and 'SEQ_Darks' in self.calOB.keys():
            if len(self.calOB['SEQ_Darks']) > 0:
                print(self.calOB['SEQ_Darks'][0])
                lines.append(f"- Object: {self.calOB['SEQ_Darks'][0].get('Object')}")
                lines.append(f"  nExp: {self.calOB['SEQ_Darks'][0].get('nExp')}")
                lines.append(f"  ExpTime: {self.calOB['SEQ_Darks'][0].get('ExpTime')}")
        if self.dark_seq2_enabled and 'SEQ_Darks' in self.calOB.keys():
            print(len(self.calOB['SEQ_Darks']))
            if len(self.calOB['SEQ_Darks']) > 1:
                print(self.calOB['SEQ_Darks'][1])
                lines.append(f"- Object: {self.calOB['SEQ_Darks'][1].get('Object')}")
                lines.append(f"  nExp: {self.calOB['SEQ_Darks'][1].get('nExp')}")
                lines.append(f"  ExpTime: {self.calOB['SEQ_Darks'][1].get('ExpTime')}")
        if self.cal_seq1_enabled and 'SEQ_Calibrations' in self.calOB.keys():
            if len(self.calOB['SEQ_Calibrations']) > 0:
                cal_seq = [f"SEQ_Calibrations:",
                           f"- CalSource: {self.calOB['SEQ_Calibrations'][0].get('CalSource')}",
                           f"  Object: {self.calOB['SEQ_Calibrations'][0].get('Object')}",
                           f"  CalND1: {self.calOB['SEQ_Calibrations'][0].get('CalND1')}",
                           f"  CalND2: {self.calOB['SEQ_Calibrations'][0].get('CalND2')}",
                           f"  nExp: {self.calOB['SEQ_Calibrations'][0].get('nExp')}",
                           f"  ExpTime: {self.calOB['SEQ_Calibrations'][0].get('ExpTime')}",
                           f"  SSS_Science: {self.calOB['SEQ_Calibrations'][0].get('SSS_Science')}",
                           f"  SSS_Sky: {self.calOB['SEQ_Calibrations'][0].get('SSS_Sky')}",
                           f"  TakeSimulCal: {self.calOB['SEQ_Calibrations'][0].get('TakeSimulCal')}",
                           f"  FF_FiberPos: {self.calOB['SEQ_Calibrations'][0].get('FF_FiberPos')}",
                           f"  ExpMeterExpTime: {self.calOB['SEQ_Calibrations'][0].get('ExpMeterExpTime')}",
                           ]
                lines.extend(cal_seq)
        for line in lines:
            print(line)
        return lines

    def run_write_calOB_to_file(self):
        self.log.debug(f"run_write_calOB_to_file")
        result = QFileDialog.getSaveFileName(self, 'Save File',
                                             f"{self.file_path}",
                                             "OB Files (*yaml);;All Files (*)")
        if result:
            save_file = result[0]
            if save_file != '':
                # save fname as path to use in future
                self.file_path = Path(save_file).parent
                self.write_calOB_to_this_file(save_file)

    def write_calOB_to_this_file(self, save_file):
        self.log.debug(f"write_to_this_file: {save_file}")
        lines = self.calOB_to_lines()
        with open(save_file, 'w') as f:
            for line in lines:
                f.write(line+'\n')

    def run_load_calOB_from_file(self):
        self.log.debug(f"run_load_calOB_from_file")
        result = QFileDialog.getOpenFileName(self, "Open Cal OB File",
                                             f"{self.file_path}",
                                             "OB Files (*yaml);;All Files (*)")
        self.log.debug(f'  Got result: {result}')
        if result:
            fname = result[0]
            if fname != '' and Path(fname).exists():
                try:
                    self.log.debug(f"  Opening: {fname}")
                    with open(fname, 'r') as f:
                        contents = yaml.safe_load(f)
                    self.log.debug('  Read in YAML')
                    self.log.debug(contents)
                    if 'SEQ_Darks' in contents.keys():
                        nDark = len(contents['SEQ_Darks'])
                        self.enable_dark_seq1_state_change(2 if nDark > 0 else 0)
                        self.enable_dark_seq2_state_change(2 if nDark > 1 else 0)
                    else:
                        self.enable_dark_seq1_state_change(0)
                        self.enable_dark_seq2_state_change(0)
                    if 'SEQ_Calibrations' in contents.keys():
                        nCal = len(contents['SEQ_Calibrations'])
                        self.enable_cal_seq1_state_change(2 if nCal > 0 else 0)
                    else:
                        self.enable_cal_seq1_state_change(0)
                    for key in contents:
                        value = contents[key]
                        self.log.debug(f"  {key}: {value} ({type(value)})")
                        if key == 'SEQ_Darks':
                            if nDark == 1:
                                for seq_key in value[0]:
                                    seq_value = value[0][seq_key]
                                    self.log.debug(f"  SEQ_Darks1: {seq_key}: {seq_value} ({type(seq_value)})")
                                    self.update_calOB(f"dark1_{seq_key}", seq_value)
                            
                            if nDark == 2:
                                for seq_key in value[1]:
                                    seq_value = value[1][seq_key]
                                    self.log.debug(f"  SEQ_Darks2: {seq_key}: {seq_value} ({type(seq_value)})")
                                    self.update_calOB(f"dark2_{seq_key}", seq_value)
                        
                        if key == 'SEQ_Calibrations':
                            if nCal > 0:
                                self.cal_seq1_enabled = True
                                for cal_key in value[0]:
                                    cal_value = value[0][cal_key]
                                    self.log.debug(f"  SEQ_Calibrations: {cal_key}: {cal_value} ({type(cal_value)})")
                                    self.update_calOB(f"cal1_{cal_key}", cal_value)
                        else:
                            self.update_calOB(key, value)
                    # Re-run this last to make sure ND filters get greyed out or not properly
    #                 if 'TakeSimulCal' in contents['SEQ_Observations'][0].keys():
    #                     self.update_OB('TakeSimulCal', contents['SEQ_Observations'][0]['TakeSimulCal'])
    #                 if 'AutoExpMeter' in contents['SEQ_Observations'][0].keys():
    #                     self.update_OB('AutoExpMeter', contents['SEQ_Observations'][0]['AutoExpMeter'])
                    # save fname as path to use in future
                    self.file_path = Path(fname).parent
#                     self.calOB_to_lines()
                except Exception as e:
                    log.error(f"Unable to load file: {fname}")
                    log.error(f"{e}")
                    load_failed_popup = QMessageBox()
                    load_failed_popup.setWindowTitle('Unable to load file')
                    load_failed_popup.setText(f"Unable to load file\n{fname}")
                    load_failed_popup.setIcon(QMessageBox.Critical)
                    load_failed_popup.setStandardButtons(QMessageBox.Ok) 
                    load_failed_popup.exec_()


    def run_executecalOB(self):
        self.log.debug(f"run_executecalOB")
        run_executecalOB_popup = QMessageBox()
        run_executecalOB_popup.setWindowTitle('Run Calibration OB Confirmation')
        run_executecalOB_popup.setText("Do you really want to execute the current OB?")
        run_executecalOB_popup.setIcon(QMessageBox.Critical)
        run_executecalOB_popup.setStandardButtons(QMessageBox.No | QMessageBox.Yes) 
        run_executecalOB_popup.buttonClicked.connect(self.run_executecalOB_popup_clicked)
        run_executecalOB_popup.exec_()

    def run_executecalOB_popup_clicked(self, i):
        self.log.debug(f"run_executecalOB_popup_clicked: {i.text()}")
        if i.text() == '&Yes':
            print(f'Triggering RunCalOB')
            self.RunCalOB()
        else:
            print('Not executing OB')

    def RunCalOB(self):
        self.log.debug(f"RunCalOB")

        # Write to temporary file
        utnow = datetime.datetime.utcnow()
        now_str = utnow.strftime('%Y%m%dat%H%M%S')
        date = utnow-datetime.timedelta(days=1)
        date_str = date.strftime('%Y%b%d').lower()
        tmp_file = Path(f'/s/sdata1701/KPFTranslator_logs/{date_str}/executedOB_{now_str}.yaml').expanduser()
        self.write_calOB_to_this_file(tmp_file)

        RunCalOB_cmd = f'kpfdo RunCalOB -f {tmp_file} --nointensemon ; echo "Done!" ; sleep 30'
        # Pop up an xterm with the script running
        cmd = ['xterm', '-title', 'RunCalOB', '-name', 'RunCalOB',
               '-fn', '10x20', '-bg', 'black', '-fg', 'white',
               '-e', f'{RunCalOB_cmd}']
        proc = subprocess.Popen(cmd)




# end of class MainWindow


if __name__ == '__main__':
    log = create_GUI_log()
    log.info(f"Starting KPF OB GUI")
    status = main()
    log.info(f"Exiting KPF OB GUI: Status={status}")
    if status != 0:
        log.error(traceback.format_exc())
    sys.exit(status)

