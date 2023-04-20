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
        movetime = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)

        axis = ['X', 'Y']
        for ax in axis:
            vals = {'-2900': [], '+2900': []}
            TTVAL = ktl.cache('kpffiu', f'TT{ax}VAL')
            for val in vals.keys():
                log.debug(f'Moving {ax} to {val}')
                TTVAL.write(int(val))
                time.sleep(10*movetime)
                results = []
                for i in range(nsamples):
                    reading = float(TTVAL.read())
                    log.debug(f'  TT{ax}VAL = {reading:.1f}')
                    results.append(reading)
                    time.sleep(movetime)
                # Analyze Results
                meanresult = np.mean(np.array(results))
                stdresult = np.std(np.array(results))
                delta = meanresult - float(val)
                frac = meanresult/float(val)
                vals[val] = [meanresult, stdresult, delta, frac]
                log.info(f"  TT{ax}VAL={val}: mean={meanresult:.1f} (stddev={stdresult:.1f})")
            log.info(f"TipTilt Range {ax}: {-vals['-2900'][3]:.0%} to {vals['+2900'][3]:.0%}")

            InitializeTipTilt.execute({})
            time.sleep(10*movetime)

        ShutdownTipTilt.execute({})


    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True