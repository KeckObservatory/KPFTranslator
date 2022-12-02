#!python3

## Import General Tools
from pathlib import Path
import argparse

import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy import visualization as vis
from astropy.modeling import models, fitting

from matplotlib import pyplot as plt


##-------------------------------------------------------------------------
## Parse Command Line Arguments
##-------------------------------------------------------------------------
## create a parser object for understanding command-line arguments
p = argparse.ArgumentParser(description='''
''')
## add arguments
p.add_argument('file', type=str,
               help="The cube file to analyze")
args = p.parse_args()


##-------------------------------------------------------------------------
## analyze_grid_search
##-------------------------------------------------------------------------
def plot_cube_stats(infile, plotfile=None):
    file = Path(infile).expanduser()
    if file.exists() is False:
        print(f"Could not find file {infile}")
    filename = file.name
    hdul = fits.open(file)
    fps = hdul[0].header.get('FPS', 100)
    t = Table(hdul[2].data)

    line0 = models.Linear1D()
    fitter = fitting.LinearLSQFitter()
    indicies = [i for i in range(len(t['timestamp']))]
    fit = fitter(line0, indicies, t['timestamp'])
    diff = t['timestamp'] - fit(indicies)

    xvals = np.ma.MaskedArray(t['object1_x'], mask=t['object1_x']<-998)
    yvals = np.ma.MaskedArray(t['object1_y'], mask=t['object1_y']<-998)
    times = t['timestamp']-t['timestamp'][0]

    mindiff = min(diff)*1000
    maxdiff = max([max(diff)*1000,abs(mindiff)])
    rmsdiff = np.std(diff)*1000

    xdelta = xvals-xvals.mean()
    ydelta = yvals-yvals.mean()
    plotylim = (min([xdelta.min(), ydelta.min()])-0.5,
                max([xdelta.max(), ydelta.max()])+0.5)
    xrms = xdelta.std()
    yrms = ydelta.std()
    
    plt.figure(figsize=(16,6))

    xdeltas = np.array([x-xvals[i-1] if i > 0 else 0 for i,x in enumerate(xvals)])
    ydeltas = np.array([y-yvals[i-1] if i > 0 else 0 for i,y in enumerate(yvals)])
    plt.subplot(2,2,(1,3))
    plt.title(f"{filename}: nframes={len(t)}")
    plt.psd(xdeltas, Fs=fps, color='g', label='X')
    plt.psd(ydeltas, Fs=fps, color='r', label='Y')
    plt.legend(loc='best')

    plt.subplot(2,2,2)
    plt.title(f"Time deltas: rms={rmsdiff:.1f} ms, max={maxdiff:.1f} ms")
    plt.plot(times, diff*1000)
    plt.ylabel('delta time (ms)')
    plt.xlim(0,times[-1])
    plt.grid()
    
    plt.subplot(2,2,4)
    plt.plot(times, xvals-xvals.mean(), 'g-', label=f'X (rms={xrms:.2f})')
    for badt in times[xvals.mask]:
        plt.plot([badt,badt], plotylim, 'r-', alpha=0.3)
    plt.plot(times, yvals-yvals.mean(), 'r-', label=f'Y (rms={yrms:.2f})')
    for badt in times[yvals.mask]:
        plt.plot([badt,badt], plotylim, 'r-', alpha=0.3)
    plt.legend(loc='best')
    plt.ylabel('delta pix')
    plt.ylim(plotylim)
    plt.grid()
    plt.xlim(0,times[-1])
    plt.xlabel('Time (s)')

    if plotfile is not None:
        plt.savefig(plotfile, bbox_inches='tight', pad_inches=0.1)
    else:
        plt.show()


if __name__ == '__main__':
    plot_cube_stats(args.file, plotfile=None)
