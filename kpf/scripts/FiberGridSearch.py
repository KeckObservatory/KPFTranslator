from pathlib import Path
import logging
from datetime import datetime
import time
from collections import OrderedDict

from astropy.table import Table, Row

import ktl
import keygrabber

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from ..fiu.InitializeTipTilt import InitializeTipTilt
from ..fiu.SetTipTilt import SetTipTilt
from ..fvc.TakeFVCExposure import TakeFVCExposure
from ..guider.TakeGuiderExposure import TakeGuiderExposure


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
now = datetime.utcnow()
now_str = now.strftime('%Y%m%dat%H%M%S')
LogFileName = Path(f'~/logs/{this_file_name}_{now_str}.log').expanduser()
LogFileHandler = logging.FileHandler(LogFileName)
LogFileHandler.setLevel(logging.DEBUG)
LogFileHandler.setFormatter(LogFormat)
log.addHandler(LogFileHandler)


##-------------------------------------------------------------------------
## fiber_grid_search
##-------------------------------------------------------------------------
class FiberGridSearch(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        log.info("###########")
        if args.get('comment', '') != '': log.info(args.get('comment', ''))
        log.info(f"args = {args}")
        log.info("###########")

        images_file = Path(f'~/logs/{this_file_name}_images_{now_str}.txt').expanduser()
        fluxes_file = Path(f'~/logs/{this_file_name}_fluxes_{now_str}.txt').expanduser()

        images = Table(names=('file', 'camera', 'dx', 'dy'),
                       dtype=('a90',  'a10',    'f4', 'f4'))
        expmeter_flux = Table(names=('dx', 'dy', 'f1', 'f2', 'f3', 'f4'),
                              dtype=('f4', 'f4', 'f4', 'f4', 'f4', 'f4'))

        nx = args.get('nx', 3)
        ny = args.get('ny', 3)
        dx = args.get('dx', 0.25)
        dy = args.get('dy', 0.25)
        xis = [xi for xi in range(int(-nx/2),int((nx+1)/2),1)]
        yis = [yi for yi in range(int(-ny/2),int((ny+1)/2),1)]
        xs = [xi*dx for xi in xis]
        ys = [yi*dy for yi in yis]

        # Set up tip tilt system
        InitializeTipTilt.execute({})

        # Set up Exposure Meter
        if 'ExpMeter' in args.get('cameras', ''):
            kpf_expmeter = ktl.cache('kpf_expmeter')
            kpfexpose = ktl.cache('kpfexpose')
            kpf_expmeter['record'].write('Yes')
            kpfexpose['SRC_SHUTTERS'].write('SciSelect,SkySelect')
            kpfexpose['SCRAMBLER_SHTR'].write('open')

        # Set up FVCs
        kpffvc = ktl.cache('kpffvc')

        # Set up guider
        if 'CRED2' in args.get('cameras', ''):
            kpfguide = ktl.cache('kpfguide')

        for i,xi in enumerate(xis):
            for j,yi in enumerate(yis):
                # Offset to position
                log.info(f"Offsetting to position ({xs[i]}, {ys[j]})")
                SetTipTilt.execute({'x': xs[i], 'y': ys[j]})

                # Start Exposure Meter
                if 'ExpMeter' in args.get('cameras', ''):
                    log.info(f"  Starting exposure meter")
                    kpf_expmeter['OBJECT'].write(f'Grid search {xs[i]}, {ys[j]} arcsec')
                    exptime = kpf_expmeter['EXPOSURE'].read(binary=True)
                    ktl.waitFor('($kpf_expmeter.EXPOSE == Ready)', timeout=exptime+2)
                    kpf_expmeter['EXPOSE'].write('Start')
                    # Begin timestamp for history retrieval
                    begin = time.time()

                # Start FVC Exposures
                initial_lastfile = {}
                for camera in ['SCI', 'CAHK', 'CAL', 'EXT']:
                    if camera in args.get('cameras', '').split(','):
                        initial_lastfile[camera] = kpffvc[f"{camera}LASTFILE"].read()
                        log.debug(f"  Initial lastfile for {camera} = {initial_lastfile[camera]}")
                        log.info(f"  Starting {camera} FVC exposure")
#                         kpffvc[f"{camera}EXPOSE"].write('yes', wait=False)
                        TakeFVCExposure.execute({'camera': camera, 'wait': False})

                # Expose using CRED2
                if 'CRED2' in args.get('cameras', '').split(','):
                    log.info(f"  Taking CRED2 exposure")
                    TakeGuiderExposure.execute({})
                    lastfile = kpfguide[f"LASTFILE"].read()
                    row = {'file': lastfile, 'camera': 'CRED2',
                           'dx': xs[i], 'dy': ys[j]}
                    images.add_row(row)

                # Collect files for FVC exposures
                for camera in ['SCI', 'CAHK', 'CAL', 'EXT']:
                    if camera in args.get('cameras', '').split(','):
                        log.info(f"  Looking for output file for {camera}")
                        expr = f'($kpffvc.{camera}LASTFILE != "{initial_lastfile[camera]}")'
                        log.debug(f"  Waiting for: {expr}")
                        ktl.waitFor(expr, timeout=20)
                        lastfile = kpffvc[f'{camera}LASTFILE'].read()
                        log.debug(f"Found {lastfile}")
                        row = {'file': lastfile, 'camera': camera,
                               'dx': xs[i], 'dy': ys[j]}
                        images.add_row(row)

                # Stop Exposure Meter
                if 'ExpMeter' in args.get('cameras', '').split(','):
                    log.info(f"  Stopping exposure meter")
                    kpf_expmeter['EXPOSE'].write('end')
                    ktl.waitFor('$kpf_expmeter.EXPSTATE == Ready')
                    kpf_expmeter['CUR_COUNTS'].wait()
                    lastfile = kpf_expmeter['FITSFILE'].read()
                    row = {'file': lastfile, 'camera': 'ExpMeter',
                           'dx': xs[i], 'dy': ys[j]}
                    images.add_row(row)
                    # Retrieve keyword history
                    end = time.time()
                    log.info(f"  Retrieving keyword history")
                    kws = {'kpf_expmeter': ['CUR_COUNTS']}
                    counts_history = keygrabber.retrieve(kws, begin=begin, end=end)
                    # Extract counts and save to table
                    for entry in counts_history:
                        value_floats = [float(v) for v in entry['ascvalue'].split()]
                        ts = datetime.fromtimestamp(entry['time']).strftime('%Y-%m-%d %H:%M:%S')
                        log.debug(f"  {ts}: {value_floats}")
                        expmeter_flux.add_row({'dx': xi, 'dy': yi,
                                               'f1': value_floats[0],
                                               'f2': value_floats[1],
                                               'f3': value_floats[2],
                                               'f4': value_floats[3],
                                               })

            if images_file.exists():
                images_file.unlink()
            images.write(images_file, format='ascii.csv')
            if 'ExpMeter' in args.get('cameras', '').split(','):
                if fluxes_file.exists():
                    fluxes_file.unlink()
                expmeter_flux.write(fluxes_file, format='ascii.csv')

        if images_file.exists():
            images_file.unlink()
        images.write(images_file, format='ascii.csv')
        if 'ExpMeter' in args.get('cameras', '').split(','):
            if fluxes_file.exists():
                fluxes_file.unlink()
            expmeter_flux.write(fluxes_file, format='ascii.csv')

        # Send tip tilt back to 0,0
        InitializeTipTilt.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        """
        The arguments to add to the command line interface.
        """
        args_to_add = OrderedDict()
        args_to_add['nx'] = {'type': int,
                    'help': 'Number of grid points in the X direction'}
        args_to_add['ny'] = {'type': int,
                    'help': 'Number of grid points in the Y direction'}
        args_to_add['dx'] = {'type': float,
                    'help': 'Distance (arcsec) between grid points in X'}
        args_to_add['dy'] = {'type': float,
                    'help': 'Distance (arcsec) between grid points in Y'}
        args_to_add['cameras'] = {'type': str,
                    'help': 'List of cameras'}
        args_to_add['comment'] = {'type': str,
                    'help': 'Comment for log'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
