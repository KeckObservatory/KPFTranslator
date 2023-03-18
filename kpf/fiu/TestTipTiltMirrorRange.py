import time

import ktl

import numpy as np

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.fiu.InitializeTipTilt import InitializeTipTilt
from kpf.fiu.ShutdownTipTilt import ShutdownTipTilt


class TestTipTiltMirrorRange(KPFTranslatorFunction):
    '''
    
    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # Verify with user if it is OK to proceed
        msg = ["",
               "--------------------------------------------------------------",
               "This script will move the tip tilt mirror.",
               "Observations should not be in progress and the AO bench should",
               "be clear of personnel.",
               "Do you wish to to continue? [Y/n]",
               "--------------------------------------------------------------",
               "",
               ]
        for line in msg:
            print(line)
        user_input = input()
        if user_input.lower() in ['n', 'no', 'q', 'quit', 'abort']:
            return

        # Measure tip tilt ranges
        log.info('Beginning TestTipTiltMirrorRange')
        InitializeTipTilt.execute({})

        nsamples = 9
        movetime = cfg.get('times', 'tip_tilt_move_time', fallback=0.1)

        xvals = {'-2900': [], '+2900': []}
        TTXVAL = ktl.cache('kpffiu', 'TTXVAL')
        for val in xvals.keys():
            log.debug(f'Moving X to {val}')
            TTXVAL.write(int(val))
            time.sleep(10*movetime)
            vals = []
            for i in range(nsamples):
                reading = float(TTXVAL.read())
                log.debug(f'  TTXVAL = {reading:.1f}')
                vals.append(reading)
                time.sleep(movetime)
            # Analyze Results
            meanval = np.mean(np.array(vals))
            stdval = np.std(np.array(vals))
            delta = meanval - float(val)
            frac = meanval/float(val)
            xvals[val] = [meanval, stdval, delta, frac]
            log.info(f"  TTXVAL={val}: mean={meanval:.1f} (stddev={stdval:.1f})")
        log.info(f"X Axis: {-xvals['-2900'][3]:.0%} to {xvals['+2900'][3]:.0%}")

        InitializeTipTilt.execute({})

        yvals = {'-2900': [], '+2900': []}
        TTYVAL = ktl.cache('kpffiu', 'TTYVAL')
        for val in yvals.keys():
            log.debug(f'Moving Y to {val}')
            TTYVAL.write(int(val))
            time.sleep(10*movetime)
            vals = []
            for i in range(nsamples):
                reading = float(TTYVAL.read())
                log.debug(f'  TTYVAL = {reading:.1f}')
                vals.append(reading)
                time.sleep(movetime)
            # Analyze Results
            meanval = np.mean(np.array(vals))
            stdval = np.std(np.array(vals))
            delta = meanval - float(val)
            frac = meanval/float(val)
            yvals[val] = [meanval, stdval, delta, frac]
            log.info(f"  TTXVAL={val}: mean={meanval:.1f} (stddev={stdval:.1f})")
        log.info(f"Y Axis: {-yvals['-2900'][3]:.0%} to {yvals['+2900'][3]:.0%}")

        ShutdownTipTilt.execute({})


    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True