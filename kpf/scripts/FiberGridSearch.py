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
from ..fiu.StartTipTilt import StartTipTilt
from ..fiu.StopTipTilt import StopTipTilt
from ..fvc.TakeFVCExposure import TakeFVCExposure
from ..fvc.SetFVCExpTime import SetFVCExpTime
from ..guider.TakeGuiderExposure import TakeGuiderExposure
from ..spectrograph.SetExptime import SetExptime
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
## fiber_grid_search
##-------------------------------------------------------------------------
class FiberGridSearch(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_eng_fgs'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.4')
        check_input(OB, 'nx')
        check_input(OB, 'ny')
        check_input(OB, 'dx')
        check_input(OB, 'dy')
        check_input(OB, 'FVCs')
        check_input(OB, 'ExpMeter_exptime')
        FVCs = OB.get('FVCs', '').split(',')
        for FVC in FVCs:
            if FVC not in ['SCI', 'CAHK', 'EXT']:
                raise FailedPreCondition(f"FVC {FVC} not supported")
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

        FVCs = OB.get('FVCs', '').split(',')
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
        total_exptime = ExpMeter_exptime = OB.get('TimeOnPosition')
        SetExptime.execute({'Exptime': total_exptime})

        # Configure Exposure Meter
        kpf_expmeter = ktl.cache('kpf_expmeter')
        ExpMeter_exptime = OB.get('ExpMeter_exptime')
        log.info(f"Setting kpf_expmeter.EXPOSURE = {ExpMeter_exptime:.2f} s")
        kpf_expmeter['EXPOSURE'].write(ExpMeter_exptime)

        # Set up FVCs
        kpffvc = ktl.cache('kpffvc')
        for FVC in ['SCI', 'CAHK', 'EXT']:
            if FVC in FVCs and OB.get(f'{FVC}FVC_exptime', None) != None:
                exptime = OB.get(f'{FVC}FVC_exptime')
                log.info(f"Setting {FVC} FVC Exptime = {exptime:.2f} s")
                SetFVCExpTime.execute({'camera': FVC, 'exptime': exptime})

        for i,xi in enumerate(xis):
            for j,yi in enumerate(yis):
                # Offset to position
                log.info(f"Stopping tip tilt")
                StopTipTilt.execute({})
                log.info(f"Adjusting target to ({xs[i]:.2f}, {ys[j]:.2f}) ({xis[i]}, {yis[j]})")
                SetTipTiltTargetPixel.execute({'x': xs[i], 'y': ys[j]})
                log.info(f"Starting tip tilt")
                StartTipTilt.execute({})

                # Take Exposure to make sure we wait at least one cycle
                log.info(f"Taking extra guider exposure to wait one cycle")
                TakeGuiderExposure.execute({}) # Blocks until done

                sleep_time = 5
                log.info(f"Sleeping {sleep_time} s to allow tip tilt loop to settle")
                time.sleep(sleep_time)

                obj_choice = kpfguide['OBJECT_CHOICE'].read()
                obj_pos = kpfguide[obj_choice].read(binary=True)
                log.debug(f'{obj_choice} is at {obj_pos[0]:.1f} {obj_pos[1]:.1f}')
                if obj_pos[0] < -1 or obj_pos[1] < -1:
                    log.error(f"  --> Lost star <--")
                    log.error(f"You have 30 seconds to recover")
                    time.sleep(30)

                # Start Exposure Meter and Science Cameras
                WaitForReady.execute({})
                kpfexpose['OBJECT'].write(f'Grid search {xs[i]}, {ys[j]} arcsec')
                log.info(f"Starting kpfexpose cameras")
                StartExposure.execute({})
                # Begin timestamp for history retrieval
                begin = time.time()

                # Start FVC Exposures
                initial_lastfile = {}
                for FVC in ['SCI', 'CAHK', 'EXT']:
                    if FVC in FVCs:
                        initial_lastfile[FVC] = kpffvc[f"{FVC}LASTFILE"].read()
                        log.debug(f"  Initial lastfile for {FVC} = {initial_lastfile[FVC]}")
                        log.info(f"  Starting {FVC} FVC exposure")
                        TakeFVCExposure.execute({'camera': FVC, 'wait': False})

                # Expose using CRED2
                log.info(f"  Taking CRED2 exposure")
                TakeGuiderExposure.execute({}) # Blocks until done
                lastfile = kpfguide[f"LASTFILE"].read()
                row = {'file': lastfile, 'camera': 'CRED2',
                       'dx': xs[i], 'dy': ys[j]}
                images.add_row(row)

                # Here's where we wait for the duration of the FVC exposures

                # Collect files for FVC exposures
                for FVC in ['SCI', 'CAHK', 'EXT']:
                    if FVC in FVCs:
                        log.info(f"  Looking for output file for {FVC}")
                        expr = f'($kpffvc.{FVC}LASTFILE != "{initial_lastfile[FVC]}")'
                        log.debug(f"  Waiting for: {expr}")
                        if ktl.waitFor(expr, timeout=20) is False:
                            lastfile = kpffvc[f'{FVC}LASTFILE'].read()
                            log.error('No new FVC file found')
                            log.error(f"  expecting: {nextfile[FVC]}")
                            log.error(f"  kpffvc.{FVC}LASTFILE = {lastfile}")
                        else:
                            lastfile = kpffvc[f'{FVC}LASTFILE'].read()
                            log.debug(f"Found {lastfile}")
                            row = {'file': lastfile, 'camera': FVC,
                                   'dx': xs[i], 'dy': ys[j]}
                            images.add_row(row)

                # Here's where we wait for the remainder of the TimeOnPosition
                log.info(f"  Waiting for kpfexpose to be ready")
                WaitForReady.execute({})

                # Stop Exposure Meter
                log.info(f"  Waiting for ExpMeter to be Ready")
                EMsuccess = ktl.waitFor('$kpf_expmeter.EXPSTATE == Ready', timeout=5)
                time.sleep(0.5) # Time shim because paranoia
                if EMsuccess is True:
                    lastfile = kpf_expmeter['FITSFILE'].read()
                else:
                    lastfile = 'failed'
                log.info(f'  Done.  Lastfile={lastfile}')
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
            if fluxes_file.exists():
                fluxes_file.unlink()
            expmeter_flux.write(fluxes_file, format='ascii.csv')

        if images_file.exists():
            images_file.unlink()
        images.write(images_file, format='ascii.csv')
        if fluxes_file.exists():
            fluxes_file.unlink()
        expmeter_flux.write(fluxes_file, format='ascii.csv')

        SetTipTiltTargetPixel.execute({'x': xpix0, 'y': ypix0})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
