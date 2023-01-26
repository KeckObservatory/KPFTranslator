import os
from pathlib import Path
import logging
from datetime import datetime,timedelta
import time
import numpy as np
from astropy.table import Table, Row

import ktl

import KPFTranslatorFunction
from ..fvc.TakeFVCExposure import TakeFVCExposure
from ..calbench.CalLampPower import CalLampPower


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
this_file_name = Path(__file__).name.replace(".py", "")

log = logging.getLogger(f'{this_file_name}')
log.setLevel(logging.DEBUG)
## Set up console output
LogConsoleHandler = logging.StreamHandler()
LogConsoleHandler.setLevel(logging.INFO)
LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
LogConsoleHandler.setFormatter(LogFormat)
log.addHandler(LogConsoleHandler)
## Set up file output
utnow = datetime.utcnow()
now_str = utnow.strftime('%Y%m%dat%H%M%S')
date = utnow-timedelta(days=1)
date_str = date.strftime('%Y%b%d').lower()
log_dir = Path(f"/s/sdata1701/{os.getlogin()}/{date_str}/script_logs/")
if log_dir.exists() is False:
    log_dir.mkdir(parents=True)
LogFileName = log_dir / f"{this_file_name}_{now_str}.log"
LogFileHandler = logging.FileHandler(LogFileName)
LogFileHandler.setLevel(logging.DEBUG)
LogFileHandler.setFormatter(LogFormat)
log.addHandler(LogFileHandler)


class ImageBackIlluminatedFibers(KPFTranslatorFunction):
    '''Take images of the back illuminated fibers using the FVCs
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        cameras = args.get('cameras', '').split(',')
        for camera in cameras:
            if camera not in ['CRED2', 'SCI', 'CAHK', 'EXT', 'ExpMeter']:
                print(f"Camera {camera} not supported")
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        log.info("###########")
        log.info(f"args = {args}")
        log.info("###########")

        images_file = log_dir / Path(f'{this_file_name}_images_{now_str}.txt')
        images = Table(names=('file', 'camera', 'LED'),
                       dtype=('a90',  'a10',    'a10'))

        # Set up FVCs
        kpffvc = ktl.cache('kpffvc')

        for LED in ['SciLED', 'SkyLED', 'CaHKLED', 'ExpMeterLED']:
            log.info(f"Imaging with {LED} on")
            for LEDname in ['SciLED', 'SkyLED', 'CaHKLED', 'ExpMeterLED']:
                pwr = {True: 'on', False: 'off'}[LED == LEDname]
                print(LEDname, pwr)

            # Start FVC Exposures
            nextfile = {}
            for camera in ['SCI', 'CAHK', 'CAL', 'EXT']:
                if camera in args.get('cameras', '').split(','):
                    nextfile[camera] = kpffvc[f"{camera}LASTFILE"].read()
                    log.debug(f"  Nextfile for {camera} = {nextfile[camera]}")
                    log.info(f"  Starting {camera} FVC exposure")
                    TakeFVCExposure.execute({'camera': camera, 'wait': False})

            # Collect files for FVC exposures
            for camera in ['SCI', 'CAHK', 'CAL', 'EXT']:
                if camera in args.get('cameras', '').split(','):
                    log.info(f"  Looking for output file for {camera}")
                    expr = f'($kpffvc.{camera}LASTFILE == "{nextfile[camera]}")'
                    log.debug(f"  Waiting for: {expr}")
                    if ktl.waitFor(expr, timeout=20) is False:
                        lastfile = kpffvc[f'{camera}LASTFILE'].read()
                        log.error('No new FVC file found')
                        log.error(f"  expecting: {nextfile[camera]}")
                        log.error(f"  kpffvc.{camera}LASTFILE = {lastfile}")
                    else:
                        lastfile = kpffvc[f'{camera}LASTFILE'].read()
                        log.debug(f"Found {lastfile}")
                        row = {'file': lastfile, 'camera': camera,
                               'LED': LED}
                        images.add_row(row)

            if images_file.exists():
                images_file.unlink()
            images.write(images_file, format='ascii.csv')


    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['cameras'] = {'type': str,
                    'help': 'List of cameras'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
