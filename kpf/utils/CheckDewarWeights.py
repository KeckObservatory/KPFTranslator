import sys
import time
from datetime import datetime, timedelta
import numpy as np

import ktl
import keygrabber

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


##-------------------------------------------------------------------------
## CheckDewarWeights
##-------------------------------------------------------------------------
class CheckDewarWeights(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        dewar = args.get('dewar', 'green')

        fill_time = cfg.getint('LN2', 'fill_time', fallback=21)
        low_weight = cfg.getint('LN2', f'low_weight_{dewar}', fallback=90)
        use_rate = cfg.getint('LN2', f'use_rate_{dewar}', fallback=40)

        utcnow = datetime.utcnow()
        if utcnow.hour < fill_time:
            time_until_fill = fill_time - (utcnow.hour + utcnow.minute/60)
        else:
            time_until_fill = fill_time+24 - (utcnow.hour + utcnow.minute/60)

        kpffill = ktl.cache('kpffill')

        weight = kpffill[f'{dewar}WEIGHT'].read(binary=True)
        weight_at_fill = weight - (time_until_fill/24)*use_rate
        if weight_at_fill > low_weight:
            # Dewar fill level is ok
            print('Dewar weight is OK')
        else:
            # Dewar fill level is not ok
            print('Dewar weight is low!')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass


    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('dewar', type=str,
                            choices=['green', 'red'],
                            default='green',
                            help='Which dewar to check? red or green')
        return super().add_cmdline_args(parser, cfg)
