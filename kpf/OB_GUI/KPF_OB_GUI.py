#!/kroot/rel/default/bin/kpython3
import sys
import traceback
import time
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
from PyQt5.QtCore import Qt

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
#     logdir = Path(f'/s/sdata1701/KPFTranslator_logs/')
#     if logdir.exists() is False:
#         logdir.mkdir(mode=0o777, parents=True)
#     LogFileName = logdir / 'OB_GUI.log'
#     LogFileHandler = RotatingFileHandler(LogFileName,
#                                          maxBytes=100*1024*1024, # 100 MB
#                                          backupCount=1000) # Keep old files
#     LogFileHandler.setLevel(logging.DEBUG)
#     LogFileHandler.setFormatter(LogFormat)
#     log.addHandler(LogFileHandler)
    return log


##-------------------------------------------------------------------------
## Define Model for MVC
##-------------------------------------------------------------------------
class OBListModel(QtCore.QAbstractListModel):
    '''Model to hold the list of OBs that the observer will select from.
    '''
    def __init__(self, *args, OBs=[], **kwargs):
        super(OBListModel, self).__init__(*args, **kwargs)
        self.OBs = OBs
        self.start_times = None

    def data(self, index, role):
        if role == Qt.DisplayRole:
            if self.start_times is None:
                OB = self.OBs[index.row()]
                output_line = f"{str(OB):s}"
            else:
                OB = self.OBs[index.row()]
                start_time_decimal = self.start_times[index.row()]
                sthr = int(np.floor(start_time_decimal))
                stmin = (start_time_decimal-sthr)*60
                start_time_str = f"{sthr:02d}:{stmin:02.0f} UT"
                output_line = f"{start_time_str}  {str(OB):s}"
            if OB.edited == True:
                output_line += ' [edited]'
            return output_line
        if role == Qt.DecorationRole:
            OB  = self.OBs[index.row()]
            if OB.executed == True:
                return QtGui.QColor('black')
            else:
                return QtGui.QColor('green')

    def rowCount(self, index):
        return len(self.OBs)

    def sort(self, sortkey):
        if self.start_times is not None:
            zipped = [z for z in zip(self.start_times, self.OBs)]
            zipped.sort(key=lambda z: z[0])
            self.OBs = [z[1] for z in zipped]
            self.start_times = [z[0] for z in zipped]
        elif sortkey == 'Name':
            self.OBs.sort(key=lambda o: o[1].Target.TargetName.value, reverse=False)
        elif sortkey == 'RA':
            self.OBs.sort(key=lambda o: o[1].Target.coord.ra.deg, reverse=False)
        elif sortkey == 'Dec':
            self.OBs.sort(key=lambda o: o[1].Target.coord.dec.deg, reverse=False)
        elif sortkey == 'Gmag':
            self.OBs.sort(key=lambda o: o[1].Target.Gmag.value, reverse=False)
        elif sortkey == 'Jmag':
            self.OBs.sort(key=lambda o: o[1].Target.Jmag.value, reverse=False)


##-------------------------------------------------------------------------
## Scrollable QMessageBox
##-------------------------------------------------------------------------
class ScrollMessageBox(QtWidgets.QMessageBox):
    '''Custom message box to show the contents of an OB (as it would appear in
    a .yaml file on disk) in a scrollable window.
    '''
    def __init__(self, OB, *args, **kwargs):
        contents = OB.__repr__()
        QtWidgets.QMessageBox.__init__(self, *args, **kwargs)
        self.setStandardButtons(QtWidgets.QMessageBox.Close | QtWidgets.QMessageBox.Cancel)
        self.button(QtWidgets.QMessageBox.Cancel).setText("Edit OB")
        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        self.content = QtWidgets.QWidget()
        scroll.setWidget(self.content)
        lay = QtWidgets.QVBoxLayout(self.content)
        contents_label = QtWidgets.QLabel(contents, self)
        contents_label.setFont(QtGui.QFont('Courier New', 11))
        lay.addWidget(contents_label)
        self.layout().addWidget(scroll, 0, 0, 1, self.layout().columnCount())
        self.setStyleSheet("QScrollArea{min-width:350 px; min-height: 600px;}")


