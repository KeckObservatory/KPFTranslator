#!python3

## Import General Tools
import sys
import os
from pathlib import Path
import argparse
import logging
import subprocess
from datetime import datetime, timedelta

import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy import visualization as vis
from astropy.modeling import models, fitting

from matplotlib import animation
from matplotlib import pyplot as plt


##-------------------------------------------------------------------------
## Parse Command Line Arguments
##-------------------------------------------------------------------------
## create a parser object for understanding command-line arguments
p = argparse.ArgumentParser(description='''
''')
## add arguments
p.add_argument('files', type=str, nargs='*',
               help="The cube files to analyze")
p.add_argument("-g", "--gif", dest="gif",
    default=False, action="store_true",
    help="Generate the animated GIF of frames (computationally expensive)")
p.add_argument("--view", dest="view",
    default=False, action="store_true",
    help="Open a viewer once the file is generated")
p.add_argument("-v", "--verbose", dest="verbose",
    default=False, action="store_true",
    help="Be verbose")
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
LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s')
LogConsoleHandler.setFormatter(LogFormat)
log.addHandler(LogConsoleHandler)


##-------------------------------------------------------------------------
## plot_cube_stats
##-------------------------------------------------------------------------
def plot_cube_stats(file, plotfile=None):
    file = Path(file)
    log.info(f'Generating summary plot for {file.name}')
    hdul = fits.open(file)
    fps = hdul[0].header.get('FPS', None)
    if fps is None:
        log.warning(f"Could not read FPS from header. Assuming 100.")
        fps = 100

    cube_ext = None
    table_ext = None
    for i,ext in enumerate(hdul):
        if ext.name == 'guider_cube_origins':
            table_ext = i
        if ext.name == 'guider_cube':
            cube_ext = i

    t = Table(hdul[table_ext].data)

    # Examine timestamps for consistency
    line0 = models.Linear1D()
    fitter = fitting.LinearLSQFitter()
    indicies = [i for i in range(len(t['timestamp']))]
    fit = fitter(line0, indicies, t['timestamp'])
    timedeltas = t['timestamp'] - fit(indicies)
    mintimedeltas = min(timedeltas)*1000
    maxtimedeltas = max([max(timedeltas)*1000,abs(mintimedeltas)])
    rmstimedeltas = np.std(timedeltas)*1000
    meantimedeltas = np.mean(timedeltas)*1000

    # Examine position statistics
    log.debug(f"  Generating objectvals")
    maskx = t['object1_x']<-998
    masky = t['object1_y']<-998
    maskall = maskx | masky
    objectxvals = np.ma.MaskedArray(t['object1_x'], mask=maskx)
    objectyvals = np.ma.MaskedArray(t['object1_y'], mask=masky)
    times = t['timestamp']-t['timestamp'][0]

    log.debug(f"  Generating objecterr")
    objectxerr = np.ma.MaskedArray(t['object1_x']-t['target_x'], mask=maskx)
    objectyerr = np.ma.MaskedArray(t['object1_y']-t['target_y'], mask=masky)
    r = ((t['object1_x']-t['target_x'])**2 + (t['object1_y']-t['target_y'])**2)**0.5
    objectrerr = np.ma.MaskedArray(r, mask=maskall)
    plotylim = (min([objectxerr.min(), objectyerr.min()])-0.5,
                max([objectxerr.max(), objectyerr.max()])+0.5)
    log.debug(f"  Generating objecterr statistics")
    xrms = objectxerr.std()
    yrms = objectyerr.std()
    rrms = objectrerr.std()
    xbias = objectxerr.mean()
    ybias = objectyerr.mean()
    rbias = (xbias**2 + ybias**2)**0.5

    # Examine stellar motion statistics
    log.debug(f"  Generating deltas")
    oxvf = objectxvals.filled(fill_value=np.nan)
    xdeltas = [val-oxvf[i-1] for i,val in\
               enumerate(oxvf)\
               if i > 0 and not np.isnan(val) and not np.isnan(oxvf[i-1])]
    oyvf = objectyvals.filled(fill_value=np.nan)
    ydeltas = [val-oyvf[i-1] for i,val in\
               enumerate(oyvf)\
               if i > 0 and not np.isnan(val) and not np.isnan(oyvf[i-1])]
    xerrs = [val\
             for val in objectxvals.filled(fill_value=np.nan)\
             if np.isnan(val) == False]
    yerrs = [val\
             for val in objectyvals.filled(fill_value=np.nan)\
             if np.isnan(val) == False]

    plt.figure(figsize=(16,8))

    log.debug(f"  Generating PSD Plot")
    plt.subplot(2,2,1)
    plt.title(f"Power Spectral Distribution\n{file.name} ({len(xerrs)}/{len(t)} frames)")
    if len(xerrs) > 0:
        plt.psd(xdeltas, Fs=fps, color='g', drawstyle='steps-mid', alpha=0.6,
                label='X F2F')
        plt.psd(ydeltas, Fs=fps, color='b', drawstyle='steps-mid', alpha=0.6,
                label='Y F2F')
        plt.legend(loc='best')
    plt.yticks([v for v in np.arange(-70,20,10)])
    plt.ylim(-70,10)
    plt.xlim(0,fps/2)

