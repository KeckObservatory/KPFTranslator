from time import sleep
import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetSourceSelectShutters(KPFTranslatorFunction):
    '''Opens and closes the source select shutters via the 
    `kpfexpose.SRC_SHUTTERS` keyword.
    
    ARGS:
    =====
    :SSS_Science: `bool` Open the SciSelect shutter? (default=False)
    :SSS_Sky: `bool` Open the SkySelect shutter? (default=False)
    :SSS_CalSciSky: `bool` Open the Cal_SciSky shutter? (default=False)
    :SSS_SoCalSci: `bool` Open the SoCalSci shutter? (default=False)
    :SSS_SoCalCal: `bool` Open the SoCalCal shutter? (default=False)
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        shutter_list = []
        if args.get('SSS_Science', False) is True:
            shutter_list.append('SciSelect')
        if args.get('SSS_Sky', False) is True:
            shutter_list.append('SkySelect')
        if args.get('SSS_SoCalSci', False) is True:
            shutter_list.append('SoCalSci')
        if args.get('SSS_SoCalCal', False) is True:
            shutter_list.append('SoCalCal')
        if args.get('SSS_CalSciSky', False) is True:
            shutter_list.append('Cal_SciSky')
        shutters_string = ','.join(shutter_list)
        log.debug(f"Setting source select shutters to '{shutters_string}'")
        kpfexpose = ktl.cache('kpfexpose')
        kpfexpose['SRC_SHUTTERS'].write(shutters_string)
        shim_time = cfg.getfloat('times', 'kpfexpose_shim_time', fallback=0.1)
        sleep(shim_time)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        timeshim = cfg.getfloat('times', 'kpfexpose_shim_time', fallback=0.01)
        sleep(timeshim)
        shutters = kpfexpose['SRC_SHUTTERS'].read()
        shutter_list = shutters.split(',')
        shutter_names = [('SciSelect', 'SSS_Science'),
                         ('SkySelect', 'SSS_Sky'),
                         ('SoCalSci', 'SSS_SoCalSci'),
                         ('SoCalCal', 'SSS_SoCalCal'),
                         ('Cal_SciSky', 'SSS_CalSciSky')]
        for shutter in shutter_names:
            shutter_status = shutter[0] in shutter_list
            shutter_target = args.get(shutter[1], False)
            if shutter_target != shutter_status:
                raise FailedToReachDestination(shutter_status, shutter_target)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument("--Science", "--Sci", "--science", "--sci",
                            dest="SSS_Science",
                            default=False, action="store_true",
                            help="Open the SciSelect shutter?")
        parser.add_argument("--Sky", "--sky", dest="SSS_Sky",
                            default=False, action="store_true",
                            help="Open the SkySelect shutter?")
        parser.add_argument("--CalSciSky", dest="SSS_CalSciSky",
                            default=False, action="store_true",
                            help="Open the Cal_SciSky shutter?")
        parser.add_argument("--SoCalSci", dest="SSS_SoCalSci",
                            default=False, action="store_true",
                            help="Open the SoCalSci shutter?")
        parser.add_argument("--SoCalCal", dest="SSS_SoCalCal",
                            default=False, action="store_true",
                            help="Open the SoCalCal shutter?")
        return super().add_cmdline_args(parser, cfg)
