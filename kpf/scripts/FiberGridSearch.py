from pathlib import Path
import logging
from datetime import datetime
import time
from collections import OrderedDict

import numpy as np
from astropy.table import Table, Row

import ktl
import keygrabber

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from ddoi_telescope_translator.azel import OffsetAzEl
from ddoi_telescope_translator.gxy import OffsetGuiderCoordXY
from ddoi_telescope_translator.wftel import WaitForTel

from ..fiu.InitializeTipTilt import InitializeTipTilt
from ..fiu.SetTipTilt import SetTipTilt
from ..fvc.TakeFVCExposure import TakeFVCExposure
from ..guider.TakeGuiderExposure import TakeGuiderExposure
from ..spectrograph.StartExposure import StartExposure
from ..spectrograph.WaitForReady import WaitForReady
from ..spectrograph.WaitForReadout import WaitForReadout


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


##-------------------------------------------------------------------------
## offset
##-------------------------------------------------------------------------
def offset(x, y, offset_system='gxy'):
    if offset_system == 'ttm':
        SetTipTilt.execute({'x': x, 'y': y)
        # If the tip/tilt system is active, and you're offloading,
        # what you want is to set the kpfguide.CURRENT_BASE keyword
        #to a new value (in pixels)
    elif offset_system == 'azel':
       OffsetAzEl.execute({'tcs_offset_az': x,
                           'tcs_offset_el': y,
                           'relative': False})
        WaitForTel.execute({})
        time.sleep(2)
    elif offset_system == 'gxy':
        OffsetGuiderCoordXY({'guider_x_offset': x,
                             'guider_y_offset': y,
                             'instrument': 'KPF',
                             'relative': False})
        WaitForTel.execute({})
        time.sleep(2)
    elif offset_system == 'custom':
        try:
            dcs['azoff'].write(x)
        except Exception as e:
            log.warning(f"Retrying dcs['azoff'].write({x})")
            log.warning(e)
            time.sleep(0.1)
            dcs['azoff'].write(x)
        time.sleep(0.1)
        try:
            dcs['eloff'].write(y)
        except Exception as e:
            log.warning(f"Retrying dcs['eloff'].write({y})")
            log.warning(e)
            time.sleep(0.1)
            dcs['eloff'].write(y)
        time.sleep(0.1)
        try:
            dcs['rel2base'].write(True)
        except Exception as e:
            log.warning(f"Retrying dcs['rel2base'].write(True)")
            log.warning(e)
            time.sleep(0.1)
            dcs['rel2base'].write(True)
    elif offset_system in [None, '']:
        log.warning(f"  No offset system selected")
        pass


##-------------------------------------------------------------------------
## fiber_grid_search
##-------------------------------------------------------------------------
class FiberGridSearch(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        offset_system = args.get('offset', 'gxy')
        if offset_system not in ['azel', 'gxy', 'ttm']:
            print(f"Offset mode {offset_system} not supported")
            return False
        cameras = args.get('cameras', '').split(',')
        for camera in cameras:
            if camera not in ['CRED2', 'SCI', 'CAHK', 'EXT', 'ExpMeter']:
                print(f"Camera {camera} not supported")
            return False
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
        expmeter_flux = Table(names=('i', 'j', 'dx', 'dy',
                                     'bck1', 'bck2', 'bck3', 'bck4',
                                     'cur1', 'cur2', 'cur3', 'cur4',
                                     'raw1', 'raw2', 'raw3', 'raw4',
                                     'nimages'),
                              dtype=('i4', 'i4', 'f4', 'f4',
                                     'f4', 'f4', 'f4', 'f4',
                                     'f4', 'f4', 'f4', 'f4',
                                     'f4', 'f4', 'f4', 'f4',
                                     'i4'))

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

        # Set up kpfexpose
        kpf_expmeter = ktl.cache('kpf_expmeter')
        kpfexpose = ktl.cache('kpfexpose')
        kpfexpose['SRC_SHUTTERS'].write('SciSelect,SkySelect')
        kpfexpose['TIMED_SHUTTERS'].write('Scrambler')
        kpfexpose['TRIG_TARG'].write('Red,Green,ExpMeter')
        log.info(f"SRC_SHUTTERS: {kpfexpose['SRC_SHUTTERS'].read()}")
        log.info(f"TIMED_SHUTTERS: {kpfexpose['TIMED_SHUTTERS'].read()}")
        log.info(f"TRIG_TARG: {kpfexpose['TRIG_TARG'].read()}")

        # Set up FVCs
        kpffvc = ktl.cache('kpffvc')

        # Set up guider
        if 'CRED2' in args.get('cameras', ''):
            kpfguide = ktl.cache('kpfguide')

        # Set up DCS
        dcs = ktl.cache('dcs')

        for i,xi in enumerate(xis):
            for j,yi in enumerate(yis):
                # Offset to position
                log.info(f"Offsetting: {offset_system} to ({xs[i]:.2f}, {ys[j]:.2f})")
                offset(xs[i], ys[j], offset_system=args.get('offset', 'gxy'))

                # Start Exposure Meter and Science Cameras
                WaitForReady.execute({})
                kpfexpose['OBJECT'].write(f'Grid search {xs[i]}, {ys[j]} arcsec')
                log.info(f"  Starting kpfexpose cameras")
                StartExposure.execute({})
                # Begin timestamp for history retrieval
                begin = time.time()

                # Start FVC Exposures
                nextfile = {}
                for camera in ['SCI', 'CAHK', 'CAL', 'EXT']:
                    if camera in args.get('cameras', '').split(','):
                        nextfile[camera] = kpffvc[f"{camera}LASTFILE"].read()
                        log.debug(f"  Nextfile for {camera} = {nextfile[camera]}")
                        log.info(f"  Starting {camera} FVC exposure")
                        TakeFVCExposure.execute({'camera': camera, 'wait': False})

                # Expose using CRED2
                if 'CRED2' in args.get('cameras', '').split(','):
                    log.info(f"  Taking CRED2 exposure")
                    TakeGuiderExposure.execute({})
                    lastfile = kpfguide[f"LASTFILE"].read()
                    row = {'file': lastfile, 'camera': 'CRED2',
                           'dx': xs[i], 'dy': ys[j]}
                    images.add_row(row)

                    log.info(f"  Taking Second CRED2 exposure")
                    TakeGuiderExposure.execute({})
                    lastfile = kpfguide[f"LASTFILE"].read()
                    row = {'file': lastfile, 'camera': 'CRED2',
                           'dx': xs[i], 'dy': ys[j]}
                    images.add_row(row)


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
                                   'dx': xs[i], 'dy': ys[j]}
                            images.add_row(row)

                # Stop Exposure Meter
                log.info(f"  Waiting for kpfexpose readout to start")
                WaitForReadout.execute({})
                log.info(f"  Waiting for ExpMeter DRP")
                kpf_expmeter['CUR_COUNTS'].wait()
                log.info(f"  Waiting for ExpMeter to be Ready")
                EMsuccess = ktl.waitFor('$kpf_expmeter.EXPSTATE == Ready')
                if EMsuccess is True:
                    lastfile = kpf_expmeter['FITSFILE'].read()
                else:
                    lastfile = 'failed'
                    row = {'file': lastfile, 'camera': 'ExpMeter',
                           'dx': xs[i], 'dy': ys[j]}
                images.add_row(row)
                # Retrieve keyword history
                end = time.time()
                expmeter_data = {'dx': xs[i], 'dy': ys[j],
                                 'i': i, 'j': j,
                                 }
                for counts_kw in ['CUR_COUNTS', 'RAW_COUNTS', 'BCK_COUNTS']:
                    log.info(f"  Retrieving keyword history for {counts_kw}")
                    kws = {'kpf_expmeter': [counts_kw]}
                    counts_history = keygrabber.retrieve(kws, begin=begin, end=end)
                    # Extract counts and save to table
                    fluxes = np.zeros((len(counts_history), 4))
                    for k,entry in enumerate(counts_history):
                        value_floats = [float(v) for v in entry['ascvalue'].split()]
                        ts = datetime.fromtimestamp(entry['time']).strftime('%Y-%m-%d %H:%M:%S')
                        log.debug(f"  {ts}: {value_floats}")
                        fluxes[k] = value_floats
                    avg_fluxes = np.mean(fluxes, axis=0)
                    expmeter_data[f"{counts_kw[:3].lower()}1"] = avg_fluxes[0]
                    expmeter_data[f"{counts_kw[:3].lower()}2"] = avg_fluxes[1]
                    expmeter_data[f"{counts_kw[:3].lower()}3"] = avg_fluxes[2]
                    expmeter_data[f"{counts_kw[:3].lower()}4"] = avg_fluxes[3]
                expmeter_data['nimages'] = len(counts_history)
                expmeter_flux.add_row(expmeter_data)

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
#         InitializeTipTilt.execute({})
        GoToBase.execute({})
        WaitForTel.execute({})

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
        args_to_add['offset'] = {'type': str,
                    'help': 'Offset method to use: azel, gxy, ttm'}
        args_to_add['comment'] = {'type': str,
                    'help': 'Comment for log'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
