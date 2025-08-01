from pathlib import Path

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.guider import guider_is_saving, guider_is_active


class TriggerSingleGuiderExposure(KPFFunction):
    '''Trigger a single guider exposure using the EXPOSE keyword.

    Args:
        wait (bool): Return only after lastfile is updated? (default = False)

    KTL Keywords Used:

    - `kpfguide.EXPTIME`
    - `kpfguide.LASTFILE`
    - `kpfguide.EXPOSE`
    '''
    @classmethod
    def pre_condition(cls, args):
        if guider_is_active() == True:
            raise FailedPreCondition('Guider is active')
        if guider_is_saving() == True:
            raise FailedPreCondition('Guider is saving')

    @classmethod
    def perform(cls, args):
        kpfguide = ktl.cache('kpfguide')
        OBJECT = ktl.cache('kpfexpose', 'OBJECT')
        exptime = kpfguide['EXPTIME'].read(binary=True)
        lastfile = kpfguide['LASTFILE']
        initial_lastfile = lastfile.read()
        log.debug(f"Triggering a new guider exposure.")
        log.debug(f"kpfexpose.OBJECT = {OBJECT.read()}")
        kpfguide['EXPOSE'].write('yes')
        if args.get('wait', True) is True:
            expr = f"($kpfguide.LASTFILE != '{initial_lastfile}')"
            success = ktl.waitFor(expr, timeout=exptime*2+1)
            if success is not True:
                log.error(f'Failed to get new LASTFILE from guider')

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument("--nowait", dest="wait",
                            default=True, action="store_false",
                            help="Start exposure and return immediately?")
        return super().add_cmdline_args(parser)
