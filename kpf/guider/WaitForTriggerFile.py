import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class WaitForTriggerFile(KPFFunction):
    '''Wait for a trigger file in progress to finish being collected.

    KTL Keywords Used:

    - `kpfguide.LASTTRIGFILE`
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'initial_lastfile')

    @classmethod
    def perform(cls, args):
        initial_lastfile = args.get('initial_lastfile', False)
        LASTTRIGFILE = ktl.cache('kpfguide', 'LASTTRIGFILE')
        log.debug(f"Waiting for guider trigger file to be written out")
        # Wait for cube file to be updated
        expr = f"$kpfguide.LASTTRIGFILE != '{initial_lastfile}'"
        success = ktl.waitFor(expr, timeout=20)
        if success:
            cube_file = LASTTRIGFILE.read()
            log.info(f"New cube file: {cube_file}")
        else:
            cube_file = None
            log.error(f"kpfguide.LASTTRIGFILE did not update")
        return cube_file

    @classmethod
    def post_condition(cls, args):
        pass
