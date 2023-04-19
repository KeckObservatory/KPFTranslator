import time

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.utils.SendEmail import SendEmail


##-------------------------------------------------------------------------
## TriggerGreenMiniFill
##-------------------------------------------------------------------------
class TriggerGreenMiniFill(KPFTranslatorFunction):
    '''I really hope this is not necessary in the long term.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        kpffill = ktl.cache('kpffill')
        if kpffill['GREENFILLIP'].read() == 'True':
            raise FailedPreCondition('Green fill already in progress')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpffill = ktl.cache('kpffill')
        # Start fill
        log.warning(f'Starting green mini fill')
        kpffill['GREENSTART'].write(1)
        # Wait
        sleep_time = args.get('duration', 240)
        log.debug(f'Sleeping {sleep_time:.0f} s')
        time.sleep(sleep_time)
        # Stop fill
        if kpffill['GREENFILLIP'].read() == 'True':
            log.warning(f'Stopping green mini fill')
            kpffill['GREENSTOP'].write(1)
            time.sleep(5)
        else:
            msg = 'Expected green mini fill to be in progress.'
            SendEmail.execute({'Subject': 'TriggerGreenMiniFill Failed',
                               'Message': f'{msg}'})
            raise KPFException(msg)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpffill = ktl.cache('kpffill')
        if kpffill['GREENFILLIP'].read() == 'True':
            msg = 'Green still in progress, should be stopped!'
            SendEmail.execute({'Subject': 'TriggerGreenMiniFill Failed',
                               'Message': f'{msg}'})
            raise FailedPostCondition(msg)
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['duration'] = {'type': float,
                'help': 'The duration of the fill in seconds (240 recommended).'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
