from time import sleep

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from ..guider.SetGuiderGain import SetGuiderGain
from ..guider.SetGuiderFPS import SetGuiderFPS


class TakeGuiderSensitivityData(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
#         check_input(args, 'FPS')
#         check_input(args, 'gains')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        FPSvalues = [10, 20]
        gains = ['low']
        
        for FPS in FPSvalues:
            for gain in gains:
                log.info(f"Setting gain to {gain} and FPS to {FPS}")
                SetGuiderGain.execute({'gain': gain})
                SetGuiderFPS.execute({'fps': FPS})
                # Wait for the stacked file to increment
                initial_lastfile = kpfguide['LASTFILE'].read()
                initial_lasttrigfile = kpfguide['LASTTRIGFILE'].read()
                ktl.waitFor(f"$kpfguide.LASTFILE != '{initial_lastfile}'")
                # Start cube collection simultaneous with stacked file
                kpfguide['TRIGGER'].write(1)
                # End cube collection simultaneous with stacked file being written
                initial_lastfile = kpfguide['LASTFILE'].read()
                ktl.waitFor(f"$kpfguide.LASTFILE != '{initial_lastfile}'")
                kpfguide['TRIGGER'].write(0)
                # Wait for cuber file to be updated
                ktl.waitFor(f"$kpfguide.LASTTRIGFILE != '{initial_lasttrigfile}'")
                stacked_file = kpfguide['LASTFILE'].read()
                cube_file = kpfguide['LASTTRIGFILE'].read()
                log.info(f"  stacked file: {stacked_file}")
                log.info(f"  cube file: {cube_file}")


    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

#     @classmethod
#     def add_cmdline_args(cls, parser, cfg=None):
#         '''The arguments to add to the command line interface.
#         '''
#         from collections import OrderedDict
#         args_to_add = OrderedDict()
#         args_to_add['OBfile'] = {'type': str,
#                                  'help': ('A YAML fortmatted file with the OB '
#                                           'to be executed. Will override OB '
#                                           'data delivered as args.')}
#         parser = cls._add_args(parser, args_to_add, print_only=False)
#         return super().add_cmdline_args(parser, cfg)
