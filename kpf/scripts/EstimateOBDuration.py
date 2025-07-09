import numpy as np

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.calbench import standardize_lamp_name


def get_readout_time(sequences, cfg, fast=False):
    trigger_red = np.any([seq.get('TriggerRed') for seq in sequences])
    trigger_green = np.any([seq.get('TriggerGreen') for seq in sequences])
    trigger_cahk = np.any([seq.get('TriggerCaHK') for seq in sequences])
    fast_str = '' if fast is False else '_fast'
    readouts = [cfg.getfloat('time_estimates', f'readout_red{fast_str}', fallback=60) if trigger_red else 0,
                cfg.getfloat('time_estimates', f'readout_green{fast_str}', fallback=60) if trigger_green else 0,
                cfg.getfloat('time_estimates', f'readout_cahk', fallback=1) if trigger_cahk else 0]
    return max(readouts)


def estimate_calibration_time(calibrations, cfg, fast=False):
    duration = 0
    readout = get_readout_time(calibrations, cfg, fast=fast)

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
        if lamp in lamps_that_need_warmup:
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
        duration += int(cal.get('nExp'))*(float(cal.get('ExpTime'))+readout)

    return duration


def estimate_observation_time(observations, cfg, fast=False):
    duration = 0
    readout = get_readout_time(observations, cfg, fast=fast)

    # Configure FIU
    duration += cfg.getfloat('time_estimates', 'FIU_mode_change', fallback=20)
    # Slew
    duration += cfg.getfloat('time_estimates', 'slew_time', fallback=120)
    # Acquire
    duration += cfg.getfloat('time_estimates', 'acquire_time', fallback=10)
    # Close Tip Tilt Loops
    duration += cfg.getfloat('time_estimates', 'tip_tilt_loop_closure', fallback=3)
    # Execute Observations
    for obs in observations:
        duration += obs.get('nExp')*(obs.get('ExpTime')+readout)

    return duration



##-----------------------------------------------------------------------------
## EstimateOBDuration
##-----------------------------------------------------------------------------
class EstimateOBDuration(KPFScript):
    '''Estimate the duration of the input OB. Uses estimates of instrument
    configuration time, slew time, acquire time, and readout time and combines
    those with the information in the observing block to estimate how long it
    will take to execute the observing block.

    ARGS:
    =====
    :fast: `bool` Estimate the duration assuming fast read mode?
    :OB: `dict` or `ObservingBlock` A fully specified observing block (OB).
    '''
    @classmethod
    def pre_condition(cls, args, OB=None):
        pass

    @classmethod
    def perform(cls, args, OB=None):
        if OB is not None and type(OB) != ObservingBlock:
            OB = ObservingBlock(OB)
        fast = args.get('fast', False)
        duration = 0

        if OB.Calibrations is not None:
            duration += estimate_calibration_time(OB.Calibrations, cfg, fast=fast)

        if OB.Observations is not None:
            duration += estimate_observation_time(OB.Observations, cfg, fast=fast)

        print(f"{duration/60:.0f} min")
        return duration/60

    @classmethod
    def post_condition(cls, args, OB=None):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('--fast', '--fastread',
                            dest="fast",
                            default=False, action="store_true",
                            help='Use fast readout mode times for estimate?')
        return super().add_cmdline_args(parser)


