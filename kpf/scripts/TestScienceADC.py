from pathlib import Path
import logging
from datetime import datetime
import time

import numpy as np
from astropy.table import Table, Row

import ktl
import keygrabber

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_as_script, check_scriptrun, check_script_stop
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
class TestScienceADC(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    @check_scriptrun
    def pre_condition(cls, args, logger, cfg):
        # Use file input for OB instead of args (temporary)
        check_input(args, 'OBfile')
        OBfile = Path(args.get('OBfile')).expanduser()
        if OBfile.exists() is True:
            OB = yaml.safe_load(open(OBfile, 'r'))
            log.warning(f"Using OB information from file {OBfile}")
        check_input(OB, 'Template_Name', allowed_values=['kpf_eng_testsciadc'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.3')
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
    @register_as_script(Path(__file__).name, os.getpid())
    def perform(cls, args, logger, cfg):
        OBfile = Path(args.get('OBfile')).expanduser()
        OB = yaml.safe_load(open(OBfile, 'r'))
        log.info('-------------------------')
        log.info(f"Running TestScienceADC OB")
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

        nx = args.get('nx')
        ny = args.get('ny')
        dx = args.get('dx')
        dy = args.get('dy')
        xis = [xi for xi in range(int(-nx/2),int((nx+1)/2),1)]
        yis = [yi for yi in range(int(-ny/2),int((ny+1)/2),1)]
        xs = [xi*dx for xi in xis]
        ys = [yi*dy for yi in yis]

        # Set up ADC
        kpffiu = ktl.cache('kpffiu')
        kpffiu['ADCTRACK'].write('Off')

        # Set up Exposure Meter
        if 'ExpMeter' in args.get('cameras', ''):
            # Set up kpfexpose
            kpfexpose = ktl.cache('kpfexpose')
            SetSourceSelectShutters.execute({'SSS_Science': True, 'SSS_Sky': True})
            SetTimedShutters.execute({'TimedShutter_Scrambler': True})
            SetTriggeredDetectors.execute({'TriggerExpMeter': True})

        # Set up FVCs
        kpffvc = ktl.cache('kpffvc')

        # Set up guider
        if 'CRED2' in args.get('cameras', ''):
            kpfguide = ktl.cache('kpfguide')

        for i,xi in enumerate(xis):
            for j,yi in enumerate(yis):
                # Offset to position
                nominalx, nominaly = kpffiu['ADCPRISMS'].read(binary=True)
                log.info(f"Offsetting to position ({xs[i]}, {ys[j]})")
                kpffiu['ADC1VAL'].write(nominalx + xs[i])
                kpffiu['ADC2VAL'].write(nominaly + ys[j])
                expr = '($kpffiu.ADC1STA == Ready) and ($kpffiu.ADC2STA == Ready)'
                success = ktl.waitFor(expr, timeout=2*max([dx*nx, dy*ny])/5)
                if success is not True:
                    ADC1STA = kpffiu['ADC1STA'].read()
                    ADC2STA = kpffiu['ADC2STA'].read()
                    msg = f'Timed out waiting for ADCs: ADC1STA={ADC1STA} ADC2STA={ADC2STA}'
                    raise KPFException(msg)

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

        # Send ADC back to nomimal
        kpffiu['ADCTRACK'].write('On')


    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['OBfile'] = {'type': str,
                                 'help': ('A YAML fortmatted file with the OB '
                                          'to be executed. Will override OB '
                                          'data delivered as args.')}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
