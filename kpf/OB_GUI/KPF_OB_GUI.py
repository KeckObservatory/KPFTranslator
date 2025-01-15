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
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy.time import Time

import ktl                      # provided by kroot/ktl/keyword/python
import kPyQt                    # provided by kroot/kui/kPyQt
from PyQt5 import uic, QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

from kpf.ObservingBlocks.ObservingBlock import ObservingBlock



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
    def __init__(self, *args, OBs=[], **kwargs):
        super(OBListModel, self).__init__(*args, **kwargs)
        self.OBs = OBs
        self.start_times = None

    def data(self, index, role):
        if role == Qt.DisplayRole:
            if self.start_times is None:
                return str(self.OBs[index.row()])
            else:
                start_time_decimal = self.start_times[index.row()]
                sthr = int(np.floor(start_time_decimal))
                stmin = (start_time_decimal-sthr)*60
                start_time_str = f"{sthr:02d}:{stmin:02.0f} UT"
                return f"{start_time_str}  {str(self.OBs[index.row()]):s}"

    def rowCount(self, index):
        return len(self.OBs)

    def sort(self, sortkey):
        if self.start_times is not None:
            zipped = [z for z in zip(self.start_times, self.OBs)]
            zipped.sort(key=lambda z: z[0])
            self.OBs = [z[1] for z in zipped]
            self.start_times = [z[0] for z in zipped]
        elif sortkey == 'Name':
            self.OBs.sort(key=lambda o: o.Target.TargetName.value, reverse=False)
        elif sortkey == 'RA':
            self.OBs.sort(key=lambda o: o.Target.coord.ra.deg, reverse=False)
        elif sortkey == 'Dec':
            self.OBs.sort(key=lambda o: o.Target.coord.dec.deg, reverse=False)
        elif sortkey == 'Gmag':
            self.OBs.sort(key=lambda o: o.Target.Gmag.value, reverse=False)
        elif sortkey == 'Jmag':
            self.OBs.sort(key=lambda o: o.Target.Jmag.value, reverse=False)


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
        # Selected OB
        self.SOB = None
        # Coordinate Systems
        self.keck = EarthLocation.of_site('Keck Observatory')


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
        UT_kw.stringCallback.connect(self.UTValue.setText)

        # Sidereal Time
        self.SiderealTimeValue = self.findChild(QtWidgets.QLabel, 'SiderealTimeValue')
        LST_kw = kPyQt.kFactory(ktl.cache(self.dcs, 'LST'))
        LST_kw.stringCallback.connect(self.SiderealTimeValue.setText)

        # time since last cal
#         self.slewcaltime_value = self.findChild(QtWidgets.QLabel, 'slewcaltime_value')
#         slewcaltime_kw = kPyQt.kFactory(self.kpfconfig['SLEWCALTIME'])
#         slewcaltime_kw.stringCallback.connect(self.update_slewcaltime_value)

        # readout mode
#         self.read_mode = self.findChild(QtWidgets.QLabel, 'readout_mode_value')
#         self.red_acf_file_kw.stringCallback.connect(self.update_acffile)
#         self.green_acf_file_kw.stringCallback.connect(self.update_acffile)

        # disabled detectors
