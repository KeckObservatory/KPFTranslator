import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


##-------------------------------------------------------------------------
## RecoverThermalControl
##-------------------------------------------------------------------------
class RecoverThermalControl(KPFFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        service = args.get('service', None)
        location = args.get('location', None)

        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info(f"  service = {service}")
        log.info(f"  location = {location}")
        log.info('-------------------------')
        if not service or not location:
            log.error('Must provide service and location')
            return
        VAL = ktl.cache(service, f'{location}VAL')
        VAL.monitor()
        MOD = ktl.cache(service, f'{location}MOD')
        RMP = ktl.cache(service, f'{location}RMP')
        RMO = ktl.cache(service, f'{location}RMO')
        RMP = ktl.cache(service, f'{location}RMP')
        RNG = ktl.cache(service, f'{location}RNG')
        TRG = ktl.cache(service, f'{location}TRG')
        TRG.monitor()
        OUT = ktl.cache(service, f'{location}OUT')
        OUT.monitor()

        if RNG.read() != 'Off':
            log.warning('Thermal control is active, no recovery process to run')
            return
        if MOD.read() != 'Closed loop PID':
            log.warning('Thermal control is not in "Closed loop PID" mode')
            return

        # First change the setpoint to match the current temperature value.
        # This ensures that there are no sudden changes to the output.
        # The ramp (RMO) will turn off for this change within the dispatcher.
        log.info(f'{location}TRG = {float(VAL):.3f}')
        TRG.write(float(VAL))

        # Check that TRG and VAL are similar
        tol = cfg.getfloat('tolerances', 'TRG_VAL_diff_tolerance', fallback=0.01)
        if abs(TRG - VAL) > tol:
            log.warning('VAL and TRG are offset')
            log.warning(f'{location}TRG = {float(TRG):.3f}')
            log.warning(f'{location}VAL = {float(VAL):.3f}')
            return

        # Set RMP
        ramp_rate = cfg.getfloat('thermal_control', f'{location}RMP', fallback=1.0)
        log.info(f'{location}RMP = {ramp_rate}')
        RMP.write(ramp_rate)

        # Set RNG
        range_string = cfg.get('thermal_control', f'{location}RNG', fallback='Medium')
        log.info(f'{location}RNG = {range_string}')
        RNG.write(range_string)

        # Check that output is low
        if OUT > 5:
            log.warning(f'Output higher than expected. {location}OUT = {float(OUT):.1f}')

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('service', type=str,
                            choices=['kpfred', 'kpfgreen', 'kpfmet'],
                            help='Which keyword service?')
        parser.add_argument('location', type=str,
                            help='Which location (the basename of the keyword set)?')
        parser.add_argument("--nowait", dest="wait",
                            default=True, action="store_false",
                            help="Send move and return immediately?")
        return super().add_cmdline_args(parser)

