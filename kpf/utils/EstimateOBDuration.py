from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
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
        return True

    @classmethod
    def perform(cls, OB, logger, cfg):
        if OB['Template_Name'] == 'kpf_cal':
            duration = EstimateCalOBDuration.execute(OB)
        elif OB['Template_Name'] == 'kpf_sci':
            duration = EstimateSciOBDuration.execute(OB)
        print(f"{duration:.0f} s ({duration/60:.1f} min)")
        return duration

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass


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
        return True

    @classmethod
    def perform(cls, OB, logger, cfg):
        duration = 0
        readout_red = 0 if OB['TriggerRed'] == False else\
                      cfg.get('time_estimates', 'readout_red', fallback=60)
        readout_green = 0 if OB['TriggerGreen'] == False else\
                        cfg.get('time_estimates', 'readout_green', fallback=60)
        readout_cahk = 0 if OB['TriggerCaHK'] == False else\
                       cfg.get('time_estimates', 'readout_cahk', fallback=1)
        readout = max([readout_red, readout_green, readout_cahk])

        # ConfigureForCalibrations
        sequence = OB.get('SEQ_Calibrations')
        lamps = set([x['CalSource'] for x in sequence if x['CalSource'] != 'Home'])
        for lamp in lamps:
            if lamp in ['Th_daily', 'Th_gold', 'U_daily', 'U_gold',
                        'BrdbandFiber', 'WideFlat']:
                duration += cfg.get('time_estimates', 'power_on_cal_lamp',
                                    fallback=1)
            if lamp == 'LFCFiber':
                duration += cfg.get('time_estimates', 'LFC_to_AstroComb',
                                    fallback=30)
        # Configure FIU
        duration += cfg.get('time_estimates', 'FIU_mode_change',
                            fallback=20)

        # Execute Darks
#         print(f"{duration:.0f} s ({duration/60:.1f} min)")
        darks = OB.get('SEQ_Darks', [])
        if len(darks) > 0:
            # Set Octagon to Home
            duration += cfg.get('time_estimates', 'octagon_move',
                                fallback=60)
        for dark in darks:
            duration += dark['nExp']*dark['ExpTime']
            duration += dark['nExp']*readout
#             print(f"  {duration:.0f} s ({duration/60:.1f} min)")

        # Execute Cals
#         print(f"{duration:.0f} s ({duration/60:.1f} min)")
        cals = OB.get('SEQ_Calibrations', [])
        archon_time_shim = cfg.get('times', 'archon_temperature_time_shim',
                             fallback=2)
        lamps_that_need_warmup = ['FF_FIBER', 'BRDBANDFIBER', 'TH_DAILY',
                                  'TH_GOLD', 'U_DAILY', 'U_GOLD']
        for cal in cals:
            duration += cfg.get('time_estimates', 'octagon_move',
                                fallback=60)
            lamp = standardize_lamp_name(cal.get('CalSource'))
            if lamp in lamps_that_need_warmup:
                # Set duration to warm up time
                try:
                    import ktl
                    warm_up = kpflamps[f'{lamp}_THRESHOLD'].read(binary=True)
                except:
                    warm_up = cfg.get('time_estimates', 'lamp_warmup',
                                      fallback=1800)
                if duration < warm_up:
                    duration += (warm_up-duration)
                lamps_that_need_warmup.pop(lamps_that_need_warmup.index(lamp))
#                 print(f"{lamp} warm up {duration:.0f} s ({duration/60:.1f} min)")
            duration += cal['nExp']*cal['ExpTime']
            duration += cal['nExp']*readout
#             print(f"  {duration:.0f} s ({duration/60:.1f} min)")

        print(f"{duration:.0f} s ({duration/60:.1f} min)")
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
        return True

    @classmethod
    def perform(cls, OB, logger, cfg):
        duration = 0
        readout_red = cfg.get('time_estimates', 'readout_red', fallback=60)
        readout_green = cfg.get('time_estimates', 'readout_green', fallback=60)
        readout = max([readout_red, readout_green])

        # Configure FIU
        duration += cfg.get('time_estimates', 'FIU_mode_change',
                            fallback=20)
        # Slew
        duration += cfg.get('time_estimates', 'slew_time',
                            fallback=120)
        # Acquire
        duration += cfg.get('time_estimates', 'acquire_time',
                            fallback=10)
        # Close Tip Tilt Loops
        duration += cfg.get('time_estimates', 'tip_tilt_loop_closure',
                            fallback=3)
        # Execute Observations
        observations = OB.get('SEQ_Observations', [])
        for observation in observations:
            duration += observation['nExp']*observation['ExpTime']
            duration += observation['nExp']*readout

        print(f"{duration:.0f} s ({duration/60:.1f} min)")
        return duration

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass