#!/kroot/rel/default/bin/kpython3
import sys
import os
import traceback
import argparse
import time
from pathlib import Path
import datetime
import logging
from logging.handlers import RotatingFileHandler
import re
import copy
import subprocess

import ktl                      # provided by kroot/ktl/keyword/python
import kPyQt                    # provided by kroot/kui/kPyQt

from PyQt5 import uic
from PyQt5.QtCore import QTimer, QMargins
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFrame, QStatusBar,
                             QLabel, QPushButton, QLineEdit, QComboBox,
                             QCheckBox, QMessageBox, QGridLayout, QAction)

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
plt.rcParams.update({'axes.titlesize': 'x-small',
                     'axes.labelsize': 'x-small',
                     'xtick.labelsize': 'x-small',
                     'ytick.labelsize': 'x-small'})

import numpy as np
from astropy.io import fits
from astropy.nddata import CCDData
from astropy.modeling.models import Moffat2D
from astropy.modeling.fitting import LevMarLSQFitter

import warnings
from astropy.wcs import FITSFixedWarning
from astropy.utils.exceptions import AstropyUserWarning
warnings.simplefilter('ignore', category=FITSFixedWarning)

from ginga.AstroImage import AstroImage
from ginga.misc import log as ginga_log
from ginga.qtw.QtHelp import QtGui, QtCore
from ginga.qtw.ImageViewQt import CanvasView


##-------------------------------------------------------------------------
## Parse Command Line Arguments
##-------------------------------------------------------------------------
## create a parser object for understanding command-line arguments
p = argparse.ArgumentParser(description='''
''')
## add flags
p.add_argument("-v", "--verbose", dest="verbose",
    default=False, action="store_true",
    help="Be verbose! (default = False)")
p.add_argument("-m", "--monitor", dest="monitor",
    default=False, action="store_true",
    help="Start GUI in monitor mode (no control)")
p.add_argument("-d", "--dark", dest="dark",
    default=False, action="store_true",
    help="Start GUI in dark mode")
cmd_line_args = p.parse_args()


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
def create_GUI_log():
    log = logging.getLogger('KPF_TipTilt_GUI')
    log.setLevel(logging.DEBUG)
    ## Set up console output
    LogConsoleHandler = logging.StreamHandler()
    if cmd_line_args.verbose is True:
        LogConsoleHandler.setLevel(logging.DEBUG)
    else:
        LogConsoleHandler.setLevel(logging.INFO)
    LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s')
    LogConsoleHandler.setFormatter(LogFormat)
    log.addHandler(LogConsoleHandler)
    ## Set up file output
    logdir = Path(f'/s/sdata1701/KPFTranslator_logs/')
    if logdir.exists() is False:
        logdir.mkdir(mode=0o777, parents=True)
    LogFileName = logdir / 'TipTilt_GUI.log'
    LogFileHandler = RotatingFileHandler(LogFileName,
                                         maxBytes=100*1024*1024, # 100 MB
                                         backupCount=1000) # Keep old files
    LogFileHandler.setLevel(logging.DEBUG)
    LogFileHandler.setFormatter(LogFormat)
    log.addHandler(LogFileHandler)
    return log


def main(log):
    application = QApplication(sys.argv)
    if cmd_line_args.dark == True:
        css_file = Path(__file__).parent / 'darkstyle.qss'
    else:
        css_file = Path(__file__).parent / 'lightstyle.qss'
    with open(css_file, 'r') as f:
        dark_css = f.read()
    application.setStyleSheet(dark_css)
    main_window = MainWindow(log)
    main_window.setupUi()
    main_window.show()
    return kPyQt.run(application)


