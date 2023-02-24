#!/kroot/rel/default/bin/kpython3
import sys
import time
from pathlib import Path
import re
import subprocess
import yaml

import ktl                      # provided by kroot/ktl/keyword/python
import kPyQt                    # provided by kroot/kui/kPyQt
from PyQt5 import uic
from PyQt5.QtWidgets import (QApplication, QMainWindow,
                             QLabel, QPushButton, QLineEdit, QComboBox,
                             QCheckBox, QMessageBox, QFileDialog)

from kpf.utils import BuildOBfromQuery


def main():
    application = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.setupUi()
    main_window.show()
    return kPyQt.run(application)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        QMainWindow.__init__(self, *args, **kwargs)
        uic.loadUi('KPF_OB_GUI.ui', self)
        # Initial OB settings
        self.OB = {
                   'TriggerCaHK': True,
                   'TriggerGreen': True,
                   'TriggerRed': True,
                   'GuiderMode': 'auto',
                   'GuiderCamGain': 'high',
                   'GuiderFPS': 100,
                   'SEQ_Observations': [
                        {'Object': '',
                         'nExp': '1',
                         'Exptime': '10',
                         'ExpMeterMode': 'manual',
                         'AutoExpMeter': False,
                         'ExpMeterExpTime': '0.5', 
                         'TakeSimulCal': True,
                         'AutoNDFilters': False,
                         'CalND1': 'OD 0.1',
                         'CalND2': 'OD 0.1'},
                    ]
                   }
        # Keywords
        self.kpfconfig = ktl.cache('kpfconfig')
        self.kpflamps = ktl.cache('kpflamps')
        self.kpfexpose = ktl.cache('kpfexpose')
        # Slew Cal Time Colors/Warnings
        self.good_slew_cal_time = 1.0 # hours
        self.bad_slew_cal_time = 2.0 # hours


    def setupUi(self):
        self.setWindowTitle("KPF OB Builder")

        # script name
        self.scriptname_value = self.findChild(QLabel, 'scriptname_value')
        scriptname_kw = kPyQt.kFactory(self.kpfconfig['SCRIPTNAME'])
        scriptname_kw.stringCallback.connect(self.scriptname_value.setText)

        # script pause
        self.scriptpause_value = self.findChild(QLabel, 'scriptpause_value')
        scriptpause_kw = kPyQt.kFactory(self.kpfconfig['SCRIPTPAUSE'])
        scriptpause_kw.stringCallback.connect(self.update_scriptpause_value)

        self.scriptpause_btn = self.findChild(QPushButton, 'scriptpause_btn')
        self.scriptpause_btn.clicked.connect(self.set_scriptpause)

        # script stop
        self.scriptstop_value = self.findChild(QLabel, 'scriptstop_value')
        scriptstop_kw = kPyQt.kFactory(self.kpfconfig['SCRIPTSTOP'])
        scriptstop_kw.stringCallback.connect(self.update_scriptstop_value)

        self.scriptstop_btn = self.findChild(QPushButton, 'scriptstop_btn')
        self.scriptstop_btn.clicked.connect(self.set_scriptstop)

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
        self.slewcalreq_value = self.findChild(QLabel, 'slewcalreq_value')
        slewcalreq_kw = kPyQt.kFactory(self.kpfconfig['SLEWCALREQ'])
        slewcalreq_kw.stringCallback.connect(self.update_slewcalreq_value)

        # slew cal file
        self.slewcalfile_value = self.findChild(QLabel, 'slewcalfile_value')
        slewcalfile_kw = kPyQt.kFactory(self.kpfconfig['SLEWCALFILE'])
        slewcalfile_kw.stringCallback.connect(self.update_slewcalfile_value)

        ##----------------------
        ## Construct OB
        ##----------------------
        # Load OB from File
        self.load_from_file_btn = self.findChild(QPushButton, 'load_from_file_btn')
        self.load_from_file_btn.clicked.connect(self.run_load_from_file)

        # Generic Name Query

        # Gaia DR3 Query
        self.gaia_id_query_input = self.findChild(QLineEdit, 'gaia_id_query_input')
        self.gaia_id_query_input.textChanged.connect(self.set_gaia_id)

        self.query_gaia_btn = self.findChild(QPushButton, 'query_gaia_btn')
        self.query_gaia_btn.clicked.connect(self.run_query_gaia)

        ##----------------------
        ## Export or Execute OB
        ##----------------------
        self.write_to_file_btn = self.findChild(QPushButton, 'write_to_file_btn')
        self.write_to_file_btn.clicked.connect(self.run_write_to_file)

        self.executeOB = self.findChild(QPushButton, 'executeOB')
        self.executeOB.clicked.connect(self.run_executeOB)

        self.executeOB_slewcal = self.findChild(QPushButton, 'executeOB_slewcal')
        self.executeOB_slewcal.clicked.connect(self.run_executeOB_slewcal)

        ##----------------------
        ## OB Contents
        ##----------------------
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
        self.GuiderMode = self.findChild(QComboBox, 'GuiderMode')
        self.GuiderMode.addItems(["auto", "manual"])
        self.update_OB('GuiderMode', self.OB['GuiderMode'])
        self.GuiderMode.currentTextChanged.connect(self.set_guider_mode)
        
        self.GuiderCamGain = self.findChild(QComboBox, 'GuiderCamGain')
        self.GuiderCamGain.addItems(["high", "medium", "low"])
        self.update_OB('GuiderCamGain', self.OB['GuiderCamGain'])
        self.GuiderCamGain.currentTextChanged.connect(self.set_guider_gain)
        self.GuiderFPS = self.findChild(QLineEdit, 'GuiderFPS')
        self.update_OB('GuiderFPS', self.OB['GuiderFPS'])
        self.GuiderFPS.textChanged.connect(self.set_fps)
        if self.OB['GuiderMode'] == 'auto':
            self.GuiderFPS.setEnabled(False)

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

        self.ExptimeEdit = self.findChild(QLineEdit, 'ExptimeEdit')
        self.ExptimeEdit.textChanged.connect(self.set_exptime)
        self.update_OB('Exptime', self.OB['SEQ_Observations'][0]['Exptime'])

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


    ##-------------------------------------------
    ## Methods relating to updates from keywords
    ##-------------------------------------------
    # Expose Status
    def update_expose_status_value(self, value):
        '''Set label text and set color'''
        self.expose_status_value.setText(value)
        if value == 'Ready':
            self.expose_status_value.setStyleSheet("color:green")
        elif value in ['Start', 'InProgress', 'Readout']:
            self.expose_status_value.setStyleSheet("color:orange")

    # SCRIPTPAUSE
    def update_scriptpause_value(self, value):
        '''Set label text and set color'''
        print(f"Updating scriptpause label: {value}")
        self.scriptpause_value.setText(value)
        if value == 'Yes':
            self.scriptpause_value.setStyleSheet("color:orange")
            self.scriptpause_btn.setText('RESUME')
        elif value == 'No':
            self.scriptpause_value.setStyleSheet("color:green")
            self.scriptpause_btn.setText('PAUSE')

    def set_scriptpause(self, value):
        current_kw_value = self.kpfconfig['SCRIPTPAUSE'].read()
        if current_kw_value == 'Yes':
            self.kpfconfig['SCRIPTPAUSE'].write('No')
            self.scriptpause_btn.setText('PAUSE')
        elif current_kw_value == 'No':
            self.kpfconfig['SCRIPTPAUSE'].write('Yes')
            self.scriptpause_btn.setText('RESUME')

    # SCRIPTSTOP
    def update_scriptstop_value(self, value):
        '''Set label text and set color'''
        print(f"Updating scriptstop label: {value}")
        self.scriptstop_value.setText(value)
        if value == 'Yes':
            self.scriptstop_value.setStyleSheet("color:red")
            self.scriptstop_btn.setText('CLEAR STOP')
        elif value == 'No':
            self.scriptstop_value.setStyleSheet("color:green")
            self.scriptstop_btn.setText('STOP')

    def set_scriptstop(self, value):
        current_kw_value = self.kpfconfig['SCRIPTSTOP'].read()
        if current_kw_value == 'Yes':
            self.kpfconfig['SCRIPTSTOP'].write('No')
            self.scriptstop_btn.setText('CLEAR STOP')
        elif current_kw_value == 'No':
            self.kpfconfig['SCRIPTSTOP'].write('Yes')
            self.scriptstop_btn.setText('STOP')

    # Slew Cal Timer
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

    # Slew cal request
    def update_slewcalreq_value(self, value):
        '''Set label text and set color'''
        print(f"Updating slewcalreq value: {value}")
        self.slewcalreq_value.setText(value)
        if value == 'Yes':
            self.slewcalreq_value.setStyleSheet("color:orange")
        elif value == 'No':
            self.slewcalreq_value.setStyleSheet("color:green")

    # Slew cal file
    def update_slewcalfile_value(self, value):
        self.slewcalfile_value.setText(f"{Path(value).name}")

    ##-------------------------------------------
    ## Methods relating modifying OB fields
    ##-------------------------------------------
    def run_query_gaia(self):
        gaiaid = self.OB['GaiaID']
        if len(gaiaid.split(' ')) == 2:
            gaiaid = gaiaid.split(' ')[1]
        names = BuildOBfromQuery.get_names_from_gaiaid(gaiaid)
        if names is not None:
            for key in names:
                self.update_OB(key, names[key])
        twomass_params = BuildOBfromQuery.get_Jmag(names['2MASSID'])
        if twomass_params is not None:
            for key in twomass_params:
                self.update_OB(key, twomass_params[key])
        gaia_params = BuildOBfromQuery.get_gaia_parameters(gaiaid)
        if gaia_params is not None:
            for key in gaia_params:
                self.update_OB(key, gaia_params[key])
        self.OB_to_lines()

    def set_gaia_id(self, value):
        includes_prefix = re.match('DR3 (\d+)', value)
        print(value, includes_prefix)
        if includes_prefix is not None:
            value = includes_prefix.group(1)
        self.update_OB('GaiaID', f"DR3 {value}")
        self.GaiaID.setText(f"DR3 {value}")

    def set_target_name(self, value):
        self.update_OB('TargetName', value)
        self.TargetName.setText(f"{value}")

    def set_guider_mode(self, value):
        self.update_OB('GuiderMode', value)

    def set_guider_gain(self, value):
        self.update_OB('GuiderCamGain', value)

    def set_fps(self, value):
        self.update_OB('GuiderFPS', value)

    def set_object(self, value):
        self.update_OB('Object', value)

    def set_nExp(self, value):
        self.update_OB('nExp', value)

    def set_exptime(self, value):
        self.update_OB('Exptime', value)

    def set_expmeter_mode(self, value):
        self.update_OB('ExpMeterMode', value)

    def set_expmeter_exptime(self, value):
        self.update_OB('ExpMeterExpTime', value)

    def set_CalND1(self, value):
        self.update_OB('CalND1', value)

    def set_CalND2(self, value):
        self.update_OB('CalND2', value)

    # Handle Checkboxes
    def TriggerCaHK_state_change(self, value):
        self.update_OB('TriggerCaHK', (value == 2))

    def TriggerGreen_state_change(self, value):
        self.update_OB('TriggerGreen', (value == 2))

    def TriggerRed_state_change(self, value):
        self.update_OB('TriggerRed', (value == 2))

    def AutoEMExpTime_state_change(self, value):
        self.update_OB('AutoExpMeter', (value == 2))

    def TakeSimulCal_state_change(self, value):
        print(f"TakeSimulCal_state_change: {value}")
        self.update_OB('TakeSimulCal', (value == 2))

    def AutoNDFilters_state_change(self, value):
        self.update_OB('AutoNDFilters', (value == 2))

    def update_OB(self, key, value):
        print(f"Setting {key} = {value}")
        seq_keys = ['Object', 'nExp', 'Exptime', 'ExpMeterMode',
                    'AutoExpMeter', 'ExpMeterExpTime', 'TakeSimulCal',
                    'AutoNDFilters', 'CalND1', 'CalND2']
        if key in seq_keys:
            self.OB['SEQ_Observations'][0][key] = value
        else:
            self.OB[key] = value

        if key == 'TargetName':
            self.TargetName.setText(f"{value}")
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
        elif key == 'GuiderMode':
            self.GuiderCamGain.setEnabled((value != 'auto'))
            self.GuiderFPS.setEnabled((value != 'auto'))
        elif key == 'GuiderCamGain':
            self.GuiderCamGain.setCurrentText(value)
        elif key == 'GuiderFPS':
            self.GuiderFPS.setText(f"{value}")
        elif key == 'TriggerCaHK':
            self.TriggerCaHK.setChecked(value)
        elif key == 'TriggerGreen':
            self.TriggerGreen.setChecked(value)
        elif key == 'TriggerRed':
            self.TriggerRed.setChecked(value)
        elif key == 'Object':
            self.ObjectEdit.setText(f"{value}")
        elif key == 'nExp':
            self.nExpEdit.setText(f"{value}")
        elif key == 'Exptime':
            self.ExptimeEdit.setText(f"{float(value):.1f}")
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
        print('Not implemented')

    def OB_to_lines(self):
        obs = self.OB.get('SEQ_Observations')[0]
        OB = [f"# Built using KPF OB GUI tool",
              f"Template_Name: kpf_sci",
              f"Template_Version: 0.6",
              f"",
              f"# Target Info",
              f"TargetName: {self.OB.get('TargetName', '?')}",
              f"GaiaID: {self.OB.get('GaiaID', '?')}",
              f"2MASSID: {self.OB.get('2MASSID', '?')}",
              f"Parallax: {self.OB.get('Parallax', '?')}",
              f"RadialVelocity: {self.OB.get('RadialVelocity', '?')}",
              f"Gmag: {self.OB.get('Gmag', '?')}",
              f"Jmag: {self.OB.get('Jmag', '?')}",
              f"Teff: {self.OB.get('Teff', '?')}",
              f"",
              f"# Guider Setup",
              f"GuiderMode: {self.OB.get('GuiderMode', '?')}"]
        if self.OB.get('GuiderMode', None) != 'auto':
            OB.extend([
              f"GuiderCamGain: {self.OB.get('GuiderCamGain', '?')}",
              f"GuiderFPS: {self.OB.get('GuiderFPS', '?')}",
              ])
        OB.extend([
              f"",
              f"# Spectrograph Setup",
              f"TriggerCaHK: {self.OB.get('TriggerCaHK', '?')}",
              f"TriggerGreen: {self.OB.get('TriggerGreen', '?')}",
              f"TriggerRed: {self.OB.get('TriggerRed', '?')}",
              f"",
              f"# Observations (repeat the indented block below to take multiple observations,",
              f"SEQ_Observations:",
              f" - Object: {obs.get('Object', '?')}",
              f"   nExp: {obs.get('nExp', '?')}",
              f"   Exptime: {obs.get('Exptime', '?')}",
              f"   ExpMeterMode: {obs.get('ExpMeterMode', '?')}",
              f"   AutoExpMeter: {obs.get('AutoExpMeter', 'False')}",
              ])
        if obs.get('AutoExpMeter', False) != True:
            OB.extend([
              f"   ExpMeterExpTime: {obs.get('ExpMeterExpTime', '?')}",
              ])
        OB.extend([
              f"   TakeSimulCal: {obs.get('TakeSimulCal', '?')}",
              ])
        if obs.get('TakeSimulCal', None) == True:
            OB.extend([
              f"   AutoNDFilters: {obs.get('AutoNDFilters', '?')}",
              ])
            if obs.get('AutoNDFilters', None) != True:
                OB.extend([
                  f"   CalND1: {obs.get('CalND1', '?')}",
                  f"   CalND2: {obs.get('CalND2', '?')}",
                  ])
        for line in OB:
            print(line)
        print(self.OB)
        return OB

    def run_write_to_file(self):
        print('Not implemented')

    def run_load_from_file(self):
        result = QFileDialog.getOpenFileName(self, "Open OB File", "/s/starlists",
                             "YAML Files (*yaml);;All Files (*)")
        if result:
            fname = result[0]
            with open(fname, 'r') as f:
                contents = yaml.safe_load(f)
            for key in contents:
                if key == 'GaiaID':
                    value = contents[key]
                    print(f"{key}: {value} ({type(value)})")
                    self.set_gaia_id(value)
                elif key == 'SEQ_Observations':
                    for seq_key in contents[key][0]:
                        seq_value = contents[key][0][seq_key]
                        print(f"SEQ_Observations: {seq_key}: {seq_value} ({type(seq_value)})")
                        self.update_OB(seq_key, seq_value)
                else:
                    value = contents[key]
                    print(f"{key}: {value} ({type(value)})")
                    self.update_OB(key, value)



    ##-------------------------------------------
    ## Methods relating to executing an OB
    ##-------------------------------------------
    def run_executeOB(self):
        run_executeOB_popup = QMessageBox()
        run_executeOB_popup.setWindowTitle('Run Science OB Confirmation')
        run_executeOB_popup.setText("Do you really want to execute the current OB?")
        run_executeOB_popup.setIcon(QMessageBox.Critical)
        run_executeOB_popup.setStandardButtons(QMessageBox.No | QMessageBox.Yes) 
        run_executeOB_popup.buttonClicked.connect(self.run_executeOB_popup_clicked)
        run_executeOB_popup.exec_()

    def run_executeOB_popup_clicked(self, i):
        print(f"run_executeOB_popup_clicked: {i.text()}")
        if i.text() == '&Yes':
