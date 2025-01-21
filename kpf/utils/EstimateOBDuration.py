from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock

from kpf.calbench import standardize_lamp_name


def estimate_calibration_time(calibrations, cfg, fast=False):
    duration = 0
    fast_str = '' if fast is False else '_fast'
    readout_red = 0 if OB['TriggerRed'] == False else\
                  cfg.getfloat('time_estimates', f'readout_red{fast_str}', fallback=60)
    readout_green = 0 if OB['TriggerGreen'] == False else\
                    cfg.getfloat('time_estimates', f'readout_green{fast_str}', fallback=60)
    readout_cahk = 0 if OB['TriggerCaHK'] == False else\
                   cfg.getfloat('time_estimates', 'readout_cahk', fallback=1)
    readout = max([readout_red, readout_green, readout_cahk])

    # ConfigureForCalibrations
    lamps = set([cal.get('CalSource') for cal in calibrations
                 if cal.get('CalSource') not in ['Home', 'Dark']])
    for lamp in lamps:
        if lamp in ['Th_daily', 'Th_gold', 'U_daily', 'U_gold',
                    'BrdbandFiber', 'WideFlat']:
            duration += cfg.getfloat('time_estimates', 'power_on_cal_lamp',
                                fallback=1)
        if lamp == 'LFCFiber':
            duration += cfg.getfloat('time_estimates', 'LFC_to_AstroComb',
                                fallback=30)
    # Configure FIU
    duration += cfg.getfloat('time_estimates', 'FIU_mode_change',
                        fallback=20)
    # Execute Calibrations
    lamps_that_need_warmup = ['FF_FIBER', 'BRDBANDFIBER', 'TH_DAILY',
                              'TH_GOLD', 'U_DAILY', 'U_GOLD']
    for cal in calibrations:
        lamp = standardize_lamp_name(cal.get('CalSource'))
        # Move Octagon
        duration += cfg.getfloat('time_estimates', 'octagon_move',
                            fallback=60)
        if cal.get('CalSource') in ['Dark', 'Home']:
            duration += int(cal['nExp'])*float(cal['ExpTime'])
            duration += int(cal['nExp'])*readout

        elif lamp in lamps_that_need_warmup:
            # Add warm up time
            try:
                import ktl
                warm_up = kpflamps[f'{lamp}_THRESHOLD'].read(binary=True)
            except:
                warm_up = cfg.getfloat('time_estimates', 'lamp_warmup',
                                  fallback=1800)
            if duration < warm_up:
                warm_up_wait = warm_up-duration
                print(f"  {lamp} warm up {warm_up_wait/60:.0f} min")
                duration += warm_up_wait
            lamps_that_need_warmup.pop(lamps_that_need_warmup.index(lamp))
        
        duration += int(cal.get('nExp'))*float(cal.get('ExpTime'))
        duration += int(cal.get('nExp'))*readout

    return duration


def estimate_observation_time(observations, cfg, fast=False):
    duration = 0
    fast_str = '' if fast is False else '_fast'
    readout_red = 0 if OB['TriggerRed'] == False else\
                  cfg.getfloat('time_estimates', f'readout_red{fast_str}', fallback=60)
    readout_green = 0 if OB['TriggerGreen'] == False else\
                    cfg.getfloat('time_estimates', f'readout_green{fast_str}', fallback=60)
    readout_cahk = 0 if OB['TriggerCaHK'] == False else\
                   cfg.getfloat('time_estimates', 'readout_cahk', fallback=1)
    readout = max([readout_red, readout_green, readout_cahk])

    # Configure FIU
    duration += cfg.getfloat('time_estimates', 'FIU_mode_change',
                             fallback=20)
    # Slew
    duration += cfg.getfloat('time_estimates', 'slew_time',
                         fallback=120)
    # Acquire
    duration += cfg.getfloat('time_estimates', 'acquire_time',
                        fallback=10)
    # Close Tip Tilt Loops
    duration += cfg.getfloat('time_estimates', 'tip_tilt_loop_closure',
                        fallback=3)
    # Execute Observations
    for observation in observations:
        duration += observation['nExp']*observation['ExpTime']
        duration += observation['nExp']*readout

    return duration



##-----------------------------------------------------------------------------
## EstimateOBDuration
##-----------------------------------------------------------------------------
class EstimateOBDuration(KPFTranslatorFunction):
    '''Estimate the duration of the input OB.

    This script will determine the OB type (science or calibration) and invoke
    either `EstimateCalOBDuration` or `EstimateSciOBDuration`

    ARGS:
    =====
    :OB: `dict` A fully specified observing block (OB).
    '''
    @classmethod
    def pre_condition(cls, OB):
        pass

    @classmethod
    def perform(cls, OB):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info('-------------------------')
        OB = ObservingBlock(OB)
        cfg = cls._load_config()
        duration = 0

        if len(OB.Calibrations) > 0:
            duration += estimate_calibration_time(OB.Calibrations, cfg, fast=False)

        if len(OB.Observations) > 0:
            duration += estimate_observation_time(OB.Observations, cfg, fast=False)

        print(f"{duration/60:.0f} min")
        return duration

    @classmethod
    def post_condition(cls, OB):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('--fast', '--fastread',
                            dest="fast",
                            default=False, action="store_true",
                            help='Use fast readout mode times for estimate?')
        return super().add_cmdline_args(parser)


