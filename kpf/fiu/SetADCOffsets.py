import ktl
import time

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetADCOffsets(KPFFunction):
    '''Quick and dirty code to manually set ADC angles to prescribed offsets
    from nominal based on the telescope position.

    Args:
        ADC1OFF (float): Offset for ADC1 (in degrees).
        ADC2OFF (float): Offset for ADC2 (in degrees).

    KTL Keywords Used:

    - `kpffiu.ADC1VAL`
    - `kpffiu.ADC2VAL`
    - `kpffiu.ADCTRACK`
    - `kpffiu.ADCPRISMS`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        kpffiu = ktl.cache('kpffiu')
        if kpffiu['ADCTRACK'].read() == 'On':
            log.info(f'Setting ADCTRACK to Off')
            kpffiu['ADCTRACK'].write('Off')
            time.sleep(1)
        ADC1_nominal, ADC2_nominal = kpffiu['ADCPRISMS'].read(binary=True)
        ADC1 = ADC1_nominal + args.get('ADC1OFF')
        ADC2 = ADC2_nominal + args.get('ADC2OFF')
        log.info(f"Setting ADC to offset angles: ADC1VAL={ADC1:.1f}, ADC2VAL={ADC2:.1f}")
        kpffiu['ADC1VAL'].write(ADC1)
        kpffiu['ADC2VAL'].write(ADC2)

    @classmethod
    def post_condition(cls, args):
        kpffiu = ktl.cache('kpffiu')
        tol = 0.1
        ADC1_nominal, ADC2_nominal = kpffiu['ADCPRISMS'].read(binary=True)
        adc1targ = ADC1_nominal + args.get('ADC1OFF')
        adc2targ = ADC2_nominal + args.get('ADC2OFF')
        expr = (f"($kpffiu.ADC1VAL > {adc1targ-tol}) "
                f"and ($kpffiu.ADC1VAL < {adc1targ+tol}) "
                f"and ($kpffiu.ADC2VAL > {adc2targ-tol}) "
                f"and ($kpffiu.ADC2VAL < {adc2targ+tol})")
        success = ktl.waitFor(expr, timeout=20)
        if success is False:
            raise FailedPostCondition('ADC Prisms did not reach destination angles')

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('ADC1OFF', type=float,
                            help="Offset for ADC1 (in degrees)")
        parser.add_argument('ADC2OFF', type=float,
                            help="Offset for ADC2 (in degrees)")
        return super().add_cmdline_args(parser)
