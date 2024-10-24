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

import ktl                      # provided by kroot/ktl/keyword/python
import kPyQt                    # provided by kroot/kui/kPyQt
from PyQt5 import uic
from PyQt5.QtWidgets import (QApplication, QMainWindow,
                             QLabel, QPushButton, QLineEdit, QComboBox,
                             QCheckBox, QMessageBox, QFileDialog)


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
    LogFileName = logdir / 'OB_GUI.log'
    LogFileHandler = RotatingFileHandler(LogFileName,
                                         maxBytes=100*1024*1024, # 100 MB
                                         backupCount=1000) # Keep old files
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
        # Keywords
        self.dcs = 'dcs1'
        self.log.debug('Cacheing keyword services')
        self.kpfexpose = ktl.cache('kpfexpose')

    def setupUi(self):
        self.log.debug('setupUi')
        self.setWindowTitle("KPF OB GUI")

        # Program ID
        self.progID = self.findChild(QLabel, 'progID')
        progname_kw = kPyQt.kFactory(self.kpfexpose['PROGNAME'])
        progname_kw.stringCallback.connect(self.progID.setText)

        # Observer
#         self.Observer = self.findChild(QLabel, 'Observer')
#         observer_kw = kPyQt.kFactory(self.kpfexpose['OBSERVER'])
#         observer_kw.stringCallback.connect(self.update_observer_value)

        # script name
#         self.scriptname_value = self.findChild(QLabel, 'scriptname_value')
#         scriptname_kw = kPyQt.kFactory(self.kpfconfig['SCRIPTNAME'])
#         scriptname_kw.stringCallback.connect(self.update_scriptname_value)

        # script stop
#         self.scriptstop_value = self.findChild(QLabel, 'scriptstop_value')
#         scriptstop_kw = kPyQt.kFactory(self.kpfconfig['SCRIPTSTOP'])
#         scriptstop_kw.stringCallback.connect(self.update_scriptstop_value)
#         self.scriptstop_btn = self.findChild(QPushButton, 'scriptstop_btn')
#         self.scriptstop_btn.clicked.connect(self.set_scriptstop)

        # full stop
#         self.fullstop_btn = self.findChild(QPushButton, 'fullstop_btn')
#         self.fullstop_btn.clicked.connect(self.do_fullstop)

        # expose status
#         self.expose_status_value = self.findChild(QLabel, 'expose_status_value')
#         expose_kw = kPyQt.kFactory(self.kpfexpose['EXPOSE'])
#         expose_kw.stringCallback.connect(self.update_expose_status_value)

        # Universal Time
        self.UTValue = self.findChild(QLabel, 'UTValue')
        UT_kw = kPyQt.kFactory(ktl.cache(self.dcs, 'UT'))
        UT_kw.stringCallback.connect(self.UTValue.setText)

        # Sidereal Time
        self.SiderealTimeValue = self.findChild(QLabel, 'SiderealTimeValue')
        LST_kw = kPyQt.kFactory(ktl.cache(self.dcs, 'LST'))
        LST_kw.stringCallback.connect(self.SiderealTimeValue.setText)

        # time since last cal
#         self.slewcaltime_value = self.findChild(QLabel, 'slewcaltime_value')
#         slewcaltime_kw = kPyQt.kFactory(self.kpfconfig['SLEWCALTIME'])
#         slewcaltime_kw.stringCallback.connect(self.update_slewcaltime_value)

        # readout mode
#         self.read_mode = self.findChild(QLabel, 'readout_mode_value')
#         self.red_acf_file_kw.stringCallback.connect(self.update_acffile)
#         self.green_acf_file_kw.stringCallback.connect(self.update_acffile)

        # disabled detectors
#         self.disabled_detectors_value = self.findChild(QLabel, 'disabled_detectors_value')
#         self.disabled_detectors_value.setText('')
#         cahk_enabled_kw = kPyQt.kFactory(self.kpfconfig['CA_HK_ENABLED'])
#         cahk_enabled_kw.stringCallback.connect(self.update_ca_hk_enabled)
#         green_enabled_kw = kPyQt.kFactory(self.kpfconfig['GREEN_ENABLED'])
#         green_enabled_kw.stringCallback.connect(self.update_green_enabled)
#         red_enabled_kw = kPyQt.kFactory(self.kpfconfig['RED_ENABLED'])
#         red_enabled_kw.stringCallback.connect(self.update_red_enabled)
#         expmeter_enabled_kw = kPyQt.kFactory(self.kpfconfig['EXPMETER_ENABLED'])
#         expmeter_enabled_kw.stringCallback.connect(self.update_expmeter_enabled)







if __name__ == '__main__':
    log = create_GUI_log()
    log.info(f"Starting KPF OB GUI")
    try:
        main()
    except Exception as e:
        log.error(e)
        log.error(traceback.format_exc())
    log.info(f"Exiting KPF OB GUI")

