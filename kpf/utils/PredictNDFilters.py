import argparse
import numpy as np

description = '''
    Estimates ND1 and ND2 filter OD level required to match target SNR

    Prints suggested OD filter based on available set in wheel:
    ND1: OD 0.1, OD 1.0, OD 1.3, OD 2.0, OD 3.0, OD 4.0
    ND2: OD 0.1, OD 0.3, OD 0.5, OD 0.8, OD 1.0, OD 4.0

    Parameters
    ----------
    snr_desired : :obj:`float`
        Minimum SNR desired for cal spectrum. Useful if you don't want to
        match the target flux, but rather hit a minimum required SNR in the
        specfied exposure time.
    
    exp_time : :obj:'float'
        Target exposure time in seconds.

    cal_source : :obj:'str'
        Calibration source being use [default = 'LFC']    

    Returns
    -------
    od : :obj:`float`
        Nominal OD value to match target star flux.

    ND1 : :obj:`float`
        Nearest OD setting to use for the first filter wheel to achieve total OD of 'od'
    
    ND2 : :obj:`float`
        Nearest OD setting to use for the second filter wheel to achieve total OD of 'od'
        
    SNR_expected : :obj:`float`
        Expected SNR that will be acquired in the cal spectrum based on actual combined OD of ND1 + ND2

    S Halverson - JPL - 29-Dec-2019 for NEID
    R Rubenzahl - Caltech - 26-Jan-2023 for KPF
    '''


def get_nd_to_use(snr_desired, exp_time, cal_source='LFCFiber'):
    nonlinear_limit_snr = 550.  # rough non-linearity limit for single exposure

    # **hardcoded values for scaling**
    # Using LFC spectrum from KP.20230124.59504.08.fits as a reference
    # in 60 seconds, LFC reaches 1e6 reduced photoelectrons in the 1D reduced (L1) file
    # Since that's a sum of three fibers, we divide by 3 for counts in a single trace 
    # The counts in the cal trace are roughly twice as high as the science traces
    # so we multiply by two get get an estimate of cal-trace counts for LFC
    # Numbers from example LFC spectrum at reddest order (peak # throughput) 
#     ref_flux_lfc = 1e6/3 * 2 # reduced photoelectrons 
#     ref_snr_lfc  = np.sqrt(ref_flux_lfc) 
#     ref_exp_time_lfc = 60. # seconds
    # This reference spectrum was taken using ND1=3.0 and ND2=0.1
#     ref_nd1 = 3.0
#     ref_nd2 = 0.1
#     ref_od = ref_nd1 + ref_nd2

    ref_flux = {'LFCFiber': 1e6/3 * 2, # reduced photoelectrons
                'EtalonFiber': None}[cal_source]
    ref_exp_time = {'LFCFiber': 60, # seconds
                    'EtalonFiber': None}[cal_source]
    ref_nd1 = {'LFCFiber': 3.0,
               'EtalonFiber': None}[cal_source]
    ref_nd2 = {'LFCFiber': 0.1,
               'EtalonFiber': None}[cal_source]
    ref_snr  = np.sqrt(ref_flux)
    ref_od = ref_nd1 + ref_nd2

    # Scale to zero attenuation
    nom_flux = ref_flux / 10**(-ref_od) 
    nom_snr  = np.sqrt(nom_flux)

    # KPF OD filter set
    nd1_filter_set = [0.1, 1.0, 1.3, 2.0, 3.0, 4.0]
    nd2_filter_set = [0.1, 0.3, 0.5, 0.8, 1.0, 4.0]
    nd_combos = {}
    for nd1 in nd1_filter_set:
        for nd2 in nd2_filter_set:
            od = nd1 + nd2
            if od in nd_combos:
                continue
            else:
                nd_combos[round(od,1)] = [nd1, nd2]
    ods_attainable = np.array(list(nd_combos.keys()))

    # Select which cal source to use
    cal_flux = nom_flux
    cal_snr  = nom_snr
    cal_exp_time = ref_exp_time
    flux_rate_cal = cal_flux / cal_exp_time

    # estimate nominal OD to reach SNR threshold in provided exposure time
    od_for_snr = -np.log10( (snr_desired/cal_snr)**2 * (cal_exp_time/exp_time) )
    
    # get nearest ND filter combination
    od_closest = ods_attainable[(np.abs(ods_attainable - od_for_snr)).argmin()]
    ND1, ND2 = nd_combos[od_closest]
    snr_exptime = (flux_rate_cal * exp_time * 10 ** (-od_closest)) ** 0.5

    if np.abs(10 ** (od_closest - od_for_snr)) > 2.:
       print('WARNING: Cal flux a factor of >2 off from nominal')

    print('')
    print('Nominal OD to achieve desired SNR:% 5.3f'%(od_for_snr))

    # warn if nominal filter to match flux is beyond bounds
    if od_closest > np.amax(ods_attainable):
        print('WARNING: beyond OD filter set max value')
    if od_closest < np.amin(ods_attainable):
        print('WARNING: below OD filter set min value')

    print('')
    print('Closest OD achievable: {}'.format(od_closest))
    print('    Set ND1 filter to: {}'.format(ND1))
    print('    Set ND2 filter to: {}'.format(ND2))
    print('')
    print('{} SNR (reddest) at closest OD filter setting in {} s is {:.1f}'.format(cal_source, exp_time, snr_exptime))

    # warn if etalon flux is approaching non-linearity
    if snr_exptime > nonlinear_limit_snr:
        print('WARNING: etalon SNR >% 3.1f' %nonlinear_limit_snr)

    return f"OD {ND1}", f"OD {ND2}"


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=description)
    p.add_argument('SNR', type=float,
                   help="The target SNR")
    p.add_argument('ExpTime', type=float,
                   help="The exposure time")
    args = p.parse_args()
    result = get_nd_to_use(args.SNR, args.ExpTime)