##-------------------------------------------------------------------------
## Editable QMessageBox
##-------------------------------------------------------------------------
class EditableMessageBox(QtWidgets.QMessageBox):
    '''Custom message box to edit the contents of an OB (as it would appear in
    a .yaml file on disk) in a scrollable window.
    '''
    def __init__(self, OB, *args, **kwargs):
        self.OB = OB
        self.OBlines_original = self.OB.__repr__()
        self.OBlines = self.OB.__repr__()
        self.newOB = None
        QtWidgets.QMessageBox.__init__(self, *args, **kwargs)
        self.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        wdgt = QtWidgets.QWidget()
        scroll.setWidget(wdgt)
        lay = QtWidgets.QVBoxLayout(wdgt)
        self.contents = QtWidgets.QPlainTextEdit(self.OBlines, self)
        self.contents.setFont(QtGui.QFont('Courier New', 11))
        self.contents.textChanged.connect(self.edit_OB)
        lay.addWidget(self.contents)
        self.layout().addWidget(scroll, 0, 0, 1, self.layout().columnCount())
        self.setStyleSheet("QScrollArea{min-width:350 px; min-height: 600px;}")

    def edit_OB(self):
        self.OBlines = self.contents.document().toPlainText()
        try:
            self.newOB = ObservingBlock(yaml.safe_load(self.OBlines))
            self.newOB.edited = True
            self.newOB.executed = self.OB.executed
        except:
            self.newOB = None


##-------------------------------------------------------------------------
## Observer Comment Dialog Box
##-------------------------------------------------------------------------
class ObserverCommentBox(QtWidgets.QDialog):
    '''Custom dialog box for observers to submit observer comments on an OB.
    '''
    def __init__(self, SOB, observer):
        super().__init__()
        self.SOB = SOB
        self.comment = ''
        self.observer = observer
        self.setWindowTitle("Observer Comment Form")
        layout = QtWidgets.QVBoxLayout()

        # Initial message lines
        lines = [f"Submit an observer comment for OB:",
                 f"{self.SOB.name()}",
                 ""]
        message = QtWidgets.QLabel("\n".join(lines))
        layout.addWidget(message)

        # Add observer field
        observer_label = QtWidgets.QLabel('Observer/Commenter:')
        layout.addWidget(observer_label)
        self.observer_field = QtWidgets.QLineEdit()
        self.observer_field.setText(self.observer)
        self.observer_field.textChanged.connect(self.edit_observer)
        layout.addWidget(self.observer_field)

        # Add comment field
        comment_label = QtWidgets.QLabel('Comment:')
        layout.addWidget(comment_label)
        self.comment_field = QtWidgets.QLineEdit()
        self.comment_field.textChanged.connect(self.edit_comment)
        layout.addWidget(self.comment_field)

        # Set up buttons
        QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

        # Wrap up definition of the ObserverCommentBox
        self.setLayout(layout)
        self.setStyleSheet("min-width:300 px;")

    def edit_comment(self, value):
        self.comment = value

    def edit_observer(self, value):
        self.observer = value


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


