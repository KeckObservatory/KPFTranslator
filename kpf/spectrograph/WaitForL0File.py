import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class WaitForL0File(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        LOUTFILE = ktl.cache('kpfassemble', 'LOUTFILE')
        initial_LOUTFILE = LOUTFILE.read()
        timeout = 10
        found_new_file = LOUTFILE.waitFor(f'!="{initial_LOUTFILE}"',
                                          timeout=timeout)
        if found_new_file is True:
            log.info(f'kpfassemble wrote {LOUTFILE.read()}')
        else:
            log.debug('WaitForL0File did not find new file')


    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
