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
    current_position = kpffiu[f'TT{ax}MEX'].read(binary=True)
    if abs(current_position-commanded_position) < tol:
        log.info(f"  TT{ax}VAX reached {commanded_position:.2f}")
        return None
    else:
        log.info(f"  TT{ax}VAX only reached {current_position:.2f}")
        return current_position 


def find_new_limit(ax, commanded_position, n=5,
                   sleeptime=1, tol=0.1, margin=0):
    kpffiu = ktl.cache('kpffiu')
    tthome = ktl.cache('kpfguide', 'TIPTILT_HOME')
    axid = {'X': 0, 'Y': 1}[ax]
    home = tthome.read(binary=True)[axid]
    limits = []
    deltas = []
    log.info(f'Finding move limit for TT{ax}VAX toward {commanded_position:.1f}')
    for i in range(n):
        log.info(f"  Commanding TT{ax}VAX to {commanded_position:.2f} ({i+1}/{n})")
        measured_limit = check_move(ax, commanded_position,
                                    sleeptime=sleeptime, tol=tol)
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
        log.info(f"  Move failed on {len(limits)}/{n} moves")
        delta_sign = -1 if commanded_position < 0 else 1
        delta = min([abs(d) for d in deltas])
        new_limit = home+delta_sign*(delta-margin)
        delta_sign_str = {-1: '-', 1: '+'}[delta_sign]
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

        sleeptime = 10 # Set by the 5 second time in the %MEX and %MEV keywords
                       # Need to account for worst case
        tol = cfg.getfloat('tolerances', 'tip_tilt_move_tolerance', fallback=0.1)
        n = args.get('repeats')

        kpffiu = ktl.cache('kpffiu')
        kpfguide = ktl.cache('kpfguide')

        measured_range = {}
        axis = ['X', 'Y']
        rawvals = {}
        update_ax = {'X': False, 'Y': False}
        for i,ax in enumerate(axis):
            nominal_range = {'X': 15.9, 'Y': 24.6}[ax]
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

        new_home = [np.mean(measured_range['X']), np.mean(measured_range['Y'])]
        current_home = kpfguide['TIPTILT_HOME'].read(binary=True)
        if np.isclose(current_home[0], new_home[0]) and np.isclose(current_home[1], new_home[1]):
            print(f'TIPTILT_HOME OK: gshow -s kpfguide TIPTILT_HOME matches {new_home}')
        else:
            print(f"modify -s kpfguide TIPTILT_HOME='{new_home[0]:.1f} {new_home[1]:.1f}'")

        for i,ax in enumerate(axis):
            print()
            range = (max(measured_range[ax]) - min(measured_range[ax]))/2
            print(f"modify -s kpfguide TIPTILT_{ax}RANGE={range:.1f}")
            print(f"  Sending {ax} to home")
            kpffiu[f'TT{ax}VAX'].write(new_home[i])
            time.sleep(sleeptime)
            new_RON = kpffiu[f'TT{ax}MED'].read()
            print(f"modify -s kpffiu TT{ax}RON='|{new_RON}|0|Home'")


    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('--repeats', type=int, default=1,
                            help="The number of iterations to use in the calculation")
        return super().add_cmdline_args(parser, cfg)