##-------------------------------------------------------------------------
## Define Application MainWindow
##-------------------------------------------------------------------------
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
        ui_file = Path(__file__).parent / 'KPF_OB_GUI.ui'
        uic.loadUi(f"{ui_file}", self)
        self.log = log
        self.log.debug('Initializing MainWindow')
        # Keywords
        self.dcs = 'dcs1'
        self.log.debug('Cacheing keyword services')
        self.DCS_AZ = ktl.cache(self.dcs, 'AZ')
        self.DCS_AZ.monitor()
        self.DCS_EL = ktl.cache(self.dcs, 'EL')
        self.DCS_EL.monitor()
        self.kpfconfig = ktl.cache('kpfconfig')
        self.red_acf_file_kw = kPyQt.kFactory(ktl.cache('kpfred', 'ACFFILE'))
        self.green_acf_file_kw = kPyQt.kFactory(ktl.cache('kpfgreen', 'ACFFILE'))
        # Selected OB
        self.SOBindex = 0
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

        # Program ID
        self.ProgID = self.findChild(QtWidgets.QComboBox, 'ProgID')
        self.ProgID.addItems(self.get_progIDs())
        self.ProgID.currentTextChanged.connect(self.set_ProgID)

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

        # Universal Time
        self.UTValue = self.findChild(QtWidgets.QLabel, 'UTValue')
        UT_kw = kPyQt.kFactory(ktl.cache(self.dcs, 'UT'))
        UT_kw.stringCallback.connect(self.update_UT)

        # Sidereal Time
        self.SiderealTimeValue = self.findChild(QtWidgets.QLabel, 'SiderealTimeValue')
        LST_kw = kPyQt.kFactory(ktl.cache(self.dcs, 'LST'))
        LST_kw.stringCallback.connect(self.update_LST)

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

        # List of Observing Blocks
        self.OBListHeader = self.findChild(QtWidgets.QLabel, 'OBListHeader')
        self.hdr = 'TargetName       RA          Dec         Gmag  Jmag  Observations'
        self.OBListHeader.setText(f"    {self.hdr}")

        self.ListOfOBs = self.findChild(QtWidgets.QListView, 'ListOfOBs')
        self.model = OBListModel(OBs=[])
        self.ListOfOBs.setModel(self.model)
        self.ListOfOBs.selectionModel().selectionChanged.connect(self.select_OB)

        # Sorting
        self.SortOBs = self.findChild(QtWidgets.QComboBox, 'SortOBs')
        self.SortOBs.addItems(['', 'Name', 'RA', 'Dec', 'Gmag', 'Jmag'])
        self.SortOBs.currentTextChanged.connect(self.sort_OB_list)

        # Weather Band
        self.WeatherBandLabel = self.findChild(QtWidgets.QLabel, 'WeatherBandLabel')
        self.WeatherBand = self.findChild(QtWidgets.QComboBox, 'WeatherBand')
        self.WeatherBand.addItems(['1', '2', '3'])
        self.WeatherBand.currentTextChanged.connect(self.set_weather_band)
        self.WeatherBand.setEnabled(False)
        self.WeatherBandLabel.setEnabled(False)

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
        self.SOB_ExecuteWithSlewCalButton = self.findChild(QtWidgets.QPushButton, 'SOB_ExecuteWithSlewCalButton')
        self.SOB_ExecuteWithSlewCalButton.clicked.connect(self.execute_with_slew_cal_SOB)


    ##-------------------------------------------
    ## Methods to display updates from keywords
    ##-------------------------------------------
    # Script Name
    def update_scriptname_value(self, value):
        '''Set label text and set color'''
        self.log.debug(f'update_scriptname_value: {value}')
        self.scriptname_value.setText(f"{value.strip('.py')}")
        if value in ['None', '']:
            self.scriptname_value.setStyleSheet("color:green")
        else:
            self.scriptname_value.setStyleSheet("color:orange")

    # Expose Status
    def update_expose_status_value(self, value):
        '''Set label text and set color'''
        self.log.debug(f'update_expose_status_value: {value}')
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


    ##-------------------------------------------
    ## Methods to get data from DB or Schedule
    ##-------------------------------------------
    def get_progIDs(self):
        progIDs = ['', 'KPF-CC']
        # Go get list of available program IDs for Instrument=KPF
        return progIDs + ['E123', 'E456', 'CPS 2024B']

    def set_ProgID(self, value):
        self.log.info(f"set_ProgID: '{value}'")
        self.clear_OB_selection()
        if value == '':
            self.OBListHeader.setText(hdr)
            self.model.OBs = []
            self.model.start_times = None
            self.model.layoutChanged.emit()
            self.SortOBs.setEnabled(False)
            self.SortOBsLabel.setEnabled(False)
            self.WeatherBand.setEnabled(False)
            self.WeatherBandLabel.setEnabled(False)
        elif value == 'CPS 2024B':
            self.OBListHeader.setText(f"    {self.hdr}")
            files = [f for f in Path('/home/kpfeng/joshw/OBs_v2/howard/2024B').glob('*.yaml')]
            self.model.OBs = []
            for i,file in enumerate(files[:30]):
                try:
                    self.model.OBs.append(ObservingBlock(str(file)))
                except:
                    print(f"Failed file {i+1}: {file}")
            print(f"Read in {len(self.model.OBs)} files")
            self.model.start_times = None
            self.model.layoutChanged.emit()
            self.SortOBs.setEnabled(True)
            self.SortOBsLabel.setEnabled(True)
            self.WeatherBand.setEnabled(False)
            self.WeatherBandLabel.setEnabled(False)
        elif value == 'KPF-CC':
            self.OBListHeader.setText('    StartTime '+self.hdr)
            files = [f for f in Path('/home/kpfeng/joshw/OBs_v2/howard/2024B').glob('*.yaml')]
            self.model.OBs = []
            self.model.start_times = []
            for i,file in enumerate(files[:30]):
                try:
                    self.model.OBs.append(ObservingBlock(str(file)))
                    import random
                    obstime = random.randrange(5, 17, step=1) + random.random()
                    self.model.start_times.append(obstime)
                except:
                    print(f"Failed file {i+1}: {file}")
            print(f"Read in {len(self.model.OBs)} files")
            self.model.sort('time')
            self.model.layoutChanged.emit()
            self.SortOBs.setEnabled(False)
            self.SortOBsLabel.setEnabled(False)
            self.WeatherBand.setEnabled(True)
            self.WeatherBandLabel.setEnabled(True)
        else:
            self.OBListHeader.setText(f"    {self.hdr}")
            self.model.OBs = [ObservingBlock('~/joshw/OBs_v2/219134.yaml'),
                              ObservingBlock('~/joshw/OBs_v2/157279.yaml'),
                              ]
            self.model.start_times = None
            self.model.layoutChanged.emit()
            self.SortOBs.setEnabled(True)
            self.SortOBsLabel.setEnabled(True)
            self.WeatherBand.setEnabled(False)
            self.WeatherBandLabel.setEnabled(False)
        self.ProgID.setCurrentText(value)

    def set_weather_band(self, value):
        self.WeatherBand.setCurrentText(value)


    ##-------------------------------------------
    ## Methods for OB List
    ##-------------------------------------------
    def select_OB(self, selected, deselected):
        if len(selected.indexes()) > 0:
            self.SOBindex = selected.indexes()[0].row()
            self.log.debug(f"Selection changed to {self.SOBindex}")
            self.update_SOB_display()
        else:
            print(selected, deselected)
            self.SOBindex = None
            self.update_SOB_display()

    def set_SOB_enabled(self, enabled):
        if enabled == False:
            self.SOB_CommentToObserver.setText('')
        self.SOB_CommentToObserverLabel.setEnabled(enabled)
        self.SOB_ShowButton.setEnabled(enabled)
        self.SOB_AddComment.setEnabled(enabled)
        self.SOB_ExecuteButton.setEnabled(enabled)
        self.SOB_ExecuteWithSlewCalButton.setEnabled(enabled)


    def update_SOB_display(self):
        if self.SOBindex is None:
            self.set_SOB_enabled(False)
            self.SOB_TargetName.setText('--')
            self.SOB_GaiaID.setText('--')
            self.SOB_TargetRA.setText('--')
            self.SOB_TargetDec.setText('--')
            self.SOB_Jmag.setText('--')
            self.SOB_Gmag.setText('--')
            self.SOB_Observation1.setText('--')
            self.SOB_Observation2.setText('--')
            self.SOB_Observation3.setText('--')
            self.SOB_ExecutionTime.setText('--')
            self.SOB_EL.setText('--')
            self.SOB_EL.setStyleSheet("color:black")
            self.SOB_EL.setToolTip("")
            self.SOB_Az.setText('--')
            self.SOB_Airmass.setText('--')
        else:
            SOB = self.model.OBs[self.SOBindex]
            self.set_SOB_enabled(True)
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

            obs_and_cals = SOB.Calibrations + SOB.Observations
            n_per_line = int(np.ceil(len(obs_and_cals)/3))
            for i in [1,2,3]:
                field = getattr(self, f'SOB_Observation{i}')
                strings = [obs_and_cals.pop(0).summary() for j in range(n_per_line) if len(obs_and_cals) > 0]
                field.setText(', '.join(strings))
            # Calculate AltAz Position
            if SOB.Target.coord is not None:
                AltAzSystem = AltAz(obstime=Time.now(), location=self.keck,
                                    pressure=620*u.mbar, temperature=0*u.Celsius)
                self.log.debug('Calculating target AltAz coordinates')
                target_altz = SOB.Target.coord.transform_to(AltAzSystem)
                self.log.debug('done')
                self.SOB_EL.setText(f"{target_altz.alt.deg:.1f} deg")
                self.SOB_Az.setText(f"{target_altz.az.deg:.1f} deg")
                is_up = above_horizon(target_altz.az.deg, target_altz.alt.deg)
                if is_up:
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

                if is_up:
                    # Calculate EL Slew Distance
                    tel_el = Angle(self.DCS_EL.binary*u.radian).to(u.deg)
                    dest_el = Angle(target_altz.alt.deg*u.deg)
                    slew = abs(tel_el - dest_el)
                    slewmsg = f"{tel_el.value:.1f} to {dest_el.value:.1f} = {slew:.1f}"
                    self.SOB_ELSlew.setText(slewmsg)
                else:
                    self.SOB_ELSlew.setText("--")

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
        if SOB is not None:
            OBcontents_popup = ScrollMessageBox(SOB)
            OBcontents_popup.setWindowTitle(f"Full OB Contents: {SOB.name()}")
            result = OBcontents_popup.exec_()
            if result == QtWidgets.QMessageBox.Ok:
                log.debug('Show popup: Ok')
            elif result == QtWidgets.QMessageBox.Cancel:
                log.info('Show popup: Edit')
                OBedit_popup = EditableMessageBox(SOB)
                OBedit_popup.setWindowTitle(f"Editing OB: {SOB.name()}")
                edit_result = OBedit_popup.exec_()
                if edit_result == QtWidgets.QMessageBox.Ok:
                    log.info('Edit popup: Ok')
                    newOB = OBedit_popup.newOB
                    if newOB.validate():
                        log.info('The edited OB has been validated')
                        self.model.OBs[self.SOBindex] = newOB
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

    def execute_SOB(self, slewcal=False):
        SOB = self.model.OBs[self.SOBindex]
        if SOB is not None:
            print('Executing OB:')
            print(str(SOB))
            self.model.OBs[self.SOBindex].executed = True
            self.model.layoutChanged.emit()

    def execute_with_slew_cal_SOB(self):
        self.execute_SOB(slewcal=True)


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

