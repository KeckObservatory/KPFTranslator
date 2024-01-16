from time import sleep
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class OptimizeFPS(KPFTranslatorFunction):
    '''
    
    Target peak = 6000 ADU
    Reasonable range = 3000-9000 ADU (0.5-1.5x target)
    
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        target_peak = 6000

        kpfguide = ktl.cache('kpfguide')
        gain = kpfguide['GAIN'].read(binary=True) # 0 Low 1 Medium 2 High
        fps = kpfguide['FPS'].read(binary=True)

        # If TIPTILT_CALC is not on, turn it on
        if kpfguide['TIPTILT_CALC'].read() == 'Inactive':
            log.info('Turning TIPTILT_CALC on')
            kpfguide['TIPTILT_CALC'].write('Active')
            time.sleep(1)
        # Check peak value
        peak = kpfguide['OBJECT_PEAK'].read(binary=True)
        peak_ratio = peak/target_peak
        if peak_ratio > 1.5:
            # Star is dangerously bright, increase FPS
            new_fps = fps*peak_ratio
        elif peak_ratio > 0.5:
            # Star is in reasonable brightness range
            pass
        elif peak_ratio > 0.1:
            # Star is somewhat faint, decrease FPS
            new_fps = fps*peak_ratio
        else:
            # Star is very faint, possibly undetected
            print('Star is very faint')
            if gain < 2:
                print('Incrasing gain')
                newgain = gain + 1
                kpfguide['GAIN'].write(newgain)
                OptimizeFPS.execute({})


    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
