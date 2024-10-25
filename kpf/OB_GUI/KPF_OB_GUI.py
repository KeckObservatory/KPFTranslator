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
from copy import deepcopy
from astropy.coordinates import SkyCoord
from astropy.time import Time

import ktl                      # provided by kroot/ktl/keyword/python
import kPyQt                    # provided by kroot/kui/kPyQt
from PyQt5 import uic, QtWidgets, QtCore
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

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return str(self.OBs[index.row()])

    def rowCount(self, index):
        return len(self.OBs)

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
        # OBs
        self.OBs = [ObservingBlock('~/joshw/OBs_v2/219134.yaml'),
                    ObservingBlock('~/joshw/OBs_v2/156279.yaml'),
                    ObservingBlock('~/joshw/OBs_v2/Bernard2.yaml'),
                    ]


    def setupUi(self):
        self.log.debug('setupUi')
        self.setWindowTitle("KPF OB GUI")

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
        self.ListOfOBs = self.findChild(QtWidgets.QListView, 'ListOfOBs')
        self.model = OBListModel(OBs=self.OBs)
        self.ListOfOBs.setModel(self.model)
        self.ListOfOBs.selectionModel().selectionChanged.connect(self.select_OB)

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
    ## Methods for OB List
    ##-------------------------------------------
    def select_OB(self, selected, deselected):
        selected_index = selected.indexes()[0].row()
        print(f"Selection changed to {selected_index}")
        SOB = self.OBs[selected_index]
        self.update_SOB_display(SOB)

    def update_SOB_display(self, SOB):
        self.SOB_TargetName.setText(SOB.Target.get('TargetName'))
        self.SOB_GaiaID.setText(SOB.Target.get('GaiaID'))
        self.SOB_TargetRA.setText(SOB.Target.get('RA'))
        self.SOB_TargetDec.setText(SOB.Target.get('Dec'))
#         try:
        now = Time(datetime.datetime.utcnow())
        print(SOB.Target)
        print(SOB.Target.coord)
        coord_now = SOB.Target.coord.apply_space_motion(new_obstime=now)
        print(coord_now)
        coord_now_string = coord_now.to_string('hmsdms', sep=':', precision=2)
        self.SOB_Jmag.setText(coord_now_string.split()[0])
        self.SOB_Gmag.setText(coord_now_string.split()[1])
#         except:
#             self.SOB_Jmag.setText(f"{SOB.Target.get('Jmag'):.2f}")
#             self.SOB_Gmag.setText(f"{SOB.Target.get('Gmag'):.2f}")
        self.SOB_nExp.setText(f"{SOB.Observations[0].get('nExp'):d}")
        self.SOB_ExpTime.setText(f"{SOB.Observations[0].get('ExpTime'):.1f} s")
        self.SOB_ExpMeterMode.setText(SOB.Observations[0].get('ExpMeterMode'))


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

