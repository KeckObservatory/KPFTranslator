from time import sleep
import numpy as np

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetSourceSelectShutters(KPFFunction):
    '''Opens and closes the source select shutters via the 
    `kpfexpose.SRC_SHUTTERS` keyword.
    
    ARGS:
    =====
    :OpenScienceShutter: `bool` Open the SciSelect shutter? (default=False)
    :OpenSkyShutter: `bool` Open the SkySelect shutter? (default=False)
    :OpenCalSciSkyShutter: `bool` Open the Cal_SciSky shutter? (default=False)
    :OpenSoCalSciShutter: `bool` Open the SoCalSci shutter? (default=False)
    :OpenSoCalCalShutter: `bool` Open the SoCalCal shutter? (default=False)
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        shutter_list = []
        if args.get('OpenScienceShutter', False) is True:
            shutter_list.append('SciSelect')
        if args.get('OpenSkyShutter', False) is True:
            shutter_list.append('SkySelect')
        if args.get('OpenSoCalSciShutter', False) is True:
            shutter_list.append('SoCalSci')
        if args.get('OpenSoCalCalShutter', False) is True:
            shutter_list.append('SoCalCal')
        if args.get('OpenCalSciSkyShutter', False) is True:
            shutter_list.append('Cal_SciSky')
        shutters_string = ','.join(shutter_list)
        log.debug(f"Setting source select shutters to '{shutters_string}'")
        kpfexpose = ktl.cache('kpfexpose')
        kpfexpose['SRC_SHUTTERS'].write(shutters_string)
        shim_time = cfg.getfloat('times', 'kpfexpose_shim_time', fallback=0.1)
        sleep(shim_time)

    @classmethod
    def post_condition(cls, args):
        kpfexpose = ktl.cache('kpfexpose')
        timeshim = cfg.getfloat('times', 'kpfexpose_shim_time', fallback=0.01)
        sleep(timeshim)
        shutters = kpfexpose['SRC_SHUTTERS'].read()
        shutter_list = shutters.split(',')
        shutter_names = [('SciSelect', 'OpenScienceShutter'),
                         ('SkySelect', 'OpenSkyShutter'),
                         ('SoCalSci', 'OpenSoCalSciShutter'),
                         ('SoCalCal', 'OpenSoCalCalShutter'),
                         ('Cal_SciSky', 'OpenCalSciSkyShutter')]
        for shutter in shutter_names:
            shutter_status = shutter[0] in shutter_list
            shutter_target = args.get(shutter[1], False)
            if shutter_target != shutter_status:
                raise FailedToReachDestination(shutter_status, shutter_target)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument("--Science", "--Sci", "--science", "--sci",
                            dest="OpenScienceShutter",
                            default=False, action="store_true",
                            help="Open the SciSelect shutter?")
        parser.add_argument("--Sky", "--sky", dest="OpenSkyShutter",
                            default=False, action="store_true",
                            help="Open the SkySelect shutter?")
        parser.add_argument("--CalSciSky", dest="OpenCalSciSkyShutter",
                            default=False, action="store_true",
                            help="Open the Cal_SciSky shutter?")
        parser.add_argument("--SoCalSci", dest="OpenSoCalSciShutter",
                            default=False, action="store_true",
                            help="Open the SoCalSci shutter?")
        parser.add_argument("--SoCalCal", dest="OpenSoCalCalShutter",
                            default=False, action="store_true",
                            help="Open the SoCalCal shutter?")
        return super().add_cmdline_args(parser)
