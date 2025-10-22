#!python3

## Import General Tools
from pathlib import Path
import argparse
import datetime
import re

import numpy as np
import matplotlib.pylab as plt

from scipy.fft import fft
import scipy
import scipy.stats


##-------------------------------------------------------------------------
## Parse Command Line Arguments
##-------------------------------------------------------------------------
## create a parser object for understanding command-line arguments
p = argparse.ArgumentParser(description='''Overlay the power spectrum of the
detector noise from the "horizontal raw plot" data from ArchonGUI. If multiple
input files are provided they will be over plotted on one another.

This was designed to work on the FITS files produced by archonGUI (see
https://keckobservatory.atlassian.net/wiki/x/AYAnk) and is not tested on files
from the main KPF data taking system (e.g. the KTL keywords). The file names
are assumed to match a particular pattern:
* start with either G or R to indicate whether it is the green or red side
* include a description in the middle offset by underscores (`_`).
* include pixel dimension (e.g. `_4188x4110`, the default from ArchonGUI).
* end in the frame number (again the default from ArchonGUI)
''')
## add arguments
p.add_argument('files', nargs='*',
               help="The files to process")
## add options
p.add_argument("-m", "--marker", dest="marker", type=float,
    help="Put a marker at this frequency (in kHz).")
p.add_argument("-o", "--outfile", dest="outfile", type=str, default='FFTs.png',
    help="The output file name (defaults to FFTs.png).")
args = p.parse_args()



def load_archon_video(filename='Aug11_regulargreen/2025aug11/6070.csv',maxrows=2560000):
    """ 
    loads voltage data and creates time array in nanoseconds
    archon samples video signal at 10ns per step or 100MHz
    """
    x,y = np.loadtxt(filename,skiprows=1,max_rows=maxrows).T
    # step size for archon is 
    tstep = 10 # 10 nano seconds or 100MHz
    return x*tstep, y


def extract_pixel_data(xs, ys, iref, ipix, pixel_time=4980,gain=5):
    """
    average reference region and pixel region for each pixel

    returns the final pixel data and N, which should be the number of pixels

    default is gain of 5 and pixel time of 4980ns (regular read mode)
    """
    ref_data  = []
    pix_data  = []
    ref_noise = []
    pix_noise = []
    N=0
    while pixel_time * N < xs[-1]:
        ref_data.append(np.nanmean(ys[(pixel_time*N +iref[0])//10: (pixel_time*N +iref[1])//10]))
        pix_data.append(np.nanmean(ys[(pixel_time*N +ipix[0])//10: (pixel_time*N +ipix[1])//10]))
        ref_noise.append(np.nanstd(ys[(pixel_time*N +iref[0])//10: (pixel_time*N +iref[1])//10]))
        pix_noise.append(np.nanstd(ys[(pixel_time*N +ipix[0])//10: (pixel_time*N +ipix[1])//10]))
        N+=1

    final_data = np.array(ref_data) - np.array(pix_data)
#     print('%s pixels read' %N)

    return gain * final_data, ref_noise, pix_noise


def do_fft(x,y):
    """run FFT of x and y data, x in seconds gives freq in hz"""
    X = fft(y)
    sampling_time = np.mean(np.diff(x))
    freq = scipy.fft.fftfreq(len(X), sampling_time)
    
    return np.abs(freq), np.abs(X)


##-------------------------------------------------------------------------
## Main Program
##-------------------------------------------------------------------------
def main():
    # Parse files
    fileinfo = {}
    for file in args.files:
        fnmatch = re.match('([GR])[a-zA-Z]*_(.*)_4188x4110_(\d+)\.(\w+)', Path(file).name)
        if fnmatch:
            timestamp = datetime.datetime.fromtimestamp(Path(file).stat().st_mtime)
            fileinfo[file] = {'det': fnmatch.group(1),
                              'label': fnmatch.group(2),
                              'frameno': int(fnmatch.group(3)),
                              'ext': fnmatch.group(4),
                              'timestamp': timestamp,
                              'timestr': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                              }
        else:
            print(f'Failed to parse filename: {Path(file).name}')


    pixel_time = 4980         # nanoseconds,  should be 2520 nanoseconds for fast read mode
    iref = np.array([530,2120])+2120     # tuning of these regions are not critical when clocks are off
    ipix = np.array([3300,5000])+2120    # these were tuned on clock data

    txtfiles = [file for file in fileinfo.keys() if fileinfo[file]['ext'] == 'txt']

    num_colors = len(txtfiles)
    colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']

    plt.figure(figsize=(12,8))
    for i,file in enumerate(txtfiles):
        print(f'Getting FFT of {file}')
        xs, ys = load_archon_video(filename=file, maxrows=737000)
        alldata, pix_data, ref_data = extract_pixel_data(xs, ys, iref, ipix, pixel_time=pixel_time)
        allnoise = np.std(alldata[200:1153])#[14:146]) # exclude the spike from parallel read out
        xf, yfft  =  do_fft(xs[100000:]*1e-9, ys[100000:])
        label = f"{fileinfo[file]['det']} {fileinfo[file]['frameno']}: {fileinfo[file]['label']}"
        multiplier = 1#e3**i
        plt.loglog(xf, yfft*multiplier, f'{colors[i]}-', alpha=0.25)
        # Bin data and plot mean in each bin
        means, bins, binnumber = scipy.stats.binned_statistic(xf, yfft, statistic='mean', bins=10000)
        plt.loglog(bins[1:], means*multiplier, f'{colors[i]}-', alpha=0.75,
                   drawstyle='steps-pre', label=label)
    if args.marker:
        freq = args.marker*1e3
        plt.axvline(x=freq, color='b', linestyle=':', ymin=0.1, ymax=0.9, alpha=0.5,
                    label=f'{args.marker:,.0f} kHz')

    plt.title('FFT of Video Signals')
    plt.legend()
    plt.xlabel("Freq (Hz)")
    plt.xlim(1e4,5e7)
    plt.ylabel('Amplitude')
    plt.grid()
    plt.savefig(args.outfile, bbox_inches='tight', pad_inches=0.1)



if __name__ == '__main__':
    main()