class MainWindow(QMainWindow):

    def __init__(self, log, *args, **kwargs):
        QMainWindow.__init__(self, *args, **kwargs)
        ui_file = Path(__file__).parent / 'TipTiltGUI.ui'
        uic.loadUi(f"{ui_file}", self)
        self.log = log
        self.ginga_log = ginga_log.get_logger("example1", log_stderr=True, level=40)
        self.log.debug('Initializing MainWindow')
        # Keywords
        self.log.debug('Cacheing keyword services')
        kpfguide = ktl.cache('kpfguide')
        self.CONTINUOUS = kPyQt.kFactory(kpfguide['CONTINUOUS'])
        self.SAVE = kPyQt.kFactory(kpfguide['SAVE'])
        self.GAIN = kPyQt.kFactory(kpfguide['GAIN'])
        self.FPS = kPyQt.kFactory(kpfguide['FPS'])
        self.TIPTILT_CALC = kPyQt.kFactory(kpfguide['TIPTILT_CALC'])
        self.TIPTILT_CONTROL = kPyQt.kFactory(kpfguide['TIPTILT_CONTROL'])
        self.OFFLOAD = kPyQt.kFactory(kpfguide['OFFLOAD'])
        self.OFFLOAD_DCS = kPyQt.kFactory(kpfguide['OFFLOAD_DCS'])
        self.ALL_LOOPS = kPyQt.kFactory(kpfguide['ALL_LOOPS'])
        self.OBJECT1 = kPyQt.kFactory(kpfguide['OBJECT1'])
        self.OBJECT2 = kPyQt.kFactory(kpfguide['OBJECT2'])
        self.OBJECT3 = kPyQt.kFactory(kpfguide['OBJECT3'])

        self.OBJECT_CHOICE = kPyQt.kFactory(kpfguide['OBJECT_CHOICE'])
        self.OBJECT_FLUX = kPyQt.kFactory(kpfguide['OBJECT_FLUX'])
        self.OBJECT_PEAK = kPyQt.kFactory(kpfguide['OBJECT_PEAK'])
        self.OBJECT_INTENSITY = kPyQt.kFactory(kpfguide['OBJECT_INTENSITY'])
        self.OBJECT_AREA = kPyQt.kFactory(kpfguide['OBJECT_AREA'])
        self.OBJECT_DBCONT = kPyQt.kFactory(kpfguide['OBJECT_DBCONT'])
        self.TIPTILT_PHASE = kPyQt.kFactory(kpfguide['TIPTILT_PHASE'])
        self.TIPTILT_ERROR = kPyQt.kFactory(kpfguide['TIPTILT_ERROR'])
        self.TIPTILT_CONTROL_X = kPyQt.kFactory(kpfguide['TIPTILT_CONTROL_X'])
        self.TIPTILT_CONTROL_Y = kPyQt.kFactory(kpfguide['TIPTILT_CONTROL_Y'])
        self.DAR_ENABLE = kPyQt.kFactory(kpfguide['DAR_ENABLE'])
        self.LASTFILE = kPyQt.kFactory(kpfguide['LASTFILE'])
        self.TIPTILT_ROIDIM = kPyQt.kFactory(kpfguide['TIPTILT_ROIDIM'])
        self.PIX_TARGET = kPyQt.kFactory(kpfguide['PIX_TARGET'])

        kpffiu = ktl.cache('kpffiu')
        self.TTXSRV = kPyQt.kFactory(kpffiu['TTXSRV'])
        self.TTYSRV = kPyQt.kFactory(kpffiu['TTYSRV'])
        self.TTXVAX = kPyQt.kFactory(kpffiu['TTXVAX'])
        self.TTYVAX = kPyQt.kFactory(kpffiu['TTYVAX'])
        self.MODE = kPyQt.kFactory(kpffiu['MODE'])

        self.SCRIPTNAME = kPyQt.kFactory(ktl.cache('kpfconfig', 'SCRIPTNAME'))

        self.EXPOSE = kPyQt.kFactory(ktl.cache('kpfexpose', 'EXPOSE'))
        self.ELAPSED = kPyQt.kFactory(ktl.cache('kpfexpose', 'ELAPSED'))
        self.OBJECT = kPyQt.kFactory(ktl.cache('kpfexpose', 'OBJECT'))
        self.EXPOSURE = kPyQt.kFactory(ktl.cache('kpfexpose', 'EXPOSURE'))

        self.tthome = kpfguide['TIPTILT_HOME'].read(binary=True)
        self.ttxrange = kpfguide['TIPTILT_XRANGE'].read(binary=True)
        self.ttyrange = kpfguide['TIPTILT_YRANGE'].read(binary=True)

        # History for Plots
        #  Tip Tilt Error Plot
        self.TipTiltErrorValues = []
        self.TipTiltErrorTimes = []
        self.TipTiltErrorTime0 = None
        self.StarPositionError = []
        self.StarPositionTimes = []
        self.StarPositionTime0 = None
        #  Mirror Position Plot
        self.MirrorPosCount = 60
        self.MirrorPosX = []
        self.MirrorPosY = []
        self.MirrorPosAlpha = np.linspace(0.1,1,self.MirrorPosCount)
        #  Flux Plot
        self.ObjectFluxValues = []
        self.ObjectFluxTimes = []
        self.ObjectFluxTime0 = None
        # Values for Image Display
        self.xcent = None
        self.ycent = None
        self.pscale = kpfguide['PSCALE'].read(binary=True)
        # Mode
        self.enable_control = not cmd_line_args.monitor
        if self.enable_control is True:
            self.log.info(f"Starting GUI in full control mode")
        else:
            self.log.info(f"Starting GUI in monitor only mode")
        # Settings
        self.TipTiltErrorPlotUpdateTime = 2 # seconds
        self.TipTiltErrorPlotAgeThreshold = 30 # seconds
        self.FluxPlotAgeThreshold = 60 # seconds
        self.MirrorPositionPlotUpdateTime = 2 # seconds
        self.FigurePadding = 0.1
        self.VeryLowPeakFluxThreshold = 300
        self.LowPeakFluxThreshold = 600
        self.HighPeakFluxThreshold = 12000
        self.VeryLowFluxThreshold = 20000
        self.LowFluxThreshold = 40000
        self.HighFluxThreshold = 10e6

    def setupUi(self):
        self.log.debug('setupUi')
        self.setWindowTitle("KPF TipTilt GUI")

        # Menu Bar
        self.actionQuit = self.findChild(QAction, 'actionQuit')
        self.actionQuit.triggered.connect(self.quit)
        self.actionrestart_kpfguide1 = self.findChild(QAction, 'actionrestart_kpfguide1')
        self.actionrestart_kpfguide1.triggered.connect(self.run_restart_kpfguide1)
        self.actionrestart_kpfguide2 = self.findChild(QAction, 'actionrestart_kpfguide2')
        self.actionrestart_kpfguide2.triggered.connect(self.run_restart_kpfguide2)
        self.actionrestart_kpfguide3 = self.findChild(QAction, 'actionrestart_kpfguide3')
        self.actionrestart_kpfguide3.triggered.connect(self.run_restart_kpfguide3)

        # Status Bar
        self.StatusBar = self.findChild(QStatusBar, 'statusBar')
        self.CONTINUOUSStatusLabel = QLabel('')
        self.StatusBar.addPermanentWidget(self.CONTINUOUSStatusLabel)
        self.SAVEStatusLabel = QLabel('')
        self.StatusBar.addPermanentWidget(self.SAVEStatusLabel)
        self.TTXSRVStatusLabel = QLabel('')
        self.StatusBar.addPermanentWidget(self.TTXSRVStatusLabel)
        self.TTYSRVStatusLabel = QLabel('')
        self.StatusBar.addPermanentWidget(self.TTYSRVStatusLabel)
        self.XAxisStatusLabel = QLabel('')
        self.StatusBar.addPermanentWidget(self.XAxisStatusLabel)
        self.YAxisStatusLabel = QLabel('')
        self.StatusBar.addPermanentWidget(self.YAxisStatusLabel)
        self.DARStatusLabel = QLabel('')
        self.StatusBar.addPermanentWidget(self.DARStatusLabel)

        # CONTINUOUS and SAVE
        self.CONTINUOUS.stringCallback.connect(self.update_CONTINUOUS)
        self.CONTINUOUS.primeCallback()
        self.SAVE.stringCallback.connect(self.update_SAVE)
        self.SAVE.primeCallback()

        # Camera Gain
        self.CameraGainValue = self.findChild(QLabel, 'CameraGainValue')
        self.CameraGain = self.findChild(QComboBox, 'CameraGain')
        self.CameraGain.addItems(list(self.GAIN.ktl_keyword._getEnumerators()) + [''])
        self.GAIN.stringCallback.connect(self.update_CameraGain)
        self.GAIN.primeCallback()
        self.CameraGain.currentTextChanged.connect(self.set_CameraGain)
        self.CameraGain.setEnabled(self.enable_control)

        # Camera FPS
        self.CameraFPSValue = self.findChild(QLabel, 'CameraFPSValue')
        self.CameraFPSSelector = self.findChild(QComboBox, 'CameraFPSSelector')
        self.fps_values = ['', '2', '5', '10', '20', '50', '100', '150']
        self.CameraFPSSelector.addItems(self.fps_values)
        self.FPS.stringCallback.connect(self.update_CameraFPS)
        self.FPS.primeCallback()
        self.CameraFPSSelector.currentTextChanged.connect(self.set_CameraFPS)
        self.CameraFPSSelector.setEnabled(self.enable_control)

        # Peak Flux
        self.PeakFlux = self.findChild(QLabel, 'PeakFlux')
        self.OBJECT_PEAK.stringCallback.connect(self.update_PeakFlux)
        self.OBJECT_PEAK.primeCallback()

        # Total Flux
        self.TotalFlux = self.findChild(QLabel, 'TotalFlux')
        self.OBJECT_FLUX.stringCallback.connect(self.update_TotalFlux)
        self.OBJECT_FLUX.primeCallback()

        # Tip Tilt FPS
        self.TipTiltFPS = self.findChild(QLabel, 'TipTiltFPS')
        self.FPS.stringCallback.connect(self.update_TipTiltFPS)
        self.FPS.primeCallback()

        # Tip Tilt Phase
        self.TipTiltPhase = self.findChild(QLabel, 'TipTiltPhase')
        self.TIPTILT_PHASE.stringCallback.connect(self.update_TipTiltPhase)
        self.TIPTILT_PHASE.primeCallback()

        # Tip Tilt Error
        self.TipTiltError = self.findChild(QLabel, 'TipTiltError')
        self.TIPTILT_ERROR.stringCallback.connect(self.update_TipTiltError)
        self.TIPTILT_ERROR.primeCallback()

        # Tip Tilt Error Plot
        self.TipTiltErrorPlotFrame = self.findChild(QFrame, 'TipTiltErrorPlotFrame')
        self.TipTiltErrorPlotFig = plt.figure(num=1, dpi=100)
        self.TipTiltErrorPlotFig.set_tight_layout({'pad': self.FigurePadding})
        self.TipTiltErrorPlotCanvas = FigureCanvasQTAgg(self.TipTiltErrorPlotFig)
        plotLayout = QGridLayout()
        plotLayout.addWidget(self.TipTiltErrorPlotCanvas, 1, 0, 1, -1)
        plotLayout.setColumnStretch(1, 100)
        self.TipTiltErrorPlotFrame.setLayout(plotLayout)
        self.update_TipTiltErrorPlot()

        # Tip Tilt Error Plot Time
        self.TTErrPlotTime = self.findChild(QComboBox, 'TTErrPlotTime')
        self.TTErrPlotTime_values = ['10', '30', '60', '120', '300']
        self.TTErrPlotTime.addItems(self.TTErrPlotTime_values)
        self.TTErrPlotTime.setCurrentText(f"{self.TipTiltErrorPlotAgeThreshold:.0f}")
        self.set_TTErrPlotTime(self.TipTiltErrorPlotAgeThreshold)
        self.TTErrPlotTime.currentTextChanged.connect(self.set_TTErrPlotTime)

        # Flux Plot
        self.FluxPlotFrame = self.findChild(QFrame, 'FluxPlotFrame')
        self.FluxPlotFig = plt.figure(num=2, dpi=100)
        self.FluxPlotFig.set_tight_layout({'pad': self.FigurePadding})
        self.FluxPlotCanvas = FigureCanvasQTAgg(self.FluxPlotFig)
        FluxPlotLayout = QGridLayout()
        FluxPlotLayout.addWidget(self.FluxPlotCanvas, 1, 0, 1, -1)
        FluxPlotLayout.setColumnStretch(1, 100)
        self.FluxPlotFrame.setLayout(FluxPlotLayout)
        self.update_FluxPlot()

        # Flux Plot Time
        self.FluxPlotTime = self.findChild(QComboBox, 'ObjectFluxPlotTime')
        self.FluxPlotTime_values = ['10', '30', '60', '120', '300']
        self.FluxPlotTime.addItems(self.FluxPlotTime_values)
        self.FluxPlotTime.setCurrentText(f"{self.FluxPlotAgeThreshold:.0f}")
        self.set_FluxPlotTime(self.FluxPlotAgeThreshold)
        self.FluxPlotTime.currentTextChanged.connect(self.set_FluxPlotTime)

        # Plot Timer
        self.PlotTimer = QTimer()
        self.PlotTimer.timeout.connect(self.update_plots)
        self.PlotTimer.start(self.TipTiltErrorPlotUpdateTime*1000)

        # Image Display
        self.ImageDisplayFrame = self.findChild(QFrame, 'ImageDisplayFrame')
        self.LastFileValue = self.findChild(QLabel, 'LastFileValue')
        self.LASTFILE.stringCallback.connect(self.update_lastfile)
        self.LASTFILE.primeCallback()
        # create the ginga viewer and configure it
        self.ImageViewer = CanvasView(self.ginga_log, render='widget')
        self.ImageViewer.enable_autocuts('on')
        self.ImageViewer.set_autocut_params('minmax')
        self.ImageViewer.enable_autozoom('on')
        self.ImageViewer.set_intensity_map('log')
        self.ImageViewer.set_bg(0.2, 0.2, 0.2)
        self.ImageViewer.ui_set_active(True)
        self.ImageViewer.add_callback('cursor-changed', self.cursor_position_update)
        # Set up drawing canvas
        ivcanvas = self.ImageViewer.get_canvas()
        DrawingCanvas = ivcanvas.get_draw_class('drawingcanvas')
        self.overlay_canvas = DrawingCanvas()
        ivcanvas.add(self.overlay_canvas)
        # enable some user interaction
        bindings = self.ImageViewer.get_bindings()
        bindings.enable_cmap(True)
        bindings.enable_cuts(True)
        ginga_widget = self.ImageViewer.get_widget()
        ginga_widget.resize(512, 512)
        gingaLayout = QGridLayout()
        gingaLayout.addWidget(ginga_widget, 1, 0, 1, -1)
        gingaLayout.setColumnStretch(1, 100)
        self.ImageDisplayFrame.setLayout(gingaLayout)

        # Object Choice
        self.ObjectChoiceValue = self.findChild(QLabel, 'ObjectChoiceValue')
        self.ObjectChoice = self.findChild(QComboBox, 'ObjectChoice')
        self.ObjectChoice.addItems(['', 'OBJECT1', 'OBJECT2', 'OBJECT3'])
        self.OBJECT_CHOICE.stringCallback.connect(self.update_ObjectChoice)
        self.OBJECT_CHOICE.primeCallback()
        self.ObjectChoice.currentTextChanged.connect(self.set_ObjectChoice)
        self.ObjectChoice.setEnabled(self.enable_control)

        # Mirror Position Plot
        self.TTXSRV.stringCallback.connect(self.update_ttxsrv)
        self.TTXSRV.primeCallback()
        self.TTYSRV.stringCallback.connect(self.update_ttysrv)
        self.TTYSRV.primeCallback()
        self.TTXVAX.stringCallback.connect(self.update_mirror_pos_x)
        self.TTXVAX.primeCallback()
        self.TTYVAX.stringCallback.connect(self.update_mirror_pos_y)
        self.TTYVAX.primeCallback()
        self.MirrorPositionFrame = self.findChild(QFrame, 'TipTiltMirrorPositionFrame')
        self.MirrorPositionFig = plt.figure(num=4, dpi=100)
        self.MirrorPositionFig.set_tight_layout({'pad': self.FigurePadding})
        self.MirrorPositionCanvas = FigureCanvasQTAgg(self.MirrorPositionFig)
        plotLayout = QGridLayout()
        plotLayout.addWidget(self.MirrorPositionCanvas, 1, 0, 1, -1)
        plotLayout.setColumnStretch(1, 100)
        self.MirrorPositionFrame.setLayout(plotLayout)
        self.update_MirrorPositionPlot()
        self.MirrorPositionPlotTimer = QTimer()
        self.MirrorPositionPlotTimer.timeout.connect(self.update_MirrorPositionPlot)
        self.MirrorPositionPlotTimer.start(self.MirrorPositionPlotUpdateTime*1000)

        # Image Cut
        self.ImageCut = self.findChild(QComboBox, 'ImageCut')
        self.ImageCut.addItems(['minmax', 'histogram 99.5', 'histogram 99', 'histogram 98', 'median', 'stddev', 'zscale'])
        self.ImageCut.currentTextChanged.connect(self.set_ImageCut)

        # Image Scaling
        self.ImageScaling = self.findChild(QComboBox, 'ImageScaling')
        self.ImageScaling.addItems(['linear', 'log', 'neglog'])
        self.ImageScaling.currentTextChanged.connect(self.set_ImageScaling)

        # Tip Tilt On/Off
        self.TipTiltOnOffButton = self.findChild(QPushButton, 'TipTiltOnOffButton')
        self.TipTiltOnOffButton.setEnabled(self.enable_control)
        self.TipTiltOnOffButton.clicked.connect(self.toggle_all_loops)

        # Tip Tilt Calculations
        self.CalculationCheckBox = self.findChild(QCheckBox, 'CalculationCheckBox')
        self.TIPTILT_CALC.integerCallback.connect(self.update_TipTiltCalc)
        self.TIPTILT_CALC.primeCallback()
        self.CalculationCheckBox.stateChanged.connect(self.TipTiltCalc_state_change)
        self.CalculationCheckBox.setEnabled(self.enable_control)

        # Tip Tilt Control
        self.ControlCheckBox = self.findChild(QCheckBox, 'ControlCheckBox')
        self.TIPTILT_CONTROL.stringCallback.connect(self.update_TipTiltControl)
        self.TIPTILT_CONTROL.primeCallback()
        self.ControlCheckBox.stateChanged.connect(self.TipTiltControl_state_change)
        self.ControlCheckBox.setEnabled(self.enable_control)

        # Offload
        self.OffloadCheckBox = self.findChild(QCheckBox, 'OffloadCheckBox')
        self.OFFLOAD.stringCallback.connect(self.update_Offload)
        self.OFFLOAD.primeCallback()
        self.OffloadCheckBox.stateChanged.connect(self.Offload_state_change)
        self.OffloadCheckBox.setEnabled(self.enable_control)

        # Offload DCS Status
        self.OFFLOAD_DCS.stringCallback.connect(self.update_OffloadDCS)
        self.OFFLOAD_DCS.primeCallback()

        # Detect SNR
        self.DetectSNRValue = self.findChild(QLabel, 'DetectSNRValue')
        self.DetectSNRSelector = self.findChild(QComboBox, 'DetectSNRSelector')
        self.DetectSNR_values = ['', '3', '5', '7', '10', '20', '30']
        self.DetectSNRSelector.addItems(self.DetectSNR_values)
        self.OBJECT_INTENSITY.stringCallback.connect(self.update_DetectSNR)
        self.OBJECT_INTENSITY.primeCallback()
        self.DetectSNRSelector.currentTextChanged.connect(self.set_DetectSNR)
        self.DetectSNRSelector.setEnabled(self.enable_control)

        # Detect Area
        self.DetectAreaValue = self.findChild(QLabel, 'DetectAreaValue')
        self.DetectAreaSelector = self.findChild(QComboBox, 'DetectAreaSelector')
        self.DetectArea_values = ['', '30', '50', '80', '100', '150', '200', '300']
        self.DetectAreaSelector.addItems(self.DetectArea_values)
        self.OBJECT_AREA.stringCallback.connect(self.update_DetectArea)
        self.OBJECT_AREA.primeCallback()
        self.DetectAreaSelector.currentTextChanged.connect(self.set_DetectArea)
        self.DetectAreaSelector.setEnabled(self.enable_control)

        # Deblend 
        self.DeblendValue = self.findChild(QLabel, 'DeblendValue')
        self.DeblendSelector = self.findChild(QComboBox, 'DeblendSelector')
        self.Deblend_values = ['', '1.00', '0.50', '0.20', '0.10', '0.02', '0.01', '0.001']
        self.DeblendSelector.addItems(self.Deblend_values)
        self.OBJECT_DBCONT.stringCallback.connect(self.update_Deblend)
        self.OBJECT_DBCONT.primeCallback()
        self.DeblendSelector.currentTextChanged.connect(self.set_Deblend)
        self.DeblendSelector.setEnabled(self.enable_control)

        # RAOffset
        self.RAOffset = self.findChild(QLineEdit, 'RAOffset')
        self.RAOffset.setEnabled(False)
        self.RAOffsetLabel = self.findChild(QLabel, 'RAOffsetLabel')
        self.RAOffsetLabel.setEnabled(False)

        # DECOffset
        self.DECOffset = self.findChild(QLineEdit, 'DECOffset')
        self.DECOffset.setEnabled(False)
        self.DECOffsetLabel = self.findChild(QLabel, 'DECOffsetLabel')
        self.DECOffsetLabel.setEnabled(False)

        # X Axis Control: TIPTILT_CONTROL_X
        self.XAxisControlValue = self.findChild(QLabel, 'XAxisControlValue')
        self.XAxisControl = self.findChild(QComboBox, 'XAxisControl')
        self.XAxisControl.addItems(['', 'Mirror', 'Bypass'])
        self.TIPTILT_CONTROL_X.stringCallback.connect(self.update_XAxisControl)
        self.TIPTILT_CONTROL_X.primeCallback()
        self.XAxisControl.currentTextChanged.connect(self.set_XAxisControl)
        self.XAxisControl.setEnabled(self.enable_control)

        # Y Axis Control: TIPTILT_CONTROL_Y
        self.YAxisControlValue = self.findChild(QLabel, 'YAxisControlValue')
        self.YAxisControl = self.findChild(QComboBox, 'YAxisControl')
        self.YAxisControl.addItems(['', 'Mirror', 'Bypass'])
        self.TIPTILT_CONTROL_Y.stringCallback.connect(self.update_YAxisControl)
        self.TIPTILT_CONTROL_Y.primeCallback()
        self.YAxisControl.currentTextChanged.connect(self.set_YAxisControl)
        self.YAxisControl.setEnabled(self.enable_control)

        # DAR Enabled: DAR_ENABLE
        self.DARCorrectionValue = self.findChild(QLabel, 'DARCorrectionValue')
        self.DAREnable = self.findChild(QComboBox, 'DAREnable')
        self.DAREnable.addItems(['', 'Yes', 'No'])
        self.DAR_ENABLE.stringCallback.connect(self.update_DAREnable)
        self.DAR_ENABLE.primeCallback()
        self.DAREnable.currentTextChanged.connect(self.set_DAREnable)
        self.DAREnable.setEnabled(self.enable_control)

        # Pixel Readout
        self.PixelReadout = self.findChild(QLabel, 'PixelReadout')

        # Pixel Target PIX_TARGET
        self.PixTargetValue = self.findChild(QLabel, 'PixTargetValue')

        # Script Status
        self.ScriptStatus = self.findChild(QLabel, 'ScriptValue')
        self.SCRIPTNAME.stringCallback.connect(self.ScriptStatus.setText)
        self.SCRIPTNAME.primeCallback()

        # Exposure Status
        self.ExposureStatus = self.findChild(QLabel, 'ExposureStatusValue')
        self.EXPOSE.stringCallback.connect(self.update_exposure_status_string)
        self.EXPOSE.primeCallback()
        self.ELAPSED.stringCallback.connect(self.update_exposure_status_string)
        self.ELAPSED.primeCallback()

        # FIU Mode
        self.FIUMode = self.findChild(QLabel, 'FIUModeValue')
        self.MODE.stringCallback.connect(self.FIUMode.setText)
        self.MODE.primeCallback()

        # OBJECT
        self.ObjectValue = self.findChild(QLabel, 'ObjectValue')
        self.OBJECT.stringCallback.connect(self.ObjectValue.setText)
        self.OBJECT.primeCallback()


    ##----------------------------------------------------------
    ## update Plots
    def update_plots(self):
        self.update_TipTiltErrorPlot()
        self.update_FluxPlot()


    ##----------------------------------------------------------
    ## update CONTINUOUS
    def update_CONTINUOUS(self, value):
        if value == 'Inactive':
            self.CONTINUOUSStatusLabel.setText('CONTINUOUS')
            self.CONTINUOUSStatusLabel.setStyleSheet('color: red;')
        else:
            self.CONTINUOUSStatusLabel.setText('')
            self.CONTINUOUSStatusLabel.setStyleSheet('color: black;')
        self.enable_control_and_telemetry(value == 'Active')

    ##----------------------------------------------------------
    ## update SAVE
    def update_SAVE(self, value):
        if value == 'Inactive':
            self.SAVEStatusLabel.setText('SAVE')
            self.SAVEStatusLabel.setStyleSheet('color: red;')
        else:
            self.SAVEStatusLabel.setText('')
            self.SAVEStatusLabel.setStyleSheet('color: black;')


    ##----------------------------------------------------------
    ## Enable/Disable Camera Control and Telemetry
    def enable_control_and_telemetry(self, enabled):
        self.CameraGain.setEnabled(enabled)
        self.CameraFPSValue.setEnabled(enabled)
        self.CameraFPSSelector.setEnabled(enabled)
        self.PeakFlux.setEnabled(enabled)
        self.TotalFlux.setEnabled(enabled)
        self.TipTiltFPS.setEnabled(enabled)
        self.TipTiltPhase.setEnabled(enabled)
        self.TipTiltError.setEnabled(enabled)
        self.ObjectChoice.setEnabled(enabled)
        self.TipTiltOnOffButton.setEnabled(enabled)
        self.CalculationCheckBox.setEnabled(enabled)
        self.ControlCheckBox.setEnabled(enabled)
        self.OffloadCheckBox.setEnabled(enabled)


    ##----------------------------------------------------------
    ## Quit
    def quit(self):
        log.info(f"Quitting KPF TipTilt GUI")
        sys.exit()

    ##----------------------------------------------------------
    ## Camera Gain
    def update_CameraGain(self, value):
        self.log.debug(f'update_CameraGain: {value}')
        self.CameraGainValue.setText(f'{value}')
        self.CameraGain.setCurrentText('')

    def set_CameraGain(self, value):
        if value != '':
            self.log.info(f'Modifying kpfguide.GAIN = {value}')
            self.GAIN.write(value)


    ##----------------------------------------------------------
    ## Camera FPS
    def update_CameraFPS(self, value):
        self.log.debug(f'update_CameraFPS: {value}')
        self.CameraFPSValue.setText(f"{float(value):.1f}")
        self.CameraFPSSelector.setCurrentText('')

    def set_CameraFPS(self, value):
        if value != '':
            self.log.info(f'Modifying kpfguide.FPS = {value}')
            self.FPS.write(value)


    ##----------------------------------------------------------
    ## Peak Flux
    def update_PeakFlux(self, value):
        self.log.debug(f'update_PeakFlux: {value}')
        self.peak_flux_value = float(value)
        if self.PeakFlux.isEnabled() == True:
            flux_string = f'{self.peak_flux_value:,.0f} ADU'
            self.PeakFlux.setText(f"{flux_string}")
            if self.peak_flux_value < self.VeryLowPeakFluxThreshold:
                style = f'color: red;'
            elif self.peak_flux_value < self.LowPeakFluxThreshold:
                style = f'color: yellow;'
            elif self.peak_flux_value > self.HighPeakFluxThreshold:
                style = f'color: red;'
            else:
                style = f'color: limegreen;'
            self.PeakFlux.setStyleSheet(style)

    ##----------------------------------------------------------
    ## Total Flux
    def update_TotalFlux(self, value):
        self.log.debug(f'update_TotalFlux: {value}')
        if self.TotalFlux.isEnabled() == True:
            flux = float(value)
            flux_string = f'{flux:,.0f}'
            self.TotalFlux.setText(f"{flux_string}")
            if flux < self.VeryLowFluxThreshold:
                style = f'color: red;'
            elif flux < self.LowFluxThreshold:
                style = f'color: yellow;'
            elif flux > self.HighFluxThreshold:
                style = f'color: red;'
            else:
                style = f'color: limegreen;'
            self.TotalFlux.setStyleSheet(style)

            ts = datetime.datetime.now()
            if len(self.ObjectFluxTimes) == 0:
                self.ObjectFluxTime0 = ts
            new_ts_value = (ts-self.ObjectFluxTime0).total_seconds()
            self.ObjectFluxTimes.append(new_ts_value)
            self.ObjectFluxValues.append(flux)


    def set_FluxPlotTime(self, value):
        self.FluxPlotAgeThreshold = float(value)

    def update_FluxPlot(self):
        npoints = len(self.ObjectFluxValues)
        fig = plt.figure(num=2)
        ax = fig.gca()
        ax.clear()
        plt.title('Flux')
        if npoints <= 1:
            log.debug('update_FluxPlot: clearing plot')
            ax.set_ylim(0,1e6)
            plt.yticks([])
            plt.xticks([])
            ax.grid('major', alpha=0.4)
            ax.tick_params(axis='both', direction='in')
            plt.xlabel(f'Last {self.FluxPlotAgeThreshold} s')
            self.FluxPlotCanvas.draw()
        else:
            tick = datetime.datetime.utcnow()
            log.debug('update_FluxPlot')
            recent = np.where(np.array(self.ObjectFluxTimes) > self.ObjectFluxTimes[-1]-self.FluxPlotAgeThreshold)[0]
            flux_times = np.array(self.ObjectFluxTimes)[recent]
            flux = np.array(self.ObjectFluxValues)[recent]
            n_plot_points = len(flux)

            ax.plot(flux_times, flux, 'ko', ms=2)
            if len(flux) == 0:
                ax.set_ylim(0,1e6)
            else:
                max_flux = max(flux)
                if max_flux > 0:
                    ax.set_ylim(0, 1.2*max_flux)
                else:
                    ax.set_ylim(0,1e6)
            plt.xticks([])
            plt.yticks([])
            ax.grid('major')
            plt.xlabel(f'Last {self.FluxPlotAgeThreshold} s')
            plt.xlim(max(flux_times)-self.FluxPlotAgeThreshold, max(flux_times))
            self.FluxPlotCanvas.draw()
            tock = datetime.datetime.utcnow()
            elapsed = (tock-tick).total_seconds()
            log.debug(f'  Plotted {npoints} Flux points in {elapsed*1000:.0f} ms')



    ##----------------------------------------------------------
    ## Tip Tilt Phase
    def update_TipTiltPhase(self, value):
        self.log.debug(f'update_TipTiltPhase: {value}')
        if self.TipTiltPhase.isEnabled() == True:
            self.TipTiltPhase.setText(f"{value}")
            if value == 'Idle':
                style = f'color: black;'
            elif value == 'Identifying':
                style = f'color: red;'
            elif value == 'Acquiring':
                style = f'color: yellow;'
            elif value == 'Tracking':
                style = f'color: limegreen;'
            self.TipTiltPhase.setStyleSheet(style)


    ##----------------------------------------------------------
    ## Tip Tilt FPS
    def update_TipTiltFPS(self, value):
        self.log.debug(f'update_TipTiltFPS: {value}')
        if self.TipTiltFPS.isEnabled() == True:
            fps = float(value)
            fps_string = f'{fps:.1f}'
            self.TipTiltFPS.setText(f"{fps_string}")
            if fps_string == '0.0':
                style = f'color: black;'
            else:
                camera_fps = self.FPS.ktl_keyword.binary
                delta_fps = abs(camera_fps - fps)
                if delta_fps/camera_fps > 0.1:
                    style = f'color: red;'
                else:
                    style = f'color: limegreen;'
            self.TipTiltFPS.setStyleSheet(style)


    ##----------------------------------------------------------
    ## Tip Tilt Error
    def update_TipTiltError(self, value):
        self.log.debug(f'update_TipTiltError: {value}')
        err = float(value)
        err_string = f'{err:.1f}'
        self.TipTiltError.setText(f"{err_string} pix")

        # X and Y Error from OBJECT position
        if self.OBJECT_CHOICE.ktl_keyword.binary != 0:
            self.TipTiltErrorValues.append(err)
            ts = datetime.datetime.fromtimestamp(self.TIPTILT_ERROR.ktl_keyword.timestamp)
            if len(self.TipTiltErrorTimes) == 0:
                self.TipTiltErrorTime0 = ts
            new_ts_value = (ts-self.TipTiltErrorTime0).total_seconds()
            self.TipTiltErrorTimes.append(new_ts_value)

            OBJECT = getattr(self, self.OBJECT_CHOICE.ktl_keyword.ascii)
            x, y, flux, hitrate = OBJECT.ktl_keyword.binary
            pix_target = self.PIX_TARGET.ktl_keyword.binary
            self.StarPositionError.append((x-pix_target[0], y-pix_target[1]))
            ts = datetime.datetime.fromtimestamp(OBJECT.ktl_keyword.timestamp)
            if len(self.StarPositionTimes) == 0:
                self.StarPositionTime0 = ts
            new_ts_value = (ts-self.StarPositionTime0).total_seconds()
            self.StarPositionTimes.append(new_ts_value)


    def set_TTErrPlotTime(self, value):
        self.TipTiltErrorPlotAgeThreshold = float(value)


    def update_TipTiltErrorPlot(self):
        npoints = len(self.TipTiltErrorValues)
        fig = plt.figure(num=1)
        ax = fig.gca()
        ax.clear()
        plt.title('Tip Tilt Error')
        if npoints <= 1:
            log.debug('update_TipTiltErrorPlot: clearing plot')
            ax.set_ylim(-3,3)
            plt.yticks([-2,0,2])
            plt.xticks([])
            ax.grid('major', alpha=0.4)
            ax.tick_params(axis='both', direction='in')
            plt.xlabel(f'Last {self.TipTiltErrorPlotAgeThreshold} s')
            self.TipTiltErrorPlotCanvas.draw()
        else:
            tick = datetime.datetime.utcnow()
            log.debug('update_TipTiltErrorPlot')

            recent = np.where(np.array(self.TipTiltErrorTimes) > self.TipTiltErrorTimes[-1]-self.TipTiltErrorPlotAgeThreshold)[0]
            tterr_times = np.array(self.TipTiltErrorTimes)[recent]
            tterr = np.array(self.TipTiltErrorValues)[recent]
            n_plot_points = len(tterr)

            recent_starpos = np.where(np.array(self.TipTiltErrorTimes) > self.TipTiltErrorTimes[-1]-self.TipTiltErrorPlotAgeThreshold)[0]
            if len(self.StarPositionError) > 0:
                starpos_xerr = np.array(self.StarPositionError)[:,0][recent_starpos]
                starpos_yerr = np.array(self.StarPositionError)[:,1][recent_starpos]
                starpos_times = np.array(self.StarPositionTimes)[recent_starpos]
                n_plot_points += len(starpos_xerr)
                n_plot_points += len(starpos_yerr)

            ax.plot(tterr_times, tterr, 'k-', ms=2, drawstyle='steps')
            if len(self.StarPositionError) > 0:
                ax.plot(starpos_times, starpos_xerr, 'gx', ms=4, alpha=0.5)
                ax.plot(starpos_times, starpos_yerr, 'bv', ms=4, alpha=0.5)
            ax.axhline(y=0, xmin=0, xmax=1, color='k', alpha=0.8)
            try:
                ax.set_ylim(min([min(starpos_xerr), min(starpos_yerr)])-0.5,
                            max([max(starpos_xerr), max(starpos_yerr), max(tterr)])+0.5)
            except:
                ax.set_ylim(-3,3)
            plt.xticks([])
            ax.grid('major')
            plt.xlabel(f'Last {self.TipTiltErrorPlotAgeThreshold} s')
            plt.xlim(max(tterr_times)-self.TipTiltErrorPlotAgeThreshold, max(tterr_times))
            self.TipTiltErrorPlotCanvas.draw()
            tock = datetime.datetime.utcnow()
            elapsed = (tock-tick).total_seconds()
            log.debug(f'  Plotted {npoints} points in {elapsed*1000:.0f} ms')


    ##----------------------------------------------------------
    ## Mirror Position
    def update_ttxsrv(self, value):
        self.log.debug(f'update_ttxsrv: {value}')
        if value == 'Open':
            self.TTXSRVStatusLabel.setText('TTXSRV')
            self.TTXSRVStatusLabel.setStyleSheet('color: red;')
        else:
            self.TTXSRVStatusLabel.setText('')
            self.TTXSRVStatusLabel.setStyleSheet('color: black;')
        self.enable_control_and_telemetry(value == 'Closed')

    def update_ttysrv(self, value):
        self.log.debug(f'update_ttysrv: {value}')
        if value == 'Open':
            self.TTYSRVStatusLabel.setText('TTYSRV')
            self.TTYSRVStatusLabel.setStyleSheet('color: red;')
        else:
            self.TTYSRVStatusLabel.setText('')
            self.TTYSRVStatusLabel.setStyleSheet('color: black;')
        self.enable_control_and_telemetry(value == 'Closed')

    def update_mirror_pos_x(self, value):
        self.log.debug(f'update_mirror_pos_x: {value}')
        self.MirrorPosX.append(float(value))
        if len(self.MirrorPosX) > self.MirrorPosCount:
            self.MirrorPosX.pop(0)

    def update_mirror_pos_y(self, value):
        self.log.debug(f'update_mirror_pos_y: {value}')
        self.MirrorPosY.append(float(value))
        if len(self.MirrorPosY) > self.MirrorPosCount:
            self.MirrorPosY.pop(0)

    def update_MirrorPositionPlot(self):
        npoints = (len(self.MirrorPosX), len(self.MirrorPosY))
        tick = datetime.datetime.utcnow()
        self.log.debug('update_MirrorPositionPlot')
        if len(self.MirrorPosX) > 0 and len(self.MirrorPosY) > 0:
            mp_fig = plt.figure(num=4)
            mp_ax = mp_fig.gca()
            #mp_ax.set_aspect('equal')
            mp_ax.clear()
            okregion = matplotlib.patches.Rectangle((self.tthome[0]-self.ttxrange,
                                     self.tthome[1]-self.ttyrange),
                                     2*self.ttxrange, 2*self.ttyrange,
                                     alpha=0.2, color='g')
            mp_ax.add_artist(okregion)
            for i,xy in enumerate(zip(self.MirrorPosX, self.MirrorPosY)):
                mp_ax.plot(xy[0], xy[1], 'bo', ms=2, alpha=self.MirrorPosAlpha[i])
            mp_ax.plot(self.tthome[0], self.tthome[1], 'r+', alpha=0.3)
