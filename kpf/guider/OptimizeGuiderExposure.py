import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class OptimizeGuiderExposure(KPFTranslatorFunction):
    '''
    
    Target peak = 6000 ADU
    Reasonable range = 3000-9000 ADU (0.5-1.5x target)
    
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        log.info('Running OptimizeGuiderExposure')
        setvalues = args.get("set", False)
        log.debug(f'set = {setvalues}')
        target_peak = 6000
        log.debug(f'target_peak = {target_peak}')

        kpfguide = ktl.cache('kpfguide')
        gain = kpfguide['GAIN'].read(binary=True) # 0 Low 1 Medium 2 High
        fps = kpfguide['FPS'].read(binary=True)
        time_shim = 1/fps + 0.5

        # If TIPTILT_CALC is not on, turn it on
        if kpfguide['TIPTILT_CALC'].read() == 'Inactive':
            log.info('Turning TIPTILT_CALC on')
            kpfguide['TIPTILT_CALC'].write('Active')
            time.sleep(time_shim)
        # Check peak value
        peak = kpfguide['OBJECT_PEAK'].read(binary=True)
        peak_ratio = peak/target_peak
        if peak_ratio > 1.5:
            # Star is dangerously bright, increase FPS
            new_fps = int(fps*peak_ratio)
            if setvalues is True:
                log.info(f'Setting new FPS = {new_fps}')
                kpfguide['FPS'].write(new_fps)
            else:
                print('Recommend new FPS: {new_fps}')
        elif peak_ratio > 0.5:
            # Star is in reasonable brightness range
            pass
        elif peak_ratio > 0.1:
            # Star is somewhat faint, decrease FPS
            new_fps = int(fps*peak_ratio)
            if setvalues is True:
                log.info(f'Setting new FPS = {new_fps}')
                kpfguide['FPS'].write(new_fps)
            else:
                print('Recommend new FPS: {new_fps}')
        else:
            # Star is very faint, possibly undetected
            log.info('Star is very faint or undetected')
            if gain < 2:
                newgain = gain + 1
                if setvalues is True:
                    gain_string = {0: 'low', 1: 'medium', 2: 'high'}[newgain]
                    log.info(f'Increasing gain to {gain_string}')
                    kpfguide['GAIN'].write(newgain)
                    time.sleep(time_shim)
                    OptimizeGuiderExposure.execute(args)
                else:
                    print(f'Recommend incrasing gain to {newgain}')


    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument("--set", dest="set",
                            default=False, action="store_true",
                            help="Set the resulting gain and FPS?")
        return super().add_cmdline_args(parser, cfg)
