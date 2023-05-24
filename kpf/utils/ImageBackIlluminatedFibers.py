import os
from pathlib import Path
import logging
from datetime import datetime,timedelta
import time
import numpy as np
from astropy.table import Table, Row

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.fvc.FVCPower import FVCPower
from kpf.fvc.SetFVCExpTime import SetFVCExpTime
from kpf.fvc.TakeFVCExposure import TakeFVCExposure
from kpf.calbench.CalLampPower import CalLampPower


class ImageBackIlluminatedFibers(KPFTranslatorFunction):
    '''Take images of the back illuminated fibers using the FVCs
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        this_file_name = Path(__file__).name.replace('.py', '')
        log_path = Path(f'/s/sdata1701/KPFTranslator_logs/')
        images_file = log_path / Path(f'{this_file_name}_images.txt')
        hstnow = datetime.now()
        now_str = hstnow.strftime('%Y-%m-%d %H:%M:%S')
        
        LEDoutlets = {'Science': 'E7',
                      'Sky': 'E8',
                      'CaHK': 'J7',
                      'ExpMeter': 'H1'}
        LEDnames = {'Science': 'Science Back-Illumination LED',
                    'Sky': 'Sky Back-Illumination LED',
                    'CaHK': 'HK Back-Illumination LED',
                    'ExpMeter': 'Exp Meter Back Illum LED'}
        exptimes = {'SCI': {'Science': 0.1,
                            'Sky': 1,
                            'ExpMeter': 2},
                    'CAHK': {'CaHK': 5}
                    }
        kpffvc = ktl.cache('kpffvc')
        kpfpower = ktl.cache('kpfpower')

        def take_back_illuminated_image(camera, LEDname):
            log.info(f"Taking back illuminated image of {LEDname} fiber with {camera} FVC")
            FVCPower.execute({'camera': camera, 'power': 'on'})
            # Take image with Science LED on
            outlet = LEDoutlets[LEDname]
            if LEDnames[LEDname] != kpfpower[f"OUTLET_{outlet}_NAME"].read():
                raise KPFException(f"Expected outlet {outlet} to have name {LEDnames[LEDname]}")
            log.debug('Turning LED on')
            kpfpower[f"OUTLET_{outlet}"].write('On')

            # Time shim to let FVC service connect to camera after power up
            time.sleep(10)
            SetFVCExpTime.execute({'camera': camera,
                                   'exptime': exptimes[camera][LEDname]})
            lastfile = TakeFVCExposure.execute({'camera': camera})
            log.info(f'  LASTFILE: {lastfile}')
            log.debug('Turning LED off')
            kpfpower[f"OUTLET_{outlet}"].write('Off')

            # Append to images file
            if images_file.exists() is False:
                # Write header line
                header = f"# HST date, camera, LED, file\n"
                with open(images_file, 'w') as f:
                    f.write(header)
            row = f"{now_str}, {camera:4s}, {LEDname:8s}, {lastfile}\n"
            with open(images_file, 'a') as f:
                f.write(row)

        if args.get('SCI', False) is True:
            take_back_illuminated_image('SCI', 'Science')
            take_back_illuminated_image('SCI', 'Sky')
            take_back_illuminated_image('SCI', 'ExpMeter')
        if args.get('CAHK', False) is True:
            take_back_illuminated_image('CAHK', 'CaHK')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument("--Science", "--Sci", "--science", "--sci", "--SCI",
                            dest="SCI",
                            default=False, action="store_true",
                            help="Image science and sky fibers with science FVC?")
        parser.add_argument("--CaHK", "--HK", "--cahk", "--hk", "--CAHK",
                            dest="CAHK",
                            default=False, action="store_true",
                            help="Image CaHK fiber with CaHK FVC?")
        return super().add_cmdline_args(parser, cfg)
