import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetObject(KPFTranslatorFunction):
    '''Sets the OBJECT keyword for the science detectors in the kpfexpose
    keyword service.
    
    ARGS:
    Object - The desired object keyword value.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
#         check_input(args, 'Object')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        obj = args.get('Object', '')
        if obj is None:
            obj = ''
        log.debug(f"Setting OBJECT to '{obj}'")
        kpfexpose['OBJECT'].write(obj)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        obj = args.get('Object')
        timeout = cfg.get('times', 'kpfexpose_timeout', fallback=0.01)
        expr = f"($kpfexpose.OBJECT == '{obj}')"
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            objectkw = ktl.cache('kpfexpose', 'OBJECT')
            raise FailedToReachDestination(objectkw.read(), obj)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['Object'] = {'type': str,
                                 'help': 'The OBJECT keyword.'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