#             print("Setting kpfconfig.SLEWCALREQ=No")
#             self.kpfconfig['SLEWCALREQ'].write('No')
#             time.sleep(0.1)
            print(f'Triggering RunSciOB')
            self.RunSciOB()
        else:
            print('Not executing OB')

    def run_executeOB_slewcal(self):
        run_executeOB_slewcal_popup = QMessageBox()
        run_executeOB_slewcal_popup.setWindowTitle('Run Science OB Confirmation')
        run_executeOB_slewcal_popup.setText("Do you really want to execute the current OB?")
        run_executeOB_slewcal_popup.setIcon(QMessageBox.Critical)
        run_executeOB_slewcal_popup.setStandardButtons(QMessageBox.No | QMessageBox.Yes) 
        run_executeOB_slewcal_popup.buttonClicked.connect(self.run_executeOB_slewcal_popup_clicked)
        run_executeOB_slewcal_popup.exec_()

    def run_executeOB_slewcal_popup_clicked(self, i):
        print(f"run_executeOB_slewcal_popup_clicked: {i.text()}")
        if i.text() == '&Yes':
            print("Setting kpfconfig.SLEWCALREQ=Yes")
            self.kpfconfig['SLEWCALREQ'].write('Yes')
            time.sleep(0.1)
            print(f'Triggering RunSciOB')
            self.RunSciOB()
        else:
            print('Not executing OB')

    def RunSciOB(self):
        self.verify_OB()
        print('RunSciOB not implemented')
        RunSciOB_cmd = 'echo Hello World! ; sleep 10'
        cmd = ['xterm', '-title', 'RunSciOB', '-name', 'RunSciOB',
               '-fn', '10x20', '-bg', 'black', '-fg', 'white',
               '-e', f'{RunSciOB_cmd}']
        proc = subprocess.Popen(cmd)




# end of class MainWindow


if __name__ == '__main__':
    status = main()
    sys.exit(status)
