import time

import ktl

import numpy as np

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.fiu.InitializeTipTilt import InitializeTipTilt
from kpf.fiu.ShutdownTipTilt import ShutdownTipTilt


class MeasureTipTiltMirrorRange(KPFTranslatorFunction):
    '''
    
    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        # Measure tip tilt ranges
        log.info('Beginning MeasureTipTiltMirrorRange')
        InitializeTipTilt.execute({})

        movetime = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
        tol = cfg.getfloat('tolerances', 'tip_tilt_move_tolerance', fallback=0.1)

        kpffiu = ktl.cache('kpffiu')

        measured_range = {}
        axis = ['X', 'Y']
        rawvals = {}
        update_ax = {'X': False, 'Y': False}
        for i,ax in enumerate(axis):
            nominal_range = {'X': 15.9, 'Y': 24.6}[ax]
            home = 0
            measured_range[ax] = [-nominal_range, nominal_range]
            rawvals[ax] = [None, None]

            commanded_position = home-nominal_range
            log.info(f"Sending TT{ax}VAX to {commanded_position}")
            kpffiu[f'TT{ax}VAX'].write(commanded_position)
            time.sleep(movetime*100)
            current_position = kpffiu[f'TT{ax}VAX'].read(binary=True)
            if abs(current_position-commanded_position) < tol:
                log.info(f"{ax} reached nominal range: {commanded_position}")
                measured_range[ax][0] = -nominal_range
            else:
                log.error(f"{ax} failed to reach {commanded_position}: {current_position:.2f}")
                measured_range[ax][0] = -np.floor(abs(current_position)*10)/10
                update_ax[ax] = True
            rawvals[ax][0] = kpffiu[f"TT{ax}RAW"].read(binary=True)

            commanded_position = home+nominal_range
            log.info(f"Sending TT{ax}VAX to {commanded_position}")
            kpffiu[f'TT{ax}VAX'].write(commanded_position)
            time.sleep(movetime*100)
            current_position = kpffiu[f'TT{ax}VAX'].read(binary=True)
            if abs(current_position-commanded_position) < tol:
                log.info(f"{ax} reached nominal range: {commanded_position}")
                measured_range[ax][1] = nominal_range
            else:
                log.error(f"{ax} failed to reach {commanded_position}: {current_position:.2f}")
                measured_range[ax][1] = np.floor(abs(current_position)*10)/10
                update_ax[ax] = True
            rawvals[ax][1] = kpffiu[f"TT{ax}RAW"].read(binary=True)

            time.sleep(movetime*100)
            InitializeTipTilt.execute({})
            time.sleep(movetime*100)

        ShutdownTipTilt.execute({})
        log.info(f"Measured X range: {measured_range['X']}")
        log.info(f"Measured Y range: {measured_range['Y']}")

        if update_ax['X'] is True:
            xrange = (max(measured_range['X']) - min(measured_range['X']))/2
            print(f"modify -s kpfguide TIPTILT_XRANGE={xrange:.1f}")
            new_RON = np.mean(rawvals['X'])
            print(f"modify -s kpffiu TTXRON='|{new_RON:.0f}|0|Home'")
        if update_ax['Y'] is True:
            yrange = (max(measured_range['Y']) - min(measured_range['Y']))/2
            print(f"modify -s kpfguide TIPTILT_YRANGE={yrange:.1f}")
            new_RON = np.mean(rawvals['Y'])
            print(f"modify -s kpffiu TTYRON='|{new_RON:.0f}|0|Home'")
        if update_ax['Y'] is True or update_ax['X'] is True:
            new_home = [np.mean(measured_range['X']), np.mean(measured_range['Y'])]
            print(f"modify -s kpfguide TIPTILT_HOME='{new_home[0]:.1f} {new_home[1]:.1f}'")

        return measured_range


    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass