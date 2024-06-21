import time

import ktl

import numpy as np

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.fiu.InitializeTipTilt import InitializeTipTilt
from kpf.fiu.ShutdownTipTilt import ShutdownTipTilt


class TestTipTiltMirrorRange(KPFTranslatorFunction):
    '''Verify if the tip tilt system is reaching the nominal range. Output is
    only via log messages.

    KTL Keywords Used:

    - `kpffiu.TTXVAX`
    - `kpffiu.TTYVAX`
    - `kpfguide.TIPTILT_HOME`
    - `kpfguide.TIPTILT_XRANGE`
    - `kpfguide.TIPTILT_YRANGE`

    Scripts Called:

    - `kpf.fiu.InitializeTipTilt`
    - `kpf.fiu.ShutdownTipTilt`
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        # Measure tip tilt ranges
        log.info('Beginning TestTipTiltMirrorRange')
        InitializeTipTilt.execute({})

        movetime = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
        tol = cfg.getfloat('tolerances', 'tip_tilt_move_tolerance', fallback=0.1)

        kpffiu = ktl.cache('kpffiu')
        kpfguide = ktl.cache('kpfguide')

        axis = ['X', 'Y']
        for i,ax in enumerate(axis):
            nominal_range = kpfguide[f'TIPTILT_{ax}RANGE'].read(binary=True)
            home = kpfguide['TIPTILT_HOME'].read(binary=True)[i]

            commanded_position = home-nominal_range
            log.info(f"Sending TT{ax}VAX to {commanded_position}")
            kpffiu[f'TT{ax}VAX'].write(commanded_position)
            time.sleep(movetime*100)
            current_position = kpffiu[f'TT{ax}VAX'].read(binary=True)
            if abs(current_position-commanded_position) < tol:
                log.info(f"{ax} reached nominal range: {commanded_position}")
            else:
                log.error(f"{ax} failed to reach {commanded_position}: {current_position}")

            commanded_position = home+nominal_range
            log.info(f"Sending TT{ax}VAX to {commanded_position}")
            kpffiu[f'TT{ax}VAX'].write(commanded_position)
            time.sleep(movetime*100)
            current_position = kpffiu[f'TT{ax}VAX'].read(binary=True)
            if abs(current_position-commanded_position) < tol:
                log.info(f"{ax} reached nominal range: {commanded_position}")
            else:
                log.error(f"{ax} failed to reach {commanded_position}: {current_position}")

            time.sleep(movetime*100)
            InitializeTipTilt.execute({})
            time.sleep(movetime*100)

        ShutdownTipTilt.execute({})


    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass