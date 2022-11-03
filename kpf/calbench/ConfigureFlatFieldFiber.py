import ktl
from time import sleep

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log
from .SetFlatFieldFiberPos import SetFlatFieldFiberPos
from .WaitForFlatFieldFiberPos import WaitForFlatFieldFiberPos
from .SetCalSource import SetCalSource
from .CalLampPower import CalLampPower


class ConfigureFlatFieldFiber(KPFTranslatorFunction):
    '''Configure the cal bench for flat field fiber use by:
    - Setting the OCTAGON to HOME
    - Setting the requested Flat Field Fiber Aperture (kpfcal.FF_FIBERPOS)
    - Turning on the Flat Field Fiber light source
    - Waiting ? for the lamp to warm up
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        target = args.get('FF_FiberPos')
        warm_up_time = cfg.get('times', 'wideflat_warmup_time', fallback=30)

        CalLampPower.execute({'lamp': 'WideFlat', 'power': 'on'})
        SetCalSource.execute({'CalSource': 'Home', 'wait': False})
        SetFlatFieldFiberPos.execute({'FF_FiberPos': target, 'wait': False})

        log.debug(f'Waiting {warm_up_time:.0f} s for lamp to warm up')
        sleep(warm_up_time)

        log.info(f"Waiting for Octagon (CalSource)")
        WaitForCalSource.execute({'CalSource': 'Home'})
        log.info(f"Waiting for Flat Field Fiber Position")
        WaitForFlatFieldFiberPos.execute(args)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['FF_FiberPos'] = {'type': str,
                                      'help': 'Wide flat aperture to use.'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)