#     plt.subplot(2,2,3)
#     if len(xerrs) > 0:
#         plt.psd(xerrs, Fs=fps, color='g', drawstyle='steps-mid', alpha=0.6,
#                 label='X Err')
#         plt.psd(yerrs, Fs=fps, color='b', drawstyle='steps-mid', alpha=0.6,
#                 label='Y Err')
#         plt.legend(loc='best')

    log.debug(f"  Generating Time Deltas Plot")
    plt.subplot(2,2,2)
    plt.title(f"Time deltas: mean={meantimedeltas:.1f}, rms={rmstimedeltas:.1f}, max={maxtimedeltas:.1f} ms")
    n, bins, foo = plt.hist(timedeltas*1000, bins=100)
    plt.xlabel('Time Delta (ms)')
    plt.ylabel('N frames')

    log.debug(f"  Generating Positional Error Plot")
    plt.subplot(2,2,3)
    ps = 56 # mas/pix
    plt.title(f"rms={rrms:.2f} pix ({rrms*ps:.1f} mas), bias={rbias:.2f} pix ({rbias*ps:.1f} mas)")
    plt.plot(times[~objectxerr.mask], objectxerr[~objectxerr.mask], 'g-',
             alpha=0.5, drawstyle='steps-mid', label=f'Xpos-Xtarg')
#     for badt in times[objectxerr.mask]:
#         plt.plot([badt,badt], plotylim, 'r-', alpha=0.1)
    plt.plot(times[~objectyerr.mask], objectyerr[~objectyerr.mask], 'b-',
             alpha=0.5, drawstyle='steps-mid', label=f'Ypos-Ytarg')
#     for badt in times[objectyerr.mask]:
#         plt.plot([badt,badt], plotylim, 'r-', alpha=0.1)
    plt.legend(loc='best')
    plt.ylabel('delta pix')
    plt.ylim(plotylim)
    plt.grid()
    plt.xlim(0,times[-1])
    plt.xlabel('Time (s)')

    log.debug(f"  Generating Positional Error Histogram")
    plt.subplot(2,2,4)
    plt.title(f"rms={rrms:.2f} pix ({rrms*ps:.1f} mas), bias={rbias:.2f} pix ({rbias*ps:.1f} mas)")
    nx, binsx, foox = plt.hist(objectxerr[~objectxerr.mask], bins=100, label='X',
                               color='g', alpha=0.6)
    ny, binsy, fooy = plt.hist(objectyerr[~objectyerr.mask], bins=100, label='Y',
                               color='b', alpha=0.3)
    maxhist = 1.1*max([max(nx), max(ny)])
    plt.plot([0,0], [0, maxhist], 'r-', alpha=0.3)
    plt.ylim(0, maxhist)
    plt.legend(loc='best')
    plt.xlabel('Position Error')
    plt.ylabel('N frames')


    if plotfile is not None:
        log.debug(f"  Saving Plot File")
        plt.savefig(plotfile, bbox_inches='tight', pad_inches=0.1)
    else:
        plt.show()
    log.info('Done.')


