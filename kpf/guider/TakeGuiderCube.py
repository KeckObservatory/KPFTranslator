import time
from pathlib import Path

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.guider.StartTriggerFile import StartTriggerFile
from kpf.guider.StopTriggerFile import StopTriggerFile
from kpf.guider.WaitForTriggerFile import WaitForTriggerFile


class TakeGuiderCube(KPFFunction):
    '''Take a "trigger file" from the guide camera of a given duration.

    Args:
        duration (float): The duration in seconds of the image set.
        ImageCube (bool): Collect the full cube of images? (default True) This
            will slow down file write considerably.

    KTL Keywords Used:

    - `kpfguide.TRIGCUBE`
    - `kpfguide.LASTTRIGFILE`
    - `kpfguide.ALL_LOOPS`

    Functions Called:

    - `kpf.guider.StartTriggerFile`
    - `kpf.guider.StopTriggerFile`
    - `kpf.guider.WaitForTriggerFile`
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'duration', value_min=0)

    @classmethod
    def perform(cls, args):
        duration = float(args.get('duration'))
        kpfguide = ktl.cache('kpfguide')
        # Read initial conditions, so we can set them back at the end
        initial_trigcube = kpfguide['TRIGCUBE'].read()
        initial_lastfile = kpfguide['LASTTRIGFILE'].read()
        initial_all_loops = kpfguide['ALL_LOOPS'].read()

        # Do we want to take the image cube?
        collect_image_cube = args.get('ImageCube', True)
        set_trigcube = {True: 'Active', False: 'Inactive'}[collect_image_cube]
        kpfguide['TRIGCUBE'].write(set_trigcube)

        # Trigger data collection
        log.info(f"Starting guider cube data collection, duration = {duration:.1f} s")
        StartTriggerFile.execute({})
        time.sleep(duration)
        StopTriggerFile.execute({})
        # Stop all loops if we're writing out a full image cube
#         if initial_all_loops == 'Active' and collect_image_cube == True:
#             kpfguide['ALL_LOOPS'].write('Inactive', wait=False)
        cube_file = WaitForTriggerFile.execute({'initial_lastfile': initial_lastfile})

        # Reset TRIGCUBE
        kpfguide['TRIGCUBE'].write(initial_trigcube)
        # Reset ALL_LOOPS to initial values
#         if initial_all_loops == 'Active' and collect_image_cube == True:
#             kpfguide['ALL_LOOPS'].write(initial_all_loops)

        return cube_file

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('duration', type=float,
                            help='The duration in seconds')
        parser.add_argument("--noTRIGCUBE", dest="ImageCube",
                            default=True, action="store_false",
                            help="Collect the full image cube?")
        return super().add_cmdline_args(parser)
