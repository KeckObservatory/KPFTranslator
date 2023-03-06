from collections import OrderedDict

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetAORotator(KPFTranslatorFunction):
    '''Set the AO rotator destination
    
    ARGS:
    =====
    :dest: Angle in degrees
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'dest')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        log.debug(f"Setting AO Rotator to {args['dest']:.1f}")
        ao['OBRT'].write(args['dest'])
        ao['OBRTMOVE'].write('1')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        success = ktl.waitfor('($ao.OBRTSTST == INPOS)', timeout=180)
        if success is not True:
            ao = ktl.cache('ao')
            raise FailedToReachDestination(ao['OBRTSTST'].read(), 'INPOS')

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['dest'] = {'type': float,
                               'help': 'Desired rotator position'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
