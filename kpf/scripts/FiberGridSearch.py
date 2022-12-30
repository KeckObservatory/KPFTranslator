import os
from pathlib import Path
import logging
from datetime import datetime, timedelta
import time
import yaml

import numpy as np
from astropy.table import Table, Row

import ktl
import keygrabber

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, obey_scriptrun, check_scriptstop
from ..fiu.SetTipTiltTargetPixel import SetTipTiltTargetPixel
from ..fvc.TakeFVCExposure import TakeFVCExposure
from ..fvc.SetFVCExpTime import SetFVCExpTime
from ..guider.TakeGuiderExposure import TakeGuiderExposure
from ..spectrograph.StartExposure import StartExposure
from ..spectrograph.WaitForReady import WaitForReady
from ..spectrograph.WaitForReadout import WaitForReadout
from ..spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from ..spectrograph.SetTimedShutters import SetTimedShutters
from ..spectrograph.SetTriggeredDetectors import SetTriggeredDetectors


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
def offset(x, y, offset_system='ttm'):
    if offset_system == 'ttm':
        SetTipTiltTargetPixel.execute({'x': x, 'y': y})
    elif offset_system == 'azel':
        from ddoi_telescope_translator.azel import OffsetAzEl
        from ddoi_telescope_translator.wftel import WaitForTel
        OffsetAzEl.execute({'tcs_offset_az': x,
                            'tcs_offset_el': y,
                            'relative': False})
        WaitForTel.execute({})
        time.sleep(2)
    elif offset_system == 'gxy':
        from ddoi_telescope_translator.gxy import OffsetGuiderCoordXY
        from ddoi_telescope_translator.wftel import WaitForTel
        OffsetGuiderCoordXY({'guider_x_offset': x,
                             'guider_y_offset': y,
                             'instrument': 'KPF',
                             'relative': False})
        WaitForTel.execute({})
        time.sleep(2)
    elif offset_system == 'custom':
        dcs = ktl.cache('dcs')
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
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_eng_fgs'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.3')
        check_input(OB, 'offset_system', allowed_values=['azel', 'gxy', 'ttm', 'custom'])
        check_input(OB, 'min_time_on_grid_position', value_min=0)
        check_input(OB, 'nx')
        check_input(OB, 'ny')
        check_input(OB, 'dx')
        check_input(OB, 'dy')
        check_input(OB, 'cameras')
        cameras = OB.get('cameras', '').split(',')
        for camera in cameras:
            if camera not in ['CRED2', 'SCI', 'CAHK', 'EXT', 'ExpMeter']:
                raise FailedPreCondition(f"Camera {camera} not supported")
        return True

    @classmethod
    @register_script(Path(__file__).name, os.getpid())
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running FiberGridSearch OB")
        for key in OB:
            log.debug(f"  {key}: {OB[key]}")
        log.info('-------------------------')

        images_file = log_dir / Path(f'{this_file_name}_images_{now_str}.txt')
        fluxes_file = log_dir / Path(f'{this_file_name}_fluxes_{now_str}.txt')

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

        offset_system = OB.get('offset_system')
        cameras = OB.get('cameras', '').split(',')
        nx = OB.get('nx')
        ny = OB.get('ny')
        dx = OB.get('dx')
        dy = OB.get('dy')
        xis = [xi for xi in range(int(-nx/2),int((nx+1)/2),1)]
        yis = [yi for yi in range(int(-ny/2),int((ny+1)/2),1)]
        xs = [xi*dx for xi in xis]
        ys = [yi*dy for yi in yis]

        # Set up guider (assume parameters set during acquisition of star)
        kpfguide = ktl.cache('kpfguide')
        if offset_system == 'ttm':
            xpix0, ypix0 = kpfguide['PIX_TARGET'].read(binary=True)
            log.info(f"Center pixel is {xpix0:.2f}, {ypix0:.2f}")
            # Pixel targets must be in absolute coordinates
            xs = [xpix+xpix0 for xpix in xs]
            ys = [ypix+ypix0 for ypix in ys]

        # Set up kpfexpose
        kpfexpose = ktl.cache('kpfexpose')
        SetSourceSelectShutters.execute({'SSS_Science': True, 'SSS_Sky': True})
        SetTimedShutters.execute({'TimedShutter_Scrambler': True})
        SetTriggeredDetectors.execute({'TriggerExpMeter': True})

        # Configure Exposure Meter
        if 'ExpMeter' in cameras and OB.get('ExpMeter_exptime', None) != None:
            kpf_expmeter = ktl.cache('kpf_expmeter')
            ExpMeter_exptime = OB.get('ExpMeter_exptime')
            log.info(f"Setting kpf_expmeter.EXPOSURE = {ExpMeter_exptime:.2f} s")
            kpf_expmeter['EXPOSURE'].write(ExpMeter_exptime)

        # Set up FVCs
        kpffvc = ktl.cache('kpffvc')
        for camera in ['SCI', 'CAHK', 'CAL', 'EXT']:
            if camera in cameras and OB.get(f'{camera}FVC_exptime', None) != None:
                exptime = OB.get(f'{camera}FVC_exptime')
                log.info(f"Setting {camera} FVC Exptime = {exptime:.2f} s")
                SetFVCExpTime.execute({'camera': camera, 'exptime': exptime})

        for i,xi in enumerate(xis):
            for j,yi in enumerate(yis):
                # Offset to position
                log.info(f"Offsetting: {offset_system} to ({xs[i]:.2f}, {ys[j]:.2f})")
                offset(xs[i], ys[j], offset_system=offset_system)

                # Take Exposure to make sure we wait at least one cycle
                log.info(f"Taking extr guider exposure to wait one cycle")
                TakeGuiderExposure.execute({})

                # Start Exposure Meter and Science Cameras
                WaitForReady.execute({})
                kpfexpose['OBJECT'].write(f'Grid search {xs[i]}, {ys[j]} arcsec')
                # Start CRED2 Cube Collection
                last_cube_file = kpfguide['LASTTRIGFILE'].read()
                log.info(f"  Starting CRED2 cube")
                kpfguide['TRIGGER'].write('Active')
                log.info(f"  Starting kpfexpose cameras")
                StartExposure.execute({})
                # Begin timestamp for history retrieval
                begin = time.time()

                # Start FVC Exposures
                initial_lastfile = {}
                for camera in ['SCI', 'CAHK', 'CAL', 'EXT']:
                    if camera in cameras:
                        initial_lastfile[camera] = kpffvc[f"{camera}LASTFILE"].read()
                        log.debug(f"  Initial lastfile for {camera} = {initial_lastfile[camera]}")
                        log.info(f"  Starting {camera} FVC exposure")
                        TakeFVCExposure.execute({'camera': camera, 'wait': False})

                # Expose using CRED2
                if 'CRED2' in cameras:
                    log.info(f"  Taking CRED2 exposure")
                    TakeGuiderExposure.execute({})
                    lastfile = kpfguide[f"LASTFILE"].read()
                    row = {'file': lastfile, 'camera': 'CRED2',
                           'dx': xs[i], 'dy': ys[j]}
                    images.add_row(row)

                # Collect files for FVC exposures
                for camera in ['SCI', 'CAHK', 'CAL', 'EXT']:
                    if camera in cameras:
                        log.info(f"  Looking for output file for {camera}")
                        expr = f'($kpffvc.{camera}LASTFILE != "{initial_lastfile[camera]}")'
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

                # Ensure minimum time on position is enforced
                duration = OB.get('min_time_on_grid_position')
                end = datetime.fromtimestamp(begin) + timedelta(seconds=duration)
                now = datetime.now()
                while now < end:
                    time.sleep(0.2)
                    now = datetime.now()

                # Stop Exposure Meter
                log.info(f"  Waiting for kpfexpose readout to start")
                WaitForReadout.execute({})
                log.info(f"  Stopping CRED2 cube")
                kpfguide['TRIGGER'].write('Inactive')
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

                # Collect CRED2 Cube
                expr = f'($kpfguide.LASTTRIGFILE != "{last_cube_file}")'
                log.debug(f"  Waiting for: {expr}")
                if ktl.waitFor(expr, timeout=60) is False:
                    log.error('No new CRED2 cube file found')
                    log.error(f"  previous: {last_cube_file}")
                    last_cube_file = kpfguide['LASTTRIGFILE'].read()
                    log.error(f"  kpffvc.LASTTRIGFILE = {last_cube_file}")
                else:
                    last_cube_file = kpfguide['LASTTRIGFILE'].read()
                    log.debug(f"Found {last_cube_file}")
                    row = {'file': last_cube_file, 'camera': 'cube',
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
            if 'ExpMeter' in cameras:
                if fluxes_file.exists():
                    fluxes_file.unlink()
                expmeter_flux.write(fluxes_file, format='ascii.csv')

        if images_file.exists():
            images_file.unlink()
        images.write(images_file, format='ascii.csv')
        if 'ExpMeter' in cameras:
            if fluxes_file.exists():
                fluxes_file.unlink()
            expmeter_flux.write(fluxes_file, format='ascii.csv')

        # Send offsets back to 0,0
        if offset_system == 'ttm':
            offset(xpix0, ypix0, offset_system=offset_system)
        else:
            offset(0, 0, offset_system=offset_system)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
