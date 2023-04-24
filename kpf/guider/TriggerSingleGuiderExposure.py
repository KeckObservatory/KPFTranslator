from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.guider import guider_is_saving, guider_is_active


class TriggerSingleGuiderExposure(KPFTranslatorFunction):
    '''Trigger a single guider exposure using the EXPOSE keyword.
    
    ARGS:
    =====
    :wait: (bool) Return only after lastfile is updated? (default = False)
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        if guider_is_active() == True:
            raise FailedPreCondition('Guider is active')
        if guider_is_saving() == True:
            raise FailedPreCondition('Guider is saving')

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        kpfexpose = ktl.cache('kpfexpose')
        exptime = kpfguide['EXPTIME'].read(binary=True)
        lastfile = kpfguide['LASTFILE']
        initial_lastfile = lastfile.read()
        log.debug(f"Triggering a new guider exposure.")
        log.debug(f"kpfexpose.OBJECT = {kpfexpose['OBJECT'].read()}")
        kpfguide['EXPOSE'].write('yes')
        if args.get('wait', True) is True:
            expr = f"($kpfguide.LASTFILE != '{initial_lastfile}')"
            success = ktl.waitFor(expr, timeout=exptime*2+1)
            if success is not True:
                log.error(f'Failed to get new LASTFILE from guider')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument("--nowait", dest="wait",
                            default=True, action="store_false",
                            help="Start exposure and return immediately?")
        return super().add_cmdline_args(parser, cfg)
