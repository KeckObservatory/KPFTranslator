#!python3

## Import General Tools
from pathlib import Path
import argparse
import logging
import re

from pathlib import Path
import numpy as np
from astropy.io import fits
from astropy import visualization as viz
from astropy import units as u
from astropy.table import Table
from astropy import stats
from astropy.nddata import CCDData
import ccdproc
import photutils
from photutils.centroids import centroid_com, centroid_2dg

from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator

##-------------------------------------------------------------------------
## Parse Command Line Arguments
##-------------------------------------------------------------------------
## create a parser object for understanding command-line arguments
p = argparse.ArgumentParser(description='''
''')
## add arguments
p.add_argument('datetimestr', type=str,
               help="The date and time string of the grid search (e.g. 20221107at090316).")
## add flags
p.add_argument("-v", "--verbose", dest="verbose",
    default=False, action="store_true",
    help="Be verbose! (default = False)")
## add options
p.add_argument("--flux_prefix", dest="flux_prefix", type=str,
    default='cur',
    help="The flux prefix to use ('cur', 'raw', or 'bck').")
p.add_argument("--fiber", dest="fiber", type=str,
    default='Science',
    help="The fiber being examined (Science, Sky, or EMSky).")
p.add_argument("--data_path", dest="data_path", type=str,
    default='/s/sdata1701/kpfeng/2022dec14',
    help="The path to the data directory with logs and CRED2 sub-directories")
args = p.parse_args()


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
log = logging.getLogger('MyLogger')
log.setLevel(logging.DEBUG)
## Set up console output
LogConsoleHandler = logging.StreamHandler()
if args.verbose is True:
    LogConsoleHandler.setLevel(logging.DEBUG)
else:
    LogConsoleHandler.setLevel(logging.INFO)
LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
LogConsoleHandler.setFormatter(LogFormat)
log.addHandler(LogConsoleHandler)
## Set up file output
# LogFileName = None
# LogFileHandler = logging.FileHandler(LogFileName)
# LogFileHandler.setLevel(logging.DEBUG)
# LogFileHandler.setFormatter(LogFormat)
# log.addHandler(LogFileHandler)


##-------------------------------------------------------------------------
## analyze_grid_search
##-------------------------------------------------------------------------
def analyze_test_science_ADC(date_time_string, flux_prefix=None, fiber='Science',
                             data_path=Path('/s/sdata1701/kpfeng/2022dec14'),
                             ):
    ks = [0,1,2,3]

    cred2_pixels = {'EMSky': (160, 256),
                    'Science': (335, 256),
                    'Sky': (510, 256)}[fiber]
    fvcsci_pixels = {'EMSky': None,
                     'Science': (800, 600),
                     'Sky': None}[fiber]
    fvccahk_pixels = {'EMSky': None,
                     'Science': (800, 600),
                     'Sky': None}[fiber]
    fvcext_pixels = {'EMSky': None,
                     'Science': (620, 700),
                     'Sky': None}[fiber]
    if flux_prefix is None:
        flux_prefix = {'EMSky': 'bck',
                       'Science': 'cur',
                       'Sky': None}[fiber]

    fluxes_file = data_path / Path('script_logs') / Path(f'TestScienceADC_fluxes_{date_time_string}.txt')
    log_file = data_path / Path('script_logs') / Path(f'TestScienceADC_{date_time_string}.log')
    ouput_analysis_image_file = Path(f"{date_time_string}_science_ADC.png")

    flux_table = Table.read(fluxes_file, format='ascii.csv')
    npos = len(flux_table)
    nx = len(set(flux_table['dx']))
    ny = len(set(flux_table['dy']))
    log.info(f"Read in {fluxes_file.name} with {npos} lines in {nx} x {ny} grid")

    try:
        with open(log_file) as FO:
            lines = FO.readlines()
        for line in lines[:20]:
            m = re.search("comment: (.*)", line)
            if m is not None:
                comment = m.groups()[0].strip('\n')
        log.info(f"Log Comment: {comment}")
    except:
        comment = ''
        log.error('Could not find comment in log file')

    # WAVEBINS = 498.125 604.375 710.625 816.875
    wavebins = [498.125, 604.375, 710.625, 816.875]
#     symbols = ['b^', 'gx', 'yo', 'r^']

    flux_plots = []
    flux_plot_labels = []
    for counter,flux_entry in enumerate(flux_table):
        dx = flux_entry['dx']
        dy = flux_entry['dy']
        f = [flux_entry[f'{flux_prefix}{k+1}'] for k in [0,1,2,3]]
        norm = f/sum(f)
        flux_plots.append(norm)
        flux_plot_labels.append(f"{dx:.1f}, {dy:.1f}")

    flux_plots = np.array(flux_plots)
    wave_plots = []
    wave_plot_labels = []
    for k in [0,1,2,3]:
        wave_plots.append(flux_plots[:,k])
        wave_plot_labels.append(f"{wavebins[k]:.0f} nm")

    plt.figure(figsize=(12,7))
    
    plt.subplot(2,1,1)
    plt.title(f"ADC Optimization")
    for counter,flux_plot in enumerate(flux_plots):
        plt.plot(wavebins, flux_plot, label=flux_plot_labels[counter])
    plt.ylabel('Relative Flux')
    plt.ylim(0,1.1)
    plt.xlabel('Wavelength (nm)')
    plt.xlim(485,925)
    plt.legend(loc='best')
    plt.grid()



    plt.subplot(2,1,2)
    for counter,wave_plot in enumerate(wave_plots):
        plt.plot(wave_plot, label=wave_plot_labels[counter])
    plt.ylabel('Relative Flux')
    plt.ylim(0,1.1)
    plt.xlabel('Run Number')
    plt.xlim(-0.2,npos*1.1)
    plt.grid()
    plt.legend(loc='best')

    plt.show()


if __name__ == '__main__':
    analyze_test_science_ADC(args.datetimestr,
                             flux_prefix=args.flux_prefix,
                             fiber=args.fiber,
                             data_path=args.data_path)