#             mp_ax.set_xlim([-17,17])
            mp_ax.set_xlim([-22,22])
            mp_ax.set_ylim([-26,26])
            mp_ax.tick_params(axis='both', direction='in')
            mp_ax.grid('major', alpha=0.4)
            mp_ax.set_xticks([-20,-10,0,10,20])
            mp_ax.set_yticks([-20,-10,0,10,20])
            mp_ax.set_xticklabels([])
            mp_ax.set_yticklabels([])
            self.MirrorPositionCanvas.draw()
            tock = datetime.datetime.utcnow()
            elapsed = (tock-tick).total_seconds()
            log.debug(f'  Plotted {npoints} points in {elapsed*1000:.0f} ms')


    ##----------------------------------------------------------
    ## Object Choice
    def update_ObjectChoice(self, value):
        self.log.debug(f'update_ObjectChoice: {value}')
        self.ObjectChoiceValue.setText(f"{value}")
        self.ObjectChoice.setCurrentText('')

    def set_ObjectChoice(self, value):
        self.log.debug(f'set_ObjectChoice: {value} ({type(value)})')
        if value != self.OBJECT_CHOICE.ktl_keyword.ascii and value in ['OBJECT1', 'OBJECT2', 'OBJECT3']:
            self.log.info(f'Modifying kpfguide.OBJECT_CHOICE = {value}')
            self.OBJECT_CHOICE.write(f'{value}')
        else:
            self.log.debug(f'No change to kpfguide.OBJECT_CHOICE')


    ##----------------------------------------------------------
    ## Tip Tilt On/Off
    def toggle_all_loops(self, value):
        self.log.debug(f'button clicked toggle_all_loops: {value}')
        current_kw_value = self.ALL_LOOPS.ktl_keyword.ascii
        if current_kw_value in ['Inactive', 'Mixed']:
            self.log.info(f'Modifying kpfguide.ALL_LOOPS = Active')
            self.ALL_LOOPS.write('Active')
        elif current_kw_value == 'Active':
            self.log.info(f'Modifying kpfguide.ALL_LOOPS = Inactive')
            self.ALL_LOOPS.write('Inactive')


    ##----------------------------------------------------------
    ## Tip Tilt Calculations
    def update_TipTiltCalc(self, intvalue):
        self.log.info(f'update_TipTiltCalc: {intvalue} ({type(intvalue)})')
        self.CalculationCheckBox.setChecked(intvalue)
        if intvalue == 0:
            self.TipTiltErrorValues = []
            self.StarPositionError = []
            self.TipTiltErrorTimes = []
            self.TipTiltErrorTime0 = None
            self.ObjectFluxValues = []
            self.ObjectFluxTimes = []
            self.ObjectFluxTime0 = None

    def TipTiltCalc_state_change(self, value):
        requested = {'2': 'Active', '0': 'Inactive'}[str(value)]
        current_value = self.TIPTILT_CALC.ktl_keyword.ascii
        self.log.debug(f'TipTiltCalc_state_change: {value} {requested} ({current_value})')
        if requested != current_value:
            self.log.info(f'Modifying kpfguide.TIPTILT_CALC = {requested}')
            self.TIPTILT_CALC.write(requested)
        else:
            self.log.debug(f'No change to kpfguide.TIPTILT_CALC')


    ##----------------------------------------------------------
    ## Tip Tilt Control
    def update_TipTiltControl(self, value):
        self.log.debug(f'update_TipTiltControl: {value}')
        self.ControlCheckBox.setChecked(value == 'Active')

    def TipTiltControl_state_change(self, value):
        requested = {'2': 'Active', '0': 'Inactive'}[str(value)]
        self.log.debug(f'TipTiltControl_state_change: {value} {requested}')
        current_value = self.TIPTILT_CONTROL.ktl_keyword.ascii
        if requested != current_value:
            self.log.info(f'Modifying kpfguide.TIPTILT_CONTROL = {requested}')
            self.TIPTILT_CONTROL.write(requested)
        else:
            self.log.debug(f'No change to kpfguide.TIPTILT_CONTROL')


    ##----------------------------------------------------------
    ## Offload
    def update_Offload(self, value):
        self.log.debug(f'update_Offload: {value}')
        self.OffloadCheckBox.setChecked(value == 'Active')

    def update_OffloadDCS(self, value):
        self.log.debug(f'update_OffloadDCS: {value}')
        if value == 'Yes':
            self.OffloadCheckBox.setStyleSheet('color: black;')
            self.OffloadCheckBox.setToolTip('OFFLOAD_DCS is Yes')
        else:
            self.OffloadCheckBox.setStyleSheet('color: red;')
            self.OffloadCheckBox.setToolTip('OFFLOAD_DCS is No')

    def Offload_state_change(self, value):
        requested = {'2': 'Active', '0': 'Inactive'}[str(value)]
        self.log.debug(f'Offload_state_change: {value} {requested}')
        # Try to re-enable OFFLOAD_DCS if it is not Yes
        if requested == 'Active' and self.OFFLOAD_DCS.ktl_keyword.ascii == 'No':
            self.log.info(f'Modifying kpfguide.OFFLOAD_DCS = Yes')
            self.OFFLOAD_DCS.write('Yes')
        self.log.info(f'Modifying kpfguide.OFFLOAD = {requested}')
        self.OFFLOAD.write(requested)


    ##----------------------------------------------------------
    ## Detect SNR
    def update_DetectSNR(self, value):
        self.log.debug(f'update_DetectSNR: {value}')
        self.DetectSNRValue.setText(f"{float(value):.1f}")
        self.DetectSNRSelector.setCurrentText('')

    def set_DetectSNR(self, value):
        if value != '':
            self.log.info(f'Modifying kpfguide.OBJECT_INTENSITY = {value}')
            self.OBJECT_INTENSITY.write(value)


    ##----------------------------------------------------------
    ## Detect Area
    def update_DetectArea(self, value):
        self.log.debug(f'update_DetectArea: {value}')
        self.DetectAreaValue.setText(f"{int(value):d}")
        self.DetectAreaSelector.setCurrentText('')

    def set_DetectArea(self, value):
        if value != '':
            self.log.info(f'Modifying kpfguide.OBJECT_AREA = {value}')
            self.OBJECT_AREA.write(value)


    ##----------------------------------------------------------
    ## Deblend
    def update_Deblend(self, value):
        self.log.debug(f'update_Deblend: {value}')
        self.DeblendValue.setText(f"{float(value):5.3f}")
        self.DeblendSelector.setCurrentText('')

    def set_Deblend(self, value):
        if value != '':
            self.log.info(f'Modifying kpfguide.OBJECT_DBCONT = {value}')
            self.OBJECT_DBCONT.write(value)


    ##----------------------------------------------------------
    ## XAxisControl
    def update_XAxisControl(self, value):
        self.log.debug(f'update_XAxisControl: {value}')
        color = {'Mirror': 'green', 'Bypass': 'orange'}[value]
        self.XAxisControlValue.setText(f"{value}")
        self.XAxisControlValue.setStyleSheet(f'color: {color};')
        self.XAxisControl.setCurrentText('')
        if value == 'Bypass':
            self.XAxisStatusLabel.setText(f"X Axis: Offloads Only (Slow)")
        else:
            self.XAxisStatusLabel.setText(f"")
        self.XAxisStatusLabel.setStyleSheet(f'color: {color};')

    def set_XAxisControl(self, value):
        if value != '':
            self.log.info(f'Modifying kpfguide.TIPTILT_CONTROL_X = {value}')
            self.TIPTILT_CONTROL_X.write(value)


    ##----------------------------------------------------------
    ## YAxisControl
    def update_YAxisControl(self, value):
        self.log.debug(f'update_YAxisControl: {value}')
        color = {'Mirror': 'green', 'Bypass': 'orange'}[value]
        self.YAxisControlValue.setText(f"{value}")
        self.YAxisControlValue.setStyleSheet(f'color: {color};')
        self.YAxisControl.setCurrentText('')
        if value == 'Bypass':
            self.YAxisStatusLabel.setText(f"Y Axis: Offloads Only (Slow)")
        else:
            self.YAxisStatusLabel.setText(f"")
        self.YAxisStatusLabel.setStyleSheet(f'color: {color};')

    def set_YAxisControl(self, value):
        if value != '':
            self.log.info(f'Modifying kpfguide.TIPTILT_CONTROL_Y = {value}')
            self.TIPTILT_CONTROL_Y.write(value)


    ##----------------------------------------------------------
    ## DAREnable
    def update_DAREnable(self, value):
        self.log.debug(f'update_DAREnable: {value}')
        color = {'Yes': 'green', 'No': 'red'}[value]
        self.DARCorrectionValue.setText(f"{value}")
        self.DARCorrectionValue.setStyleSheet(f'color: {color};')
        self.DAREnable.setCurrentText('')
        if value == 'No':
            self.DARStatusLabel.setText(f"DAR Disbabled")
        else:
            self.DARStatusLabel.setText(f"")
        self.DARStatusLabel.setStyleSheet(f'color: {color};')
        self.load_file(self.LASTFILE.ktl_keyword.ascii)

    def set_DAREnable(self, value):
        if value != '':
            self.log.info(f'Modifying kpfguide.DAR_ENABLE = {value}')
            self.DAR_ENABLE.write(value)


    ##----------------------------------------------------------
    ## Exposure Status
    def update_exposure_status_string(self, value):
        status = self.EXPOSE.ktl_keyword.ascii
        elapsed = self.ELAPSED.ktl_keyword.binary
        exptime = self.EXPOSURE.ktl_keyword.binary
        exposure_status_string = f"{status} ({elapsed:.0f}/{exptime:.0f} s)"
        self.ExposureStatus.setText(exposure_status_string)


    ##----------------------------------------------------------
    ## Ginga Image Display Tools
    def set_ImageCut(self, value):
        self.log.info(f"set_ImageCut: {value}")
        match_hist = re.match('histogram (\d\d\.?\d?)', value)
        if match_hist is None:
            self.ImageViewer.set_autocut_params(value)
        else:
            pct = float(match_hist.group(1))/100
            self.ImageViewer.set_autocut_params('histogram', pct=pct)

    def set_ImageScaling(self, value):
        self.log.info(f"set_ImageScaling: {value}")
        # >>> ginga.imap.get_names()
        # ['equa', 'expo', 'gamma', 'jigsaw', 'lasritt', 'log', 'neg', 'neglog', 'null', 'ramp', 'stairs', 'ultrasmooth']
        ginga_name = {'log': 'log',
                      'neglog': 'neglog',
                      'linear': 'ramp',
                      }[value]
        self.ImageViewer.set_intensity_map(ginga_name)

    def refresh_guide_geometry_parameters(self):
        roidim  = int(self.TIPTILT_ROIDIM.ktl_keyword.binary/2) # Use half width
        pix_target = self.PIX_TARGET.ktl_keyword.binary
        self.xcent, self.ycent = np.array(np.round(pix_target), dtype=int)
        if pix_target[0] < 0 or pix_target[0] > 640 or pix_target[1] < 0 or pix_target[1] > 512:
            self.PixTargetValue.setText(f"Out Of Range")
            self.PixTargetValue.setStyleSheet(f'color: red;')
        else:
            self.PixTargetValue.setText(f"{pix_target[0]:.1f}, {pix_target[1]:.1f}")
            self.PixTargetValue.setStyleSheet(f'color: black;')

    def load_file(self, filepath):
        try:
            filepath = Path(filepath)
        except:
            log.warning(f'Unable to parse file: {filepath}')
            return

        roidim  = int(self.TIPTILT_ROIDIM.ktl_keyword.binary/2) # Use half width
        tick = datetime.datetime.utcnow()
        if filepath.exists() is False:
            self.log.debug(f"Could not find file: {filepath}")
        elif filepath.is_dir() is True:
            self.log.debug(f"File is a directory: {filepath}")
        else:
            self.log.debug(f"Loading FITS file: {filepath}")
            hdul = fits.open(filepath, output_verify='silentfix')
            # Crop Image
            # Scale to an individual frame
            stack = hdul[0].header.get('FRAM_STK')
            self.refresh_guide_geometry_parameters()
            x0 = self.xcent-roidim
            x1 = self.xcent+roidim
            y0 = self.ycent-roidim
            y1 = self.ycent+roidim
            cropped = CCDData(data=hdul[0].data[y0:y1,x0:x1]/stack,
                              header=hdul[0].header, unit='adu')
            date_beg = hdul[0].header.get('DATE-BEG')
            ts = datetime.datetime.strptime(date_beg, '%Y-%m-%dT%H:%M:%S.%f')
            self.LastFileValue.setText(f"{filepath.name} ({date_beg} UT)")
    
            TipTiltCalc = self.TIPTILT_CALC.ktl_keyword.ascii
            ObjectChoice = self.OBJECT_CHOICE.ktl_keyword.ascii
            image = AstroImage()
            image.load_nddata(cropped)
            self.ImageViewer.set_image(image)
    
            self.overlay_objects()
            tock = datetime.datetime.utcnow()
            elapsed = (tock-tick).total_seconds()
            log.debug(f'  Image loaded in {elapsed*1000:.0f} ms')


    def update_lastfile(self, value):
        p = Path(value)
        if p.exists() is False:
            log.error(f'{p} not found')
        else:
            self.load_file(f"{p}")

    def overlay_objects(self):
        roidim = int(self.TIPTILT_ROIDIM.ktl_keyword.binary/2) # Use half width
        pix_target = self.PIX_TARGET.ktl_keyword.binary
        self.add_mark(pix_target[0]-self.xcent+roidim,
                      pix_target[1]-self.ycent+roidim,
                      'crosshair', tag='PIX_TARGET',
                      label=False,
                      color='red', alpha=0.5)

        for obj in [1,2,3]:
            objectN_kfo = getattr(self, f'OBJECT{obj}')
            objectN = objectN_kfo.ktl_keyword.binary
            if objectN[0] > -998:
                color = {1: 'blue', 2: 'green', 3: 'red'}[obj]
                flux = objectN[2]
                hits = objectN[3]
                self.add_mark(objectN[0]-self.xcent+roidim,
                              objectN[1]-self.ycent+roidim,
                              'circle', tag=f'OBJECT{obj}',
                              label=f"OBJ{obj}: {hits:.0%}",
                              color=color, radius=10, alpha=0.8)
            else:
                self.overlay_canvas.delete_objects_by_tag([f'OBJECT{obj}', f"OBJECT{obj}_TEXT", f"OBJECT{obj}_point"])

    def add_mark(self, x, y, marker,
                 tag=None, label=True, dxtext=-10, dytext=3, **kwargs):
        Marker = self.overlay_canvas.get_draw_class(marker)
        self.overlay_canvas.delete_objects_by_tag([tag, f"{tag}_TEXT", f"{tag}_point"])
        if marker == 'crosshair' and label == False:
            self.overlay_canvas.add(Marker(x, y, text='', **kwargs), tag=tag)
        elif marker == 'circle':
            if 'radius' in kwargs.keys():
                if kwargs['radius'] > 5:
                    self.overlay_canvas.add(Marker(x, y, **kwargs), tag=tag)
                    Point = self.overlay_canvas.get_draw_class('point')
                    point_kwargs = copy.deepcopy(kwargs)
                    point_kwargs['radius'] = 2
                    self.overlay_canvas.add(Point(x, y, **point_kwargs), tag=f"{tag}_point")
        else:
            self.overlay_canvas.add(Marker(x, y, **kwargs), tag=tag)

        if label != False:
            if label is True:
                text = tag
            else:
                text = label
            if 'radius' in kwargs.keys():
                dytext += kwargs['radius']
            Text = self.overlay_canvas.get_draw_class('text')
            self.overlay_canvas.add(Text(x+dxtext, y+dytext, text, **kwargs),
                                    tag=f"{tag}_TEXT")


    def cursor_position_update(self, viewer, button, data_x, data_y):
        roidim = int(self.TIPTILT_ROIDIM.ktl_keyword.binary/2) # Use half width
        pix_target = self.PIX_TARGET.ktl_keyword.binary
        try:
            # We report the value across the pixel, even though the coords
            # change halfway across the pixel
            value = viewer.get_data(int(data_x + viewer.data_off),
                                    int(data_y + viewer.data_off))
            value = int(value)

            

            fits_x = pix_target[0] - roidim + data_x + 1
            fits_y = pix_target[1] - roidim + data_y + 1
            text = f"X: {fits_x:.0f}, Y: {fits_y:.0f}, value: {value:d}"
            #text = f"pixel value: {value:d}"
            self.PixelReadout.setText(text)

        except Exception:
            value = None

    ##----------------------------------------------------------
    ## Restarting kpfguide dispatchers
    def run_restart_kpfguide1(self):
        self.run_restart_kpfguide_popup(1)

    def run_restart_kpfguide2(self):
        self.run_restart_kpfguide_popup(2)

    def run_restart_kpfguide3(self):
        self.run_restart_kpfguide_popup(3)

    def run_restart_kpfguide_popup(self, num):
        self.log.debug(f"run_restart_kpfguide_popup{num}")
        restart_kpfguide_popup = QMessageBox()
        restart_kpfguide_popup.setWindowTitle(f'Restart kpfguide{num} Confirmation')
        restart_kpfguide_popup.setText(f"Do you really want to restart kpfguide{num}?")
        restart_kpfguide_popup.setIcon(QMessageBox.Critical)
        restart_kpfguide_popup.setStandardButtons(QMessageBox.No | QMessageBox.Yes) 
        bttn = restart_kpfguide_popup.exec_()
        if bttn == QMessageBox.Yes:
            self.log.debug(f'restart_kpfguide{num} confirmed')
            self.restart_kpfguide(num)
        else:
            self.log.debug(f'restart_kpfguide{num} cancelled')
            return False


    def restart_kpfguide(self, num):
        self.log.warning(f"Recieved request to restart kpfguide{num}")
        restart_kpfguide_cmd = f'kpf restart kpfguide{num} ; echo "Done!" ; sleep 5'
        # Pop up an xterm with the script running
        xterm_cmd = ['xterm',
                     '-title', f'restart kpfguide{num}',
                     '-name', f'restart kpfguide{num}',
                     '-fn', '10x20', '-bg', 'black', '-fg', 'white',
                     '-e', f'{restart_kpfguide_cmd}']
        self.log.warning(f"Launching: {xterm_cmd}")
        proc = subprocess.Popen(xterm_cmd)

# end of class MainWindow


if __name__ == '__main__':
    log = create_GUI_log()
    log.info(f"Starting KPF TipTilt GUI")
    pid = os.getpid()
    log.info(f"  PID = {pid}")
    try:
        main(log)
    except Exception as e:
        log.error(e)
        log.error(traceback.format_exc())
    log.info(f"Exiting KPF TipTilt GUI")

