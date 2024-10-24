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


class TakeADCGridData(KPFTranslatorFunction):
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

        adc1min = args.get('ADC1MIN', 60)
        adc1max = args.get('ADC1MAX', 70)
        adc2min = args.get('ADC2MIN', 60)
        adc2max = args.get('ADC2MAX', 70)
        adcstep = args.get('ADCSTEP', 1)
        adc1vals = np.arange(adc1min, adc1max+adcstep, adcstep)
        adc2vals = np.arange(adc2min, adc2max+adcstep, adcstep)

        adcsleeptime = 1
        fvcsleeptime = 0.25

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

        for i,adc1 in enumerate(adc1vals):
            for j,adc2 in enumerate(adc2vals):
                log.info(f'Moving ADC1 to {adc1:.1f}, ADC2 to {adc2:.1f}')
                ADC1VAL.write(f"{adc1:.1f}")
                ADC2VAL.write(f"{adc2:.1f}")
                time.sleep(adcsleeptime)
                log.info('Taking EXT FVC exposure')
                TakeFVCExposure.execute({'camera': 'EXT'})
                time.sleep(fvcsleeptime)
                row = {'file': str(LASTFILE),
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
        parser.add_argument('ADC1MIN', type=float,
                            help="Starting ADC1 angle")
        parser.add_argument('ADC1MAX', type=float,
                            help="Ending ADC1 angle")
        parser.add_argument('ADC2MIN', type=float,
                            help="Starting ADC2 angle")
        parser.add_argument('ADC2MAX', type=float,
                            help="Ending ADC2 angle")
        parser.add_argument('ADCSTEP', type=float,
                            help="Anglular step size")
        return super().add_cmdline_args(parser, cfg)
