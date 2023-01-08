import os
from pathlib import Path
import logging
from datetime import datetime, timedelta
import time
import yaml
import subprocess

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
from ..guider.StartTriggerFile import StartTriggerFile
from ..guider.StopTriggerFile import StopTriggerFile
from ..guider.WaitForTriggerFile import WaitForTriggerFile
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
class GridSearch(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_eng_grid'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.4')
        check_input(OB, 'Grid', allowed_values=['TipTilt', 'SciADC'])
        check_input(OB, 'nx')
        check_input(OB, 'ny')
        check_input(OB, 'dx')
        check_input(OB, 'dy')
        check_input(OB, 'ExpMeter_exptime')
        FVCs = OB.get('FVCs', '').split(',')
        for FVC in FVCs:
            if FVC not in ['SCI', 'CAHK', 'EXT', '']:
                raise FailedPreCondition(f"FVC {FVC} not supported")
        return True

    @classmethod
    @register_script(Path(__file__).name, os.getpid())
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for key in OB:
            log.debug(f"  {key}: {OB[key]}")
        log.info('-------------------------')

        grid = OB.get('Grid')

        images_file = log_dir / Path(f'{grid}{this_file_name}_images_{now_str}.txt')
        fluxes_file = log_dir / Path(f'{grid}{this_file_name}_fluxes_{now_str}.txt')

        images = Table(names=('file', 'camera', 'x', 'y'),
                       dtype=('a90',  'a10',    'f4', 'f4'))
        expmeter_flux = Table(names=('i', 'j', 'x', 'y',
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
        log.info('Setting TRIGCUBE Inactive')
        kpfguide['TRIGCUBE'].write('Inactive')
        if grid == 'TipTilt':
            xpix0, ypix0 = kpfguide['PIX_TARGET'].read(binary=True)
            log.info(f"Center pixel is {xpix0:.2f}, {ypix0:.2f}")
            # Pixel targets must be in absolute coordinates
            xs = [xpix+xpix0 for xpix in xs]
            ys = [ypix+ypix0 for ypix in ys]
        elif grid == 'SciADC':
            kpffiu = ktl.cache('kpffiu')
            kpffiu['ADCTRACK'].write('Off')
            nominalx, nominaly = kpffiu['ADCPRISMS'].read(binary=True)
            x0 = OB.get('ADC1Position')
            if str(x0).lower() == 'nominal':
                x0 = nominalx
            else:
                x0 = float(OB.get('ADC1Position'))
            y0 = OB.get('ADC2Position')
            if str(y0).lower() == 'nominal':
                y0 = nominaly
            else:
                y0 = float(OB.get('ADC2Position'))
            log.info(f"ADC starting position: {x0:.1f} {y0:.1f}")
            # Apply reverse rotation if requested
            if OB.get('ADC1Reverse', False) is True:
                x0 = -x0
            if OB.get('ADC2Reverse', False) is True:
                y0 = -y0
            log.info(f"ADC reverse nominal position: {x0:.1f} {y0:.1f}")
            # Apply flip if requested
            if OB.get('ADC1Flip', False) is True:
                x0 += 180
            if OB.get('ADC2Flip', False) is True:
                y0 += 180
            log.info(f"ADC flip nominal position: {x0:.1f} {y0:.1f}")
            xs = [x+x0 for x in xs]
            ys = [y+y0 for y in ys]

        # Set up kpfexpose
        kpfexpose = ktl.cache('kpfexpose')
        SetSourceSelectShutters.execute(OB)
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
            yis.reverse()
            for j,yi in enumerate(yis):
                check_scriptstop()

                if grid == 'TipTilt':
                    ##------------------------------------------------------
                    ## Tip Tilt
                    ##------------------------------------------------------
                    log.info(f"Adjusting target to ({xs[i]:.2f}, {ys[j]:.2f}) ({xis[i]}, {yis[j]})")
                    SetTipTiltTargetPixel.execute({'x': xs[i], 'y': ys[j]})
                    sleep_time = 5
                    log.debug(f"Sleeping {sleep_time} s to allow tip tilt loop to settle")
                    time.sleep(sleep_time)
                    # Check for lost star
                    obj_choice = kpfguide['OBJECT_CHOICE'].read()
                    if obj_choice in [None, 'None']:
                        log.error(f"  --> Lost star <--")
                        log.info(f"Stopping tip tilt")
                        StopTipTilt.execute({})
                        time.sleep(1)
                        log.info(f"Starting tip tilt")
                        StartTipTilt.execute({})
                        time.sleep(5)
                        # Check for lost star
                        obj_choice = kpfguide['OBJECT_CHOICE'].read()
                        if obj_choice in [None, 'None']:
                            log.error(f"  --> Lost star <--")
                            subprocess.call(['kpf', 'restart', 'kpfguide2'])
                            time.sleep(5)
                            log.info(f"Starting tip tilt")
                            StartTipTilt.execute({})
                            time.sleep(5)
                            obj_choice = kpfguide['OBJECT_CHOICE'].read()
                            if obj_choice in [None, 'None']:
                                log.error(f"  --> Lost star <--")
                                raise KPFError('Lost Star')
                elif grid == 'SciADC':
                    ##------------------------------------------------------
                    ## Science ADC
                    ##------------------------------------------------------
                    log.info(f"Offsetting to ({xs[i]:.2f}, {ys[j]:.2f}) ({xis[i]}, {yis[j]})")
                    kpffiu['ADC1VAL'].write(xs[i])
                    kpffiu['ADC2VAL'].write(ys[j])
                    log.info(f"Absolute position: {xs[i]:.1f} {ys[j]:.1f}")
                    expr = '($kpffiu.ADC1STA == Ready) and ($kpffiu.ADC2STA == Ready)'
                    success = ktl.waitFor(expr, timeout=2*max([dx*nx, dy*ny])/5)
                    if success is not True:
                        ADC1STA = kpffiu['ADC1STA'].read()
                        ADC2STA = kpffiu['ADC2STA'].read()
                        msg = f'Timed out waiting for ADCs: ADC1STA={ADC1STA} ADC2STA={ADC2STA}'
                        raise KPFException(msg)

                # Start Exposure Meter and Science Cameras
                WaitForReady.execute({})
                kpfexpose['OBJECT'].write(f'Grid search {xs[i]}, {ys[j]}')
                log.info(f"Starting kpfexpose cameras")
                StartExposure.execute({})
                # Begin timestamp for history retrieval
                begin = time.time()
                log.info('Starting guider Trigger file')
                initial_last_cube = kpfguide['LASTTRIGFILE'].read()
                StartTriggerFile.execute({})

                # Start FVC Exposures
                initial_lastfile = {}
                failedFVCs = []
                for FVC in ['SCI', 'CAHK', 'EXT']:
                    if FVC in FVCs:
                        initial_lastfile[FVC] = kpffvc[f"{FVC}LASTFILE"].read()
                        log.debug(f"  Initial lastfile for {FVC} = {initial_lastfile[FVC]}")
                        log.info(f"  Starting {FVC} FVC exposure")
                        try:
                            TakeFVCExposure.execute({'camera': FVC, 'wait': False})
                        except:
                            log.error('Starting FVC image failed')
                            failedFVCs.append(FVC)

                check_scriptstop()

                # Collect files for FVC exposures
                for FVC in ['SCI', 'CAHK', 'EXT']:
                    if FVC in FVCs and FVC not in failedFVCs:
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
                                   'x': xs[i], 'y': ys[j]}
                            images.add_row(row)

                check_scriptstop()

                # Here's where we wait for the remainder of the TimeOnPosition
                log.info(f"  Waiting for kpfexpose to be ready")
                WaitForReady.execute({})

                StopTriggerFile.execute({})
                WaitForTriggerFile.execute({'initial_lastfile': initial_last_cube})
                last_cube = kpfguide['LASTTRIGFILE'].read()
                row = {'file': last_cube, 'camera': 'CRED2',
                       'x': xs[i], 'y': ys[j]}
                images.add_row(row)

                # Stop Exposure Meter
                log.info(f"  Waiting for ExpMeter to be Ready")
                EMsuccess = ktl.waitFor('$kpf_expmeter.EXPSTATE == Ready', timeout=5)
                time.sleep(0.5) # Time shim because paranoia
                if EMsuccess is True:
                    lastfile = kpf_expmeter['FITSFILE'].read()
                else:
                    lastfile = 'failed'
                log.debug(f'  Done.  FITSFILE={lastfile}')
                row = {'file': lastfile, 'camera': 'ExpMeter',
                       'x': xs[i], 'y': ys[j]}
                images.add_row(row)
                if EMsuccess is True:
                    loutfile = kpf_expmeter['LOUTFILE'].read()
                else:
                    loutfile = 'failed'
                log.debug(f'  Done.  LOUTFILE={loutfile}')
                row = {'file': loutfile, 'camera': 'ExpMeter_1Dspec',
                       'x': xs[i], 'y': ys[j]}
                images.add_row(row)

                # Retrieve keyword history
                end = time.time()
                expmeter_data = {'x': xs[i], 'y': ys[j],
                                 'i': i, 'j': j,
                                 }
                log.info(f"  Retrieving keyword history")
                for counts_kw in ['CUR_COUNTS', 'RAW_COUNTS', 'BCK_COUNTS']:
                    log.debug(f"  Retrieving keyword history for {counts_kw}")
                    kws = {'kpf_expmeter': [counts_kw]}
                    counts_history = keygrabber.retrieve(kws, begin=begin, end=end)
                    # Extract counts and save to table (initial style output)
                    fluxes = np.zeros((len(counts_history)-2, 4))
                    for k,entry in enumerate(counts_history):
                        if k != 0 and k != len(counts_history)-1:
                            value_floats = [float(v) for v in entry['ascvalue'].split()]
                            ts = datetime.fromtimestamp(entry['time']).strftime('%Y-%m-%d %H:%M:%S')
                            log.debug(f"  {ts}: {value_floats}")
                            fluxes[k-1] = value_floats
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

        if grid == 'TipTilt':
            SetTipTiltTargetPixel.execute({'x': xpix0, 'y': ypix0})
        elif grid == 'SciADC':
            kpffiu['ADC1NAM'].write('Null')
            kpffiu['ADC2NAM'].write('Null')
#             kpffiu['ADCTRACK'].write('On')


    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