#         self.disabled_detectors_value = self.findChild(QtWidgets.QLabel, 'disabled_detectors_value')
#         self.disabled_detectors_value.setText('')
#         cahk_enabled_kw = kPyQt.kFactory(self.kpfconfig['CA_HK_ENABLED'])
#         cahk_enabled_kw.stringCallback.connect(self.update_ca_hk_enabled)
#         green_enabled_kw = kPyQt.kFactory(self.kpfconfig['GREEN_ENABLED'])
#         green_enabled_kw.stringCallback.connect(self.update_green_enabled)
#         red_enabled_kw = kPyQt.kFactory(self.kpfconfig['RED_ENABLED'])
#         red_enabled_kw.stringCallback.connect(self.update_red_enabled)
#         expmeter_enabled_kw = kPyQt.kFactory(self.kpfconfig['EXPMETER_ENABLED'])
#         expmeter_enabled_kw.stringCallback.connect(self.update_expmeter_enabled)

        # List of Observing Blocks
        self.OBListHeader = self.findChild(QtWidgets.QLabel, 'OBListHeader')
        self.hdr = 'TargetName       RA           Dec         Gmag  Jmag  Observations'
        self.OBListHeader.setText(self.hdr)

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
        self.SOB_nExp = self.findChild(QtWidgets.QLabel, 'SOB_nExp')
        self.SOB_ExpTime = self.findChild(QtWidgets.QLabel, 'SOB_ExpTime')
        self.SOB_ExpMeterMode = self.findChild(QtWidgets.QLabel, 'SOB_ExpMeterMode')
        # Calculated Values
        self.SOB_ExecutionTime = self.findChild(QtWidgets.QLabel, 'SOB_ExecutionTime')
        self.SOB_EL = self.findChild(QtWidgets.QLabel, 'SOB_EL')
        self.SOB_Az = self.findChild(QtWidgets.QLabel, 'SOB_Az')
        self.SOB_Airmass = self.findChild(QtWidgets.QLabel, 'SOB_Airmass')
        self.SOB_AzSlew = self.findChild(QtWidgets.QLabel, 'SOB_AzSlew')
        self.SOB_ELSlew = self.findChild(QtWidgets.QLabel, 'SOB_ELSlew')

        # SOB Execution
        self.SOB_ShowButton = self.findChild(QtWidgets.QPushButton, 'SOB_ShowButton')
        self.SOB_ShowButton.clicked.connect(self.show_SOB)


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


    ##-------------------------------------------
    ## Methods to get data from DB or Schedule
    ##-------------------------------------------
    def get_progIDs(self):
        progIDs = ['', 'KPF-CC']
        # Go get list of available program IDs for Instrument=KPF
        return progIDs + ['E123', 'E456']

    def set_ProgID(self, value):
        print(f"set_ProgID: '{value}'")
        if value == '':
            self.OBListHeader.setText(hdr)
            self.model.OBs = []
            self.model.start_times = None
            self.model.layoutChanged.emit()
            self.SortOBs.setEnabled(False)
            self.SortOBsLabel.setEnabled(False)
            self.WeatherBand.setEnabled(False)
            self.WeatherBandLabel.setEnabled(False)
        elif value == 'KPF-CC':
            self.OBListHeader.setText('StartTime '+self.hdr)
            self.model.OBs = [ObservingBlock('~/joshw/OBs_v2/219134.yaml'),
                              ObservingBlock('~/joshw/OBs_v2/156279.yaml'),
                              ObservingBlock('~/joshw/OBs_v2/Bernard2.yaml'),
                              ]
            self.model.start_times = [8.1, 5.2, 6.3]
            self.model.sort('time')
            self.model.layoutChanged.emit()
            self.SortOBs.setEnabled(False)
            self.SortOBsLabel.setEnabled(False)
            self.WeatherBand.setEnabled(True)
            self.WeatherBandLabel.setEnabled(True)
        else:
            self.OBListHeader.setText(self.hdr)
            self.model.OBs = [ObservingBlock('~/joshw/OBs_v2/219134.yaml'),
                              ObservingBlock('~/joshw/OBs_v2/156279.yaml'),
                              ObservingBlock('~/joshw/OBs_v2/Bernard2.yaml'),
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
            selected_index = selected.indexes()[0].row()
            print(f"Selection changed to {selected_index}")
            self.SOB = self.model.OBs[selected_index]
            self.update_SOB_display(self.SOB)

    def update_SOB_display(self, SOB):
        if self.SOB is None:
            self.SOB_TargetName.setText('--')
            self.SOB_GaiaID.setText('--')
            self.SOB_TargetRA.setText('--')
            self.SOB_TargetDec.setText('--')
            self.SOB_Jmag.setText('--')
            self.SOB_Gmag.setText('--')
            self.SOB_nExp.setText('--')
            self.SOB_ExpTime.setText('--')
            self.SOB_ExpMeterMode.setText('--')
            self.SOB_EL.setText('--')
            self.SOB_EL.setStyleSheet("color:black")
            self.SOB_Az.setText('--')
            self.SOB_Airmass.setText('--')
        else:
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
            self.SOB_nExp.setText(f"{SOB.Observations[0].get('nExp'):d}")
            self.SOB_ExpTime.setText(f"{SOB.Observations[0].get('ExpTime'):.1f} s")
            self.SOB_ExpMeterMode.setText(SOB.Observations[0].get('ExpMeterMode'))
            # Calculate AltAz Position
            if self.SOB.Target.coord is not None:
                self.log.debug('Generating AltAzSystem')
                AltAzSystem = AltAz(obstime=Time.now(), location=self.keck)
                self.log.debug('Calculating target AltAz coordinates')
                target_altz = self.SOB.Target.coord.transform_to(AltAzSystem)
                self.log.debug('done')
                self.SOB_EL.setText(f"{target_altz.alt.deg:.1f} deg")
                self.SOB_Az.setText(f"{target_altz.az.deg:.1f} deg")
                if above_horizon(target_altz.az.deg, target_altz.alt.deg):
                    self.SOB_Airmass.setText(f"{target_altz.secz:.2f}")
                    self.SOB_EL.setStyleSheet("color:black")
                else:
                    self.SOB_Airmass.setText("--")
                    self.SOB_EL.setStyleSheet("color:orange")

    def sort_OB_list(self, value):
        self.model.sort(value)
        self.model.layoutChanged.emit()
        self.ListOfOBs.selectionModel().clearSelection()
        self.SOB = None
        self.update_SOB_display(self.SOB)

    def show_SOB(self):
        if self.SOB is not None:
            popup = QtWidgets.QMessageBox()
            popup.setWindowTitle(f"Full OB Contents: {str(self.SOB)}")
            popup.setText(self.SOB.__repr__())
            popup.setFont(QtGui.QFont('Courier New', 12))
            popup.exec_()


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

