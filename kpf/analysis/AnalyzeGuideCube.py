#!python3

## Import General Tools
from pathlib import Path
import argparse
import logging
import subprocess

import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy import visualization as vis
from astropy.modeling import models, fitting

from matplotlib import pyplot as plt
import imageio


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
## Create logger object
##-------------------------------------------------------------------------
log = logging.getLogger('MyLogger')
log.setLevel(logging.DEBUG)
## Set up console output
LogConsoleHandler = logging.StreamHandler()
LogConsoleHandler.setLevel(logging.DEBUG)
LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s')
LogConsoleHandler.setFormatter(LogFormat)
log.addHandler(LogConsoleHandler)


##-------------------------------------------------------------------------
## plot_cube_stats
##-------------------------------------------------------------------------
def plot_cube_stats(file, plotfile=None):
    log.info('Generating summary plot')
    hdul = fits.open(file)
    fps = hdul[0].header.get('FPS', None)
    if fps is None:
        log.warning(f"Could not read FPS from header. Assuming 100.")
        fps = 100
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
    xdeltas = np.array([x-xvals[i-1] if i > 0 else 0\
                        for i,x in enumerate(xvals.filled(fill_value=0))])
    ydeltas = np.array([y-yvals[i-1] if i > 0 else 0\
                        for i,y in enumerate(yvals.filled(fill_value=0))])

    plt.figure(figsize=(16,6))

    plt.subplot(2,2,(1,3))
    plt.title(f"{file.name} ({len(t)} frames)")
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
    plt.plot(times, xvals-xvals.mean(), 'g-', label=f'X (rms={xrms:.2f} pix)')
    for badt in times[xvals.mask]:
        plt.plot([badt,badt], plotylim, 'r-', alpha=0.3)
    plt.plot(times, yvals-yvals.mean(), 'r-', label=f'Y (rms={yrms:.2f} pix)')
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
    log.info('Done.')


##-------------------------------------------------------------------------
## generate_cube_gif
##-------------------------------------------------------------------------
def generate_cube_gif(file, giffile):
    log.info('Generating animated gif')
    hdul = fits.open(file)
    cube = hdul[1].data
    t = Table(hdul[2].data)
    nf, ny, nx = cube.shape
    norm = vis.ImageNormalize(cube,
                          interval=vis.AsymmetricPercentileInterval(0.9,99.99),
                          stretch=vis.LogStretch())

    plotdir = Path('~/tmp/cubefiles').expanduser()
    if plotdir.exists() is False:
        plotdir.mkdir(parents=True)
    png_filenames = []

    log.info("  Generating individual png file for each frame")
    for j,im in enumerate(cube):
        plotfile = plotdir / f"cubeslice_{j:04d}.png"
        png_filenames.append(plotfile)
        if plotfile.exists() is True: plotfile.unlink()

        plt.figure(figsize=(8,8))
        plt.title(f"{file.name}: frame {j:04d}")
        plt.imshow(im, origin='lower', cmap='gray', norm=norm)

        if t[j]['object1_x'] > 0 and t[j]['object1_y'] > 0:
            xpix = t[j]['object1_x'] - (t[j]['target_x'] - nx/2)
            ypix = t[j]['object1_y'] - (t[j]['target_y'] - ny/2)
            plt.plot(xpix, ypix, 'r+')

        plt.savefig(plotfile, bbox_inches='tight', pad_inches=0.10)
        plt.close()

    log.info("  Assembling animated GIF")
    with imageio.get_writer(giffile, mode='I') as writer:
        for filename in png_filenames:
            image = imageio.imread(filename)
            writer.append_data(image)
    log.info('Done.')


##-------------------------------------------------------------------------
## if __name__ == '__main__':
##-------------------------------------------------------------------------
if __name__ == '__main__':
    file = Path(args.file).expanduser()
    if file.exists() is False:
        log.error(f"Could not find file {args.file}")

    viewer_commands = ['eog', 'open']
    viewer_command = None
    for cmd in viewer_commands:
        rtn = subprocess.call(['which', cmd])
        if rtn == 0:
            viewer_command = cmd

    plotfile = Path(str(file.name).replace('.fits', '.png'))
    plot_cube_stats(file, plotfile=plotfile)

    log.info(f"Opening {plotfile} using {viewer_command}")
    if viewer_command is not None:
        proc = subprocess.Popen([viewer_command, f"{plotfile}"])

    giffile = Path(str(file.name).replace('.fits', '.gif'))
    generate_cube_gif(file, giffile)

    log.info(f"Opening {giffile} using {viewer_command}")
    if viewer_command is not None:
        proc = subprocess.Popen([viewer_command, f"{giffile}"])