##-------------------------------------------------------------------------
## generate_cube_gif
##-------------------------------------------------------------------------
def generate_cube_gif(file, giffile):
    log.info('Generating animation')
    hdul = fits.open(file)

    date_beg = hdul[0].header.get('DATE-BEG')
    start = datetime.fromisoformat(date_beg)
    date_end = hdul[0].header.get('DATE-END')
    end = datetime.fromisoformat(date_end)
    duration = (end - start).total_seconds()

    cube_ext = None
    table_ext = None
    for i,ext in enumerate(hdul):
        if ext.name == 'guider_cube_origins':
            table_ext = i
        if ext.name == 'guider_cube':
            cube_ext = i

    if cube_ext is None:
        return

    cube = hdul[cube_ext].data
    t = Table(hdul[table_ext].data)
    nf, ny, nx = cube.shape
    norm = vis.ImageNormalize(cube,
                          interval=vis.AsymmetricPercentileInterval(1.5,99.99),
                          stretch=vis.LogStretch())

    # ims is a list of lists, each row is a list of artists to draw in the
    # current frame; here we are just animating one artist, the image, in
    # each frame
    
    fig = plt.figure(figsize=(8,8))

    fps = 10
    if sys.platform == 'darwin':
#         writer = animation.ImageMagickWriter(fps=fps)
#         writer = animation.ImageMagickFileWriter(fps=fps)
        writer = animation.FFMpegWriter(fps=fps)
#         writer = animation.PillowWriter(fps=fps)
    else:
        writer = animation.ImageMagickWriter(fps=fps)


    log.info('Building individual frames')
    ims = []
    for j,im in enumerate(cube):
        plt.title(f"{file.name}: {duration:.1f} s, {nf:d} frames")
        im = plt.imshow(im, origin='lower', cmap='gray', norm=norm, animated=True)
        frametext = plt.text(nx-20, ny-5, f"{j:04d}/{nf:04d}", color='r')
        lines = []
        if t[j]['object1_x'] > 0 and t[j]['object1_y'] > 0:
            xpix = t[j]['object1_x'] - (t[j]['target_x'] - nx/2)
            ypix = t[j]['object1_y'] - (t[j]['target_y'] - ny/2)
            lines = plt.plot(xpix, ypix, 'r+')
        newim = [im] + [frametext] + lines
        ims.append(newim)
        if j%100 == 0
        log.info(f"Processed frame {j}/{nf}")

    log.info('Building animation')
    ani = animation.ArtistAnimation(fig, ims, interval=1000/fps, blit=True,
                                    repeat_delay=1000)
    log.info(f'Writing {giffile} using {writer}')
    p = Path(giffile)
    if p.expanduser().exists(): p.unlink()
    ani.save(f"{giffile}", writer)
    log.info('Done')


def generate_cube_gif_old(file, giffile):
    import imageio

    log.info('Generating animated gif')
    hdul = fits.open(file)
    cube = hdul[1].data
    t = Table(hdul[2].data)
    nf, ny, nx = cube.shape
    norm = vis.ImageNormalize(cube,
                          interval=vis.AsymmetricPercentileInterval(1.5,99.99),
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
    for file in args.files:
        file = Path(file).expanduser()
        if file.exists() is False:
            log.error(f"Could not find file {args.file}")

        viewer_command = None
        if args.view is True:
            viewer_commands = ['eog', 'open']
            for cmd in viewer_commands:
                rtn = subprocess.call(['which', cmd])
                if rtn == 0:
                    viewer_command = cmd

        plotfile = Path(str(file.name).replace('.fits', '.png'))
        plot_cube_stats(file, plotfile=plotfile)

        if viewer_command is not None:
            log.info(f"Opening {plotfile} using {viewer_command}")
            proc = subprocess.Popen([viewer_command, f"{plotfile}"])

        if args.gif is True:
            giffile = Path(str(file.name).replace('.fits', '.gif'))
            generate_cube_gif(file, giffile)

            if viewer_command is not None:
                log.info(f"Opening {giffile} using {viewer_command}")
                proc = subprocess.Popen([viewer_command, f"{giffile}"])
