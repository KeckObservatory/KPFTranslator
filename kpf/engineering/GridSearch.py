import time
import os
from pathlib import Path
import logging
from datetime import datetime, timedelta
import time
import subprocess

import numpy as np
from astropy.table import Table, Row

import ktl
import keygrabber

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.fiu.SetTipTiltTargetPixel import SetTipTiltTargetPixel
from kpf.fiu.StartTipTilt import StartTipTilt
from kpf.fiu.StopTipTilt import StopTipTilt
from kpf.fvc.TakeFVCExposure import TakeFVCExposure
from kpf.fvc.SetFVCExpTime import SetFVCExpTime
from kpf.guider.StartTriggerFile import StartTriggerFile
from kpf.guider.StopTriggerFile import StopTriggerFile
from kpf.guider.WaitForTriggerFile import WaitForTriggerFile
from kpf.spectrograph.SetExpTime import SetExpTime
from kpf.spectrograph.StartExposure import StartExposure
from kpf.spectrograph.WaitForReady import WaitForReady
from kpf.spectrograph.WaitForReadout import WaitForReadout
from kpf.spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from kpf.spectrograph.SetTimedShutters import SetTimedShutters
from kpf.spectrograph.SetTriggeredDetectors import SetTriggeredDetectors


##-------------------------------------------------------------------------
## fiber_grid_search
##-------------------------------------------------------------------------
class GridSearch(KPFTranslatorFunction):
    '''Executes an engineering grid search OB.

    This must have arguments as input, either from a file using the `-f` command
    line tool, or passed in from the execution engine.

    ARGS:
    =====
    None
    '''
    abortable = True

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

    @classmethod
    @register_script(Path(__file__).name, os.getpid())
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for key in OB:
            log.debug(f"  {key}: {OB[key]}")
        log.info('-------------------------')

        grid = OB.get('Grid')

        this_file_name = Path(__file__).name.replace('.py', '')
        utnow = datetime.utcnow()
        now_str = utnow.strftime('%Y%m%dat%H%M%S')
        date_str = (utnow-timedelta(days=1)).strftime('%Y%b%d').lower()
        log_path = Path(f'/s/sdata1701/KPFTranslator_logs/{date_str}')
        images_file = log_path / Path(f'{grid}{this_file_name}_images_{now_str}.txt')
        fluxes_file = log_path / Path(f'{grid}{this_file_name}_fluxes_{now_str}.txt')

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
        xindicies = [ind for ind in range(nx)]
        yindicies = [ind for ind in range(ny)]
        xs = [xi*dx for xi in xis]
        ys = [yi*dy for yi in yis]

        # Set up guider (assume parameters set during acquisition of star)
        kpfguide = ktl.cache('kpfguide')
        log.info('Setting TRIGCUBE Inactive')
        kpfguide['TRIGCUBE'].write('Inactive')
        if grid == 'TipTilt':
            log.info(f"DAR_ENABLE = {kpfguide['DAR_ENABLE'].read()}")
            dar_offset = kpfguide['DAR_OFFSET'].read(binary=True)
            log.info(f"DAR_OFFSET = {dar_offset[0]:.2f} {dar_offset[1]:.2f}")
            xpix0, ypix0 = kpfguide['PIX_TARGET'].read(binary=True)
            log.info(f"PIX_TARGET is {xpix0:.2f}, {ypix0:.2f}")
            basex, basey = kpfguide['CURRENT_BASE'].read(binary=True)
            log.info(f"CURRENT_BASE is {basex:.2f}, {basey:.2f}")
            # Pixel targets must be in absolute coordinates
            xs = [basex+xpix for xpix in xs]
            ys = [basey+ypix for ypix in ys]
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
        OB['TimedShutter_Scrambler'] = True
        OB['TimedShutter_CaHK'] = OB.get('TriggerCaHK', False)
        SetTimedShutters.execute(OB)
        SetTriggeredDetectors.execute(OB)
        total_exptime = OB.get('TimeOnPosition')
        SetExpTime.execute({'ExpTime': total_exptime})

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
                log.info(f"Setting {FVC} FVC ExpTime = {exptime:.2f} s")
                SetFVCExpTime.execute({'camera': FVC, 'exptime': exptime})

        for i in xindicies:
            yindicies.reverse()
            for j in yindicies:
                check_scriptstop()

                if grid == 'TipTilt':
                    ##------------------------------------------------------
                    ## Tip Tilt
                    ##------------------------------------------------------
                    log.info(f"Adjusting CURRENT_BASE to ({xs[i]:.2f}, {ys[j]:.2f}) ({xis[i]}, {yis[j]})")
                    max_move = 3
                    precisison = 0.01
                    current_base = ktl.cache('kpfguide', 'CURRENT_BASE')
                    current_cb = current_base.read(binary=True)
                    delta_cb = (xs[i]-current_cb[0], ys[j]-current_cb[1])
                    while abs(delta_cb[0]) > precisison or abs(delta_cb[1]) > precisison:
                        # Calc X move
                        new_X_target = current_cb[0]
                        if abs(delta_cb[0]) > precisison:
                            move_sign_X = delta_cb[0]/abs(delta_cb[0])
                            move_mag_X = min([max_move, abs(delta_cb[0])])
                            new_X_target += move_sign_X*move_mag_X
                        # Calc Y move
                        new_Y_target = current_cb[1]
                        if abs(delta_cb[1]) > precisison:
                            move_sign_Y = delta_cb[1]/abs(delta_cb[1])
                            move_mag_Y = min([max_move, abs(delta_cb[1])])
                            new_Y_target += move_sign_Y*move_mag_Y
                        log.info(f"  Setting CURRENT_BASE to {new_X_target:.2f}, {new_Y_target:.2f}")
                        SetTipTiltTargetPixel.execute({'x': new_X_target,
                                                       'y': new_Y_target})
                        success = ktl.waitFor("$kpfguide.TIPTILT_PHASE == 'Tracking'", timeout=5)
                        current_cb = current_base.read(binary=True)
                        delta_cb = (xs[i]-current_cb[0], ys[j]-current_cb[1])
                    xpix, ypix = kpfguide['PIX_TARGET'].read(binary=True)
                    log.info(f"PIX_TARGET is {xpix:.2f}, {ypix:.2f}")
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
                                raise KPFException('Lost Star')
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

                WaitForReady.execute({})
                check_scriptstop() # Stop here if requested

                # Start Exposure Meter and Science Cameras
                kpfexpose['OBJECT'].write(f'Grid search {xs[i]}, {ys[j]}')
                log.info(f"Starting kpfexpose cameras")
                StartExposure.execute({})
                # Begin timestamp for history retrieval
                begin = time.time()
                # Take CRED2 image
                if OB.get('UseCRED2', True) is True:
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

                # Collect CRED2 File
                if OB.get('UseCRED2', True) is True:
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
            SetTipTiltTargetPixel.execute({'x': basex, 'y': basey})
            StopTipTilt.execute({})
        elif grid == 'SciADC':
            kpffiu['ADC1NAM'].write('Null')
            kpffiu['ADC2NAM'].write('Null')
#             kpffiu['ADCTRACK'].write('On')


    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
