from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.calbench import standardize_lamp_name


##-----------------------------------------------------------------------------
## EstimateOBDuration
##-----------------------------------------------------------------------------
class EstimateOBDuration(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, OB, logger, cfg):
        pass

    @classmethod
    def perform(cls, OB, logger, cfg):
        if OB['Template_Name'] == 'kpf_cal':
            return EstimateCalOBDuration.execute(OB)
        elif OB['Template_Name'] == 'kpf_sci':
            return EstimateSciOBDuration.execute(OB)
        else:
            print(f"Time estimate not supported for {OB['Template_Name']} type")

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('--fast', '--fastread',
                            dest="fast",
                            default=False, action="store_true",
                            help='Use fast readout mode times for estimate?')
        return super().add_cmdline_args(parser, cfg)


##-----------------------------------------------------------------------------
## EstimateCalOBDuration
##-----------------------------------------------------------------------------
class EstimateCalOBDuration(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_cal'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')

    @classmethod
    def perform(cls, OB, logger, cfg):
        fast = '' if OB.get('fast', False) is False else '_fast'

        duration = 0
        readout_red = 0 if OB['TriggerRed'] == False else\
                      cfg.getfloat('time_estimates', f'readout_red{fast}', fallback=60)
        readout_green = 0 if OB['TriggerGreen'] == False else\
                        cfg.getfloat('time_estimates', f'readout_green{fast}', fallback=60)
        readout_cahk = 0 if OB['TriggerCaHK'] == False else\
                       cfg.getfloat('time_estimates', 'readout_cahk', fallback=1)
        readout = max([readout_red, readout_green, readout_cahk])

        # ConfigureForCalibrations
        sequence = OB.get('SEQ_Calibrations', [])
        if len(sequence) > 0:
            lamps = set([x['CalSource'] for x in sequence if x['CalSource'] != 'Home'])
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

        # Execute Darks
        darks = OB.get('SEQ_Darks', [])
        if len(darks) > 0:
            # Set Octagon to Home
            duration += cfg.getfloat('time_estimates', 'octagon_move',
                                fallback=60)
        for dark in darks:
            duration += int(dark['nExp'])*float(dark['ExpTime'])
            duration += int(dark['nExp'])*readout

        # Execute Cals
        cals = OB.get('SEQ_Calibrations', [])
        archon_time_shim = cfg.getfloat('times', 'archon_temperature_time_shim',
                             fallback=2)
        lamps_that_need_warmup = ['FF_FIBER', 'BRDBANDFIBER', 'TH_DAILY',
                                  'TH_GOLD', 'U_DAILY', 'U_GOLD']
        for cal in cals:
            duration += cfg.getfloat('time_estimates', 'octagon_move',
                                fallback=60)
            lamp = standardize_lamp_name(cal.get('CalSource'))
            if lamp in lamps_that_need_warmup:
                # Set duration to warm up time
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
            duration += int(cal['nExp'])*max([float(cal['ExpTime']), archon_time_shim])
            duration += int(cal['nExp'])*readout

        print(f"{duration/60:.0f} min")
        return duration

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass


##-----------------------------------------------------------------------------
## EstimateSciOBDuration
##-----------------------------------------------------------------------------
class EstimateSciOBDuration(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')

    @classmethod
    def perform(cls, OB, logger, cfg):
        fast = '' if OB.get('fast', False) is False else '_fast'

        readout_red = 0 if OB['TriggerRed'] == False else\
                      cfg.getfloat('time_estimates', f'readout_red{fast}', fallback=60)
        readout_green = 0 if OB['TriggerGreen'] == False else\
                        cfg.getfloat('time_estimates', f'readout_green{fast}', fallback=60)
        readout_cahk = 0 if OB['TriggerCaHK'] == False else\
                       cfg.getfloat('time_estimates', 'readout_cahk', fallback=1)
        readout = max([readout_red, readout_green, readout_cahk])

        # Configure FIU
        FIU_mode_change = cfg.getfloat('time_estimates', 'FIU_mode_change',
                                  fallback=20)
        # Slew
        slew_time = cfg.getfloat('time_estimates', 'slew_time',
                             fallback=120)

        duration = max([FIU_mode_change, slew_time])

        # Acquire
        duration += cfg.getfloat('time_estimates', 'acquire_time',
                            fallback=10)
        # Close Tip Tilt Loops
        duration += cfg.getfloat('time_estimates', 'tip_tilt_loop_closure',
                            fallback=3)
        # Execute Observations
        observations = OB.get('SEQ_Observations', [])
        for observation in observations:
            duration += observation['nExp']*observation['ExpTime']
            duration += observation['nExp']*readout

        print(f"{duration/60:.0f} min")
        return duration

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass
