from pathlib import Path
import datetime
import numpy as np
from astropy.io import fits
from astropy.modeling import models
from astropy import units as u
from astropy.table import Table
import matplotlib.pyplot as plt

import ktl

from kpf_etc.etc import kpf_photon_noise_estimate, _findel

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.calbench.SetND import SetND


## ------------------------------
## Function from Sam Halversion
## ------------------------------
# function to get all possible additions of two arrays
def all_possible_sums_with_indices_sorted(arr1, arr2):
    sums_and_indices = []
    for a in arr1:
        for b in arr2:
            sums_and_indices.append((a + b, a,b))
    
    # Sort by the sums
    sums_and_indices.sort()

    # Separate the sums and indices into two lists
    sorted_sums = [x[0] for x in sums_and_indices]
    sorted_indices = [(x[1], x[2]) for x in sums_and_indices]

    return sorted_sums, sorted_indices


## ------------------------------
## Function from Sam Halversion
## ------------------------------
# function to derive etalon OD setting
def get_simulcal_od(vmag, teff, exp_time, cal_fits, ref_wave=None,
                    od_values=[0.2,1.0,1.3,2.0,3.0,4.0],
                    filter_configs=[(0,0),(0,1),(0,2),(0,3),(0,4),(0,5)],
                    plot=False):
    '''
    Function to compute nominal ND filter settings for KPF simultaneous
    calibration source for a given stellar target
    Note that target and exposure parameters must fall within the 
    bounds of the KPF exposure time calculator:

    - Teff: 2700 - 6600 Kelvin
    - Vmag: 2 - 19
    - Texp: 10 - 3600 seconds

    Parameters
    ----------
    vmag : float
        V-magnitude of target. 

    teff : float
        Target effective temperature [K]

    ref_wave : float
        Reference wavelength at which the calibration source
        and stellar flux rates should be matched [Angstrom].
        (default is None)

        If no wavelength is provided, the wavelength chosen
        will be the flux-averaged stellar wavelength computed
        by the KPF exposure time calculator

    od_values : array
        Array of all of possible ND filter combinations.

    filter_configs : array of lists
        Array of filter combinations, separated by filter wheel,
        that generate the values in od_values.

    Returns
    -------
    od_nearest : float
        Nominal total ND filter setting for observation

    nd_config : array
        Nominal individual filter wheel settings to reach od_nearest
    '''

    # run ETC to get approximate stellar SNR in SCI channels
    _, wvl_arr, snr_rv_ord, _ = kpf_photon_noise_estimate(teff,
                                                          vmag,
                                                          exp_time,
                                                          quiet=True)
    
    # get the approximate 1D SNR per slice
    snr_rv_ord_slice = snr_rv_ord * (1./3. ** 0.5) # hokey, but not a bad approximation

    # get flux-averaged wavelength of stellar spectrum to match
    wav_avg = np.average(wvl_arr, weights=snr_rv_ord ** 2.)
    peak_ord = _findel(wav_avg, wvl_arr)

    # if no user defined wavelength to match, use the flux-weighted wavelength
    if ref_wave is not None:
        order_ref = _findel(ref_wave, wvl_arr*10.)
#         print('----------------------------------')
#         print('Using reference wavelength: ' + str(ref_wave) + ' Angstrom')
#         print('----------------------------------')
    else:
        order_ref = peak_ord
#         print('----------------------------------')
#         print('No reference wavelength provided -- matching CAL and SCI flux at flux-averaged stellar wavelength')
#         print('----------------------------------')

    # compute the effective stellar flux rate at the reference wavelength
    stellar_flux_rate = snr_rv_ord[order_ref] ** 2. / exp_time # photons per second at order
    stellar_flux_rate_slice = stellar_flux_rate / 3. # approximate per-slice flux rate
    #---------------------------------------------------
    
    # CAL SPECTRUM SCALING
    #---------------------------------------------------
    # flux spectrum of cal source
    spec = np.concatenate((fits.getdata(cal_fits,'GREEN_CAL_FLUX'),fits.getdata(cal_fits,'RED_CAL_FLUX')))
    spec_max = np.nanpercentile(spec, 99, axis=1)

    # wavelengths
    wav = np.concatenate((fits.getdata(cal_fits,'GREEN_CAL_WAVE'),fits.getdata(cal_fits,'RED_CAL_WAVE')))
    wav_mean = np.nanmean(wav, axis=1)

    # relevant exposure settings
    cal_exptime = fits.getval(cal_fits,'EXPTIME') # get cal file exposure time

    # get cal sample file total OD
    ref_OD = float(fits.getval(cal_fits, 'SSCALFW').split(' ')[-1]) + \
                float(fits.getval(cal_fits, 'SIMCALFW').split(' ')[-1])

    spec_max_native = spec_max * (10. ** (ref_OD))
    cal_flux_rate = spec_max[order_ref] / cal_exptime # CAL photons per second at ref order
    cal_flux_rate_native = cal_flux_rate * (10. ** (ref_OD)) # CAL flux rate with no OD filter    
    
    #---------------------------------------------------
    # flux rate of CAL compared to SCI slices
    ratio_flux = cal_flux_rate_native/stellar_flux_rate_slice # ratio

    # find the nearest OD filter to the computed flux rate
    index_od_nearest = _findel(np.log10(ratio_flux), od_values)
    od_nearest = od_values[index_od_nearest] # total OD
    
    # compute the cal flux rate at the nearest OD filter setting
    cal_flux_rate_nearest =  cal_flux_rate_native * (10. ** (-od_nearest))

    # check that the closest CAL flux level is larger than SCI:
    while cal_flux_rate_nearest > stellar_flux_rate_slice * 1.:
        # if it is, bump up to the next OD filter setting
        print('CAL FLUX EXCEEDS STELLAR FLUX -- ADDING MORE OD')
        index_od_nearest += 1
        od_nearest = od_values[index_od_nearest] # total OD
        cal_flux_rate_nearest =  cal_flux_rate_native * (10. ** (-od_nearest))
    else:
        od_nearest = od_values[index_od_nearest]

    # if we're at the maximum filter suppression, spit out a warning
    if index_od_nearest == len(od_values) - 1:
        print('WARNING -- OD FILTERS MAXED OUT')    
    
    # final filter configuration
    nd_config = filter_configs[index_od_nearest]

    # get the nearest OD setting etalon spectrum
    snr_nearest = (spec_max_native/cal_exptime * (10. ** (-od_nearest) * exp_time)) ** 0.5
    
    # if the final etalon spectrum has low SNR, spit out a warning
    if snr_nearest[order_ref] < 60:
        print('WARNING -- LOW SIMULCAL FLUX AT THESE SETTINGS')
        print('CAL SNR at reference wavelength ' + str(np.round(snr_nearest[order_ref],1)))

    if plot:
        cross_ord = 35 # crossover order from GREEN to RED
        plt.plot(wvl_arr[0:cross_ord] * 10., snr_rv_ord_slice[0:cross_ord],'-d',color='k',mec='k',mfc='tab:green',ms=13,mew=2,label='Mean stellar SNR, single slice')
        plt.plot(wvl_arr[cross_ord:] * 10., snr_rv_ord_slice[cross_ord:],'-d',color='k',mec='k',mfc='tab:red',ms=13,mew=2,label='Mean stellar SNR, single slice')
        plt.plot(wav_mean, snr_nearest,'s',mec='k',mfc='tab:orange',ms=12,mew=2,label='Etalon CAL, OD: ' + str(np.round(od_nearest,1)))
        plt.title('V = ' + str(np.round(vmag,1)) + ', Teff = ' + str(int(teff)) 
                  + ' K, ' + str(int(exp_time)) + ' second exposure')
        plt.ylabel('Mean order SNR')
        plt.xlabel('Order wavelength [$\mathcal{\AA}$]')
        plt.legend(ncol=1,loc='best')
        
        plt.show()
#     print('SUGGESTED TOTAL ND: ', str(np.round(od_nearest,1)))
#     print('SUGGESTED FILTER WHEEL SETTINGS --', 
#           'SSCALFW:', nd_config[0],
#           'SIMCALFW:', nd_config[1])
    return od_nearest, nd_config



## ------------------------------
## Convert from Gmag to Vmag
## ------------------------------
def get_GminusV(Teff):
    '''Table of data from:
    https://www.pas.rochester.edu/~emamajek/EEM_dwarf_UBVIJHK_colors_Teff.txt
    '''
    p = Path(__file__).parent
    table_file = p / 'EEM_dwarf_UBVIJHK_colors_Teff.txt'
    if table_file.exists() is False:
        return 0
    t = Table.read(table_file, format='ascii')
    filtered = t[t['G-V'] != '...']
    Teff_diff = abs(filtered['Teff'] - Teff)
    ind = np.argmin(Teff_diff)
    GminusV = float(filtered[ind]['G-V'])
    return GminusV


class PredictNDFilters(KPFFunction):
    '''Predict which ND filters should be used for simultaneous calibrations.

    Args:
        ? (float): 

    Scripts Called:

     - `kpf.calbench.SetND`
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'Gmag', allowed_types=[int, float])
        check_input(args, 'Teff', allowed_types=[int, float])
        check_input(args, 'ExpTime', allowed_types=[int, float])

    @classmethod
    def perform(cls, args):
        tick = datetime.datetime.now()
        gmag = args.get('Gmag')
        teff = args.get('Teff')
        log.debug('Estimating Vmag from Gmag:')
        vmag = gmag - get_GminusV(teff)
        log.debug(f'  Gmag={gmag:.2f} --> Vmag={vmag:.2f}')
        obs_exp_time = args.get('ExpTime')

        # reference calibration file to scale up/down
        #cal_file = 'KP.20240529.80736.43_L1.fits' # reference etalon L1 file
        data_dir = Path(__file__).parent.parent.parent / 'data'
        cal_file = data_dir / 'KP.20240529.80736.43_L1.fits'

        # Filter wheel populations for both wheels
#         od_arr_scical = [0.1, 0.3, 0.5, 0.8, 1.0, 4.0]
#         od_arr_cal = [0.1, 1.0, 1.3, 2., 3., 4.]
#         od_arr_scical = [0.1, 1.0, 1.3, 2., 3., 4.]
#         od_arr_cal = [0.1, 0.3, 0.5, 0.8, 1.0, 4.0]

        ND1POS = ktl.cache('kpfcal', 'ND1POS')
        ND1POS_allowed_values = list(ND1POS._getEnumerators())
        if 'Unknown' in ND1POS_allowed_values:
            ND1POS_allowed_values.pop(ND1POS_allowed_values.index('Unknown'))
        od_arr_scical = [float(pos[3:]) for pos in ND1POS_allowed_values]

        ND2POS = ktl.cache('kpfcal', 'ND2POS')
        ND2POS_allowed_values = list(ND2POS._getEnumerators())
        if 'Unknown' in ND2POS_allowed_values:
            ND2POS_allowed_values.pop(ND2POS_allowed_values.index('Unknown'))
        od_arr_cal = [float(pos[3:]) for pos in ND2POS_allowed_values]

        od_vals_all, filter_configs_all = all_possible_sums_with_indices_sorted(od_arr_scical, od_arr_cal)

        od, nd_config = get_simulcal_od(vmag, teff, obs_exp_time, cal_file,
                            ref_wave=5500, od_values=od_vals_all,
                            filter_configs=filter_configs_all)

        result = {'CalND1': f'OD {nd_config[0]}',
                  'CalND2': f'OD {nd_config[1]}'}
        log.info(f"Predicted ND1 = {result['CalND1']}")
        log.info(f"Predicted ND2 = {result['CalND2']}")
        tock = datetime.datetime.now()
        elapsed = (tock-tick).total_seconds()
        log.debug(f'ND filter calculation took {elapsed:.1f}s')
        if args.get('set', False):
            SetND.execute(result)
        return result

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('Gmag', type=float,
                            help="The gaia G magnitude of the target")
        parser.add_argument('Teff', type=float,
                            help="The effective temperature of the target")
        parser.add_argument('ExpTime', type=float,
                            help="The exposure time on target")
        parser.add_argument("--set", dest="set",
            default=False, action="store_true",
            help="Set these values after calculating?")
        return super().add_cmdline_args(parser)
