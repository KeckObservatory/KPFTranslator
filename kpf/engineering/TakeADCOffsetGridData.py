from pathlib import Path
import os
from datetime import datetime, timedelta
import time
from astropy.table import Table

import ktl

import numpy as np
from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input, ScriptStopTriggered)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.fvc.TakeFVCExposure import TakeFVCExposure
from kpf.fiu.SetADCOffsets import SetADCOffsets

class TakeADCOffsetGridData(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, OB, logger, cfg):
        pass

    @classmethod
    @register_script(Path(__file__).name, os.getpid())
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for key in args:
            log.debug(f"  {key}: {args[key]}")
        log.info('-------------------------')

        adc1delta = args.get('ADC1DELTA', 5)
        adc2delta = args.get('ADC2DELTA', 5)
        adcstep = args.get('ADCSTEP', 1)
        adc1deltas = np.arange(-adc1delta, adc1delta, adcstep)
        adc2deltas = np.arange(-adc2delta, adc2delta, adcstep)

        fvcsleeptime = 0.25

        ADCPRISMS = ktl.cache('kpffiu', 'ADCPRISMS')
        ADCPRISMS.monitor()
        ADC1VAL = ktl.cache('kpffiu', 'ADC1VAL')
        ADC1VAL.monitor()
        ADC2VAL = ktl.cache('kpffiu', 'ADC2VAL')
        ADC2VAL.monitor()
        LASTFILE = ktl.cache('kpffvc', 'EXTLASTFILE')
        LASTFILE.monitor()

        this_file_name = Path(__file__).name.replace('.py', '')
        utnow = datetime.utcnow()
        now_str = utnow.strftime('%Y%m%dat%H%M%S')
        date_str = (utnow-timedelta(days=1)).strftime('%Y%b%d').lower()
        log_path = Path(f'/s/sdata1701/KPFTranslator_logs/{date_str}')
        images_file = log_path / Path(f'{this_file_name}_{now_str}.txt')
        images = Table(names=('file', 'ADC1VAL', 'ADC2VAL'),
                       dtype=('a90',  'f4', 'f4'))

        for i,delta1 in enumerate(adc1deltas):
            for j,delta2 in enumerate(adc2deltas):
                log.info(f'Moving ADC1 to {adc1:.1f}, ADC2 to {adc2:.1f}')
                SetADCOffsets.execute({'ADC1OFF': delta1, 'ADC2OFF': delta2})
                log.info('Taking EXT FVC exposure')
                TakeFVCExposure.execute({'camera': 'EXT'})
                time.sleep(fvcsleeptime)
                row = {'file': str(LASTFILE),
                       'DELTA1': delta1,
                       'DELTA2': delta2,
                       'ADC1VAL': str(ADC1VAL),
                       'ADC2VAL': str(ADC2VAL)}
                log.info(f'  {row["file"]}')
                images.add_row(row)
                if images_file.exists():
                    images_file.unlink()
                images.write(images_file, format='ascii.csv')
        log.info('Done')


    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('ADC1DELTA', type=float,
                            help="Maximum ADC1 offset from nominal")
        parser.add_argument('ADC2DELTA', type=float,
                            help="Maximum ADC2 offset from nominal")
        parser.add_argument('ADCSTEP', type=float,
                            help="Anglular step size")
        return super().add_cmdline_args(parser, cfg)
