from time import sleep
import numpy as np

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetSourceSelectShutters(KPFFunction):
    '''Opens and closes the source select shutters via the 
    `kpfexpose.SRC_SHUTTERS` keyword.

    Args:
        OpenScienceShutter (bool): Open the SciSelect shutter? (default=False)
        OpenSkyShutter (bool): Open the SkySelect shutter? (default=False)
        OpenCalSciSkyShutter (bool): Open the Cal_SciSky shutter? (default=False)
        OpenSoCalSciShutter (bool): Open the SoCalSci shutter? (default=False)
        OpenSoCalCalShutter (bool): Open the SoCalCal shutter? (default=False)

    KTL Keywords Used:

    - `kpfexpose.SRC_SHUTTERS`
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
        SRC_SHUTTERS = ktl.cache('kpfexpose', 'SRC_SHUTTERS')
        SRC_SHUTTERS.write(shutters_string)
        shim_time = cfg.getfloat('times', 'kpfexpose_shim_time', fallback=0.01)
        sleep(shim_time)

    @classmethod
    def post_condition(cls, args):
        SRC_SHUTTERS = ktl.cache('kpfexpose', 'SRC_SHUTTERS')
        SRC_SHUTTERS.monitor()
        shutter_names = [('SciSelect', 'OpenScienceShutter'),
                         ('SkySelect', 'OpenSkyShutter'),
                         ('SoCalSci', 'OpenSoCalSciShutter'),
                         ('SoCalCal', 'OpenSoCalCalShutter'),
                         ('Cal_SciSky', 'OpenCalSciSkyShutter')]
        shutter_tests = [False]
        timeshim = cfg.getfloat('times', 'kpfexpose_shim_time', fallback=0.01)
        total_time = 0
        while np.all(shutter_tests) != True and total_time < 0.25:
            shutter_tests = []
            for shutter in shutter_names:
                if args.get(shutter[1], False) is True:
                    shutter_tests.append(shutter[0] in SRC_SHUTTERS.ascii.split(','))
            sleep(timeshim)
            total_time += timeshim
        if np.all(shutter_tests) != True:
            raise FailedToReachDestination(SRC_SHUTTERS.ascii, 'TBD')

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
