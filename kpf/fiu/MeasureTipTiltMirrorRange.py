import time

import ktl

import numpy as np

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.fiu.InitializeTipTilt import InitializeTipTilt
from kpf.fiu.ShutdownTipTilt import ShutdownTipTilt


def check_move(ax, commanded_position, sleeptime=1, tol=0.1):
    kpffiu = ktl.cache('kpffiu')
    try:
        kpffiu[f'TT{ax}VAX'].write(commanded_position)
    except:
        time.sleep(sleeptime)
        kpffiu[f'TT{ax}VAX'].write(commanded_position)
    time.sleep(sleeptime)
    current_position = kpffiu[f'TT{ax}VAX'].read(binary=True)
    if abs(current_position-commanded_position) < tol:
        log.info(f"  TT{ax}VAX reached {commanded_position:.2f}")
        return None
    else:
        log.info(f"  TT{ax}VAX only reached {current_position:.2f}")
        return current_position 


def find_new_limit(ax, commanded_position, n=5,
                   sleeptime=1, tol=0.1, margin=1):
    kpffiu = ktl.cache('kpffiu')
    tthome = ktl.cache('kpfguide', 'TIPTILT_HOME')
    axid = {'X': 0, 'Y': 1}[ax]
    home = tthome.read(binary=True)[axid]
    limits = []
    deltas = []
    log.info(f'Finding move limit for TT{ax}VAX toward {commanded_position:.1f}')
    for i in range(n):
        log.info(f"  Commanding TT{ax}VAX to {commanded_position:.2f} ({i+1}/{n})")
        measured_limit = check_move(ax, commanded_position)
        if measured_limit is not None:
            limits.append(measured_limit)
            deltas.append(home-measured_limit)
        # Send home
        try:
            kpffiu[f'TT{ax}VAX'].write(home)
        except:
            time.sleep(sleeptime)
            kpffiu[f'TT{ax}VAX'].write(home)
        time.sleep(sleeptime)

    if len(limits) == 0:
        return None
    else:
        log.info(f"Move failed on {len(limits)}/{n} moves")
#         print(commanded_position)
#         print(limits)
#         print(deltas)
        delta_sign = -1 if min(deltas) < 0 else 1
        delta = min([abs(d)-margin for d in deltas])
        new_limit = home-delta_sign*delta
        delta_sign_str = {-1: '+', 1: '-'}[delta_sign]
#         print(new_limit, delta, delta_sign, delta_sign_str)
        log.warning(f"New limit for {delta_sign_str}{ax} = {new_limit:.1f} (margin={margin:.1f})")
        return new_limit


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

        movetime = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.01)
        sleeptime = movetime*500
        tol = cfg.getfloat('tolerances', 'tip_tilt_move_tolerance', fallback=0.1)
        n = 3

        kpffiu = ktl.cache('kpffiu')

        measured_range = {}
        axis = ['X', 'Y']
        rawvals = {}
        update_ax = {'X': False, 'Y': False}
        for i,ax in enumerate(axis):
#             nominal_range = {'X': 15.9, 'Y': 24.6}[ax]
            nominal_range = {'X': 15.0, 'Y': 20.0}[ax]
            home = 0
            measured_range[ax] = [-nominal_range, nominal_range]
            rawvals[ax] = [None, None]

            # Negative side
            commanded_position = home-nominal_range
            new_limit = find_new_limit(ax, commanded_position,
                                       sleeptime=sleeptime, tol=tol, n=n)
            if new_limit is not None:
                update_ax[ax] = True
                measured_range[ax][0] = new_limit

            # Positive side
            commanded_position = home+nominal_range
            new_limit = find_new_limit(ax, commanded_position,
                                       sleeptime=sleeptime, tol=tol, n=n)
            if new_limit is not None:
                update_ax[ax] = True
                measured_range[ax][1] = new_limit

            time.sleep(sleeptime)
            InitializeTipTilt.execute({})
            time.sleep(sleeptime)

        log.info(f"Measured X range: {measured_range['X']}")
        log.info(f"Measured Y range: {measured_range['Y']}")

        if update_ax['Y'] is True or update_ax['X'] is True:
            new_home = [np.mean(measured_range['X']), np.mean(measured_range['Y'])]
            print(f"modify -s kpfguide TIPTILT_HOME='{new_home[0]:.1f} {new_home[1]:.1f}'")

        if update_ax['X'] is True:
            xrange = (max(measured_range['X']) - min(measured_range['X']))/2
            print(f"modify -s kpfguide TIPTILT_XRANGE={xrange:.1f}")

            kpffiu[f'TT{ax}VAX'].write(new_home[0])
            time.sleep(sleeptime)
            new_RON = kpffiu[f'TT{ax}RAW'].read()
            print(f"modify -s kpffiu TT{ax}RON='|{new_RON}|0|Home'")
        if update_ax['Y'] is True:
            yrange = (max(measured_range['Y']) - min(measured_range['Y']))/2
            print(f"modify -s kpfguide TIPTILT_YRANGE={yrange:.1f}")
            kpffiu[f'TT{ax}VAX'].write(new_home[1])
            time.sleep(sleeptime)
            new_RON = kpffiu[f'TT{ax}RAW'].read()
            print(f"modify -s kpffiu TT{ax}RON='|{new_RON}|0|Home'")

        ShutdownTipTilt.execute({})


    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass