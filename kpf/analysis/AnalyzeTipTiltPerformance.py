#!python3

## Import General Tools
import sys
import os
import yaml
from pathlib import Path
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

from kpf.KPFTranslatorFunction import KPFTranslatorFunction


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
log = logging.getLogger('MyLogger')
log.setLevel(logging.DEBUG)
## Set up console output
LogConsoleHandler = logging.StreamHandler()
LogConsoleHandler.setLevel(logging.INFO)
LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s')
LogConsoleHandler.setFormatter(LogFormat)
log.addHandler(LogConsoleHandler)


##-------------------------------------------------------------------------
## read_file
##-------------------------------------------------------------------------
def read_file(file):
    '''Read the file on disk, either the L0 file or the kpfguide_cube file.
    
    Return an astropy.table.Table of telemetry, the image cube (if present),
    and a dictionary with selected metadata.
    '''
    hdul = fits.open(file)
    # print(hdul.info())
    guider_cube = None
    guide_origins_hdu = None
    guide_cube_header_hdu = fits.PrimaryHDU()
    L0_header_hdu = fits.PrimaryHDU()
    for hdu in hdul:
        if hdu.name == 'guider_cube_origins':
            log.info(f"Found: {hdu.name}")
            guide_origins_hdu = hdu
        if hdu.name == 'guider_avg':
            log.info(f"Found: {hdu.name}")
            guide_cube_header_hdu = hdu
        if hdu.name == 'PRIMARY':
            log.info(f"Found: {hdu.name}")
            L0_header_hdu = hdu
        if hdu.name == 'guider_cube':
            log.info(f"Found: {hdu.name}")
            guider_cube = hdu.data
    # Assemble metadata
    metadata = {'FPS': guide_cube_header_hdu.header.get('FPS', None),
                'DATE-BEG': guide_cube_header_hdu.header.get('DATE-BEG', None),
                'DATE-END': guide_cube_header_hdu.header.get('DATE-END', None),
                'IMTYPE': L0_header_hdu.header.get('IMTYPE', None),
                'Gmag': L0_header_hdu.header.get('GAIAMAG', None),
                'Jmag': L0_header_hdu.header.get('2MASSMAG', None),
                'TARGNAME': L0_header_hdu.header.get('TARGNAME', None),
                'IMTYPE': L0_header_hdu.header.get('IMTYPE', None),
               }
    if metadata['FPS'] is None:
        # Assume 100 FPS
        metadata['FPS'] = 100
    if metadata['DATE-BEG'] is None:
        metadata['DATE-BEG'] = L0_header_hdu.header.get('DATE-BEG', None)
    if metadata['DATE-END'] is None:
        metadata['DATE-END'] = L0_header_hdu.header.get('DATE-END', None)

    if metadata['IMTYPE'] not in [None, 'Object']:
        return None, None, None
    if guide_origins_hdu is None:
        return None, metadata, guider_cube
    else:
        return Table(guide_origins_hdu.data), metadata, guider_cube


##-------------------------------------------------------------------------
## plot_tiptilt_stats
##-------------------------------------------------------------------------
def plot_tiptilt_stats(file, plotfile=None, start=None, end=None):
    results = {'file': f"{file}"}
    ps = 56 # mas/pix
    log.info(f'Reading file: {file}')
    t, metadata, _ = read_file(file)
    if t is None: return
    log.info('Processing telemetry table')
    fps = metadata['FPS']
    Gmag = metadata['Gmag']
    Jmag = metadata['Jmag']
    targname = metadata['TARGNAME']

    results['FPS'] = fps
    results['Gmag'] = Gmag
    results['Jmag'] = Jmag
    results['TARGNAME'] = targname

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

    results['RMS of Time Deltas (ms)'] = float(rmstimedeltas)

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

    results['Position Error RMS (mas)'] = float(rrms*ps)
    results['Position Error Bias (mas)'] = float(rbias*ps)

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

    # Calculate FWHM
    objectavals = np.ma.MaskedArray(t['object1_a'], mask=maskall)
    objectbvals = np.ma.MaskedArray(t['object1_b'], mask=maskall)
    coef = 2*np.sqrt(2*np.log(2))
    fwhm = np.sqrt((coef*objectavals)**2 + (coef*objectbvals)**2)
    fwhm *= ps/1000
    mean_fwhm = np.mean(fwhm)

    results['FWHM (arcsec)'] = float(mean_fwhm)

    # Mean Flux
    flux_kcounts = t['object1_flux'] / 1000
    mean_flux = np.mean(t['object1_flux'][~objectxerr.mask])

    results['Flux (ADU)'] = float(mean_flux)

    # Count number of stars
    nstars = []
    for entry in t:
        star_count = 0
        for i in [1,2,3]:
            if entry[f'object{i}_x'] > -998:
                star_count +=1
        nstars.append(star_count)
    nstars = np.array(nstars, dtype=int)
    median_nstars = int(np.median(nstars))
    w_nstars_off = np.where(nstars != median_nstars)[0]
    nframes_with_incorrect_nstars = len(w_nstars_off)

    results['Nframes'] = int(len(nstars))
    results['Median Nstars'] = int(median_nstars)
    results['Frames with Incorrect Nstars'] = int(nframes_with_incorrect_nstars)

    plt.figure(figsize=(16,8))

    log.debug(f"  Generating Flux Plot")
    plt.subplot(2,2,1)
    title_line1 = f"{file.name} ({len(xerrs)}/{len(t)} frames)"
    title_line2 = ''
    if metadata['Gmag'] is not None:
        title_line2 += f"{targname}: Gmag={Gmag}, Jmag={Jmag}, FWHM={mean_fwhm:.2f}"
    plt.title(f"{title_line1}\n{title_line2}")
    flux_line = plt.plot(times[~objectxerr.mask],
                         flux_kcounts[~objectxerr.mask],
                         'k-', alpha=0.5, drawstyle='steps-mid', label=f'flux')
    plt.plot(times, np.ones(len(times))*5, 'r-', alpha=0.1, label='Too Dim')
    if start is not None and end is not None:
        plt.xlim(start, end)
    else:
        plt.xlim(0,times[-1])
    plt.ylabel('Flux (kADU)')
    plt.ylim(0,1.1*max(flux_kcounts[~objectxerr.mask]))

    ax2 = plt.gca().twinx()
    fwhm_line = ax2.plot(times[~maskall], fwhm[~maskall], 'g-',
                         alpha=0.5, drawstyle='steps-mid', label=f'FWHM ({mean_fwhm:.1f} arcsec)')
    nstars_line = ax2.plot(times, nstars, 'r-',
                         alpha=0.3, markersize=2, label=f'Nstars')
    ax2.set_yticks(np.arange(0,3.2,0.5))
    ax2.set_ylim(0,3.1)
    plt.ylabel('FWHM (arcsec)')
    plt.legend(handles=[flux_line[0], fwhm_line[0], nstars_line[0]], loc='lower center')

    log.debug(f"  Generating PSD Plot")
    plt.subplot(2,2,2)
    plt.title(f"Stellar Motion Power Spectral Distribution: FPS={fps}")
    if len(xerrs) > 0:
        plt.psd(xdeltas, Fs=fps, color='g', drawstyle='steps-mid', alpha=0.6,
                label='X F2F')
        plt.psd(ydeltas, Fs=fps, color='b', drawstyle='steps-mid', alpha=0.6,
                label='Y F2F')
        plt.legend(loc='best')
    plt.yticks([v for v in np.arange(-70,20,10)])
    plt.ylim(-70,10)
    plt.xlim(0,fps/4)


    log.debug(f"  Generating Positional Error Plot")
    plt.subplot(2,2,3)
    plt.title(f"rms={rrms:.2f} pix ({rrms*ps:.1f} mas), bias={rbias:.2f} pix ({rbias*ps:.1f} mas)")
    plt.plot(times[~objectxerr.mask], objectxerr[~objectxerr.mask], 'g-',
             alpha=0.5, drawstyle='steps-mid', label=f'Xpos-Xtarg')
    for badt in times[objectxerr.mask]:
        plt.plot([badt,badt], plotylim, 'r-', alpha=0.1)
    plt.plot(times[~objectyerr.mask], objectyerr[~objectyerr.mask], 'b-',
             alpha=0.5, drawstyle='steps-mid', label=f'Ypos-Ytarg')
    for badt in times[objectyerr.mask]:
        plt.plot([badt,badt], plotylim, 'r-', alpha=0.1)
    plt.legend(loc='best')
    plt.ylabel('delta pix')
    plt.ylim(plotylim)
    plt.grid()
    if start is not None and end is not None:
        plt.xlim(start, end)
    else:
        plt.xlim(0,times[-1])
    plt.xlabel('Time (s)')

    log.debug(f"  Generating Positional Error Histogram")
    plt.subplot(2,2,4)
#     plt.title(f"rms={rrms:.2f} pix ({rrms*ps:.1f} mas), bias={rbias:.2f} pix ({rbias*ps:.1f} mas)")
    nx, binsx, foox = plt.hist(objectxerr[~objectxerr.mask], bins=100, label='X',
                               color='g', alpha=0.6, log=True)
    ny, binsy, fooy = plt.hist(objectyerr[~objectyerr.mask], bins=100, label='Y',
                               color='b', alpha=0.3, log=True)
    maxhist = 1.1*max([max(nx), max(ny)])
    plt.plot([0,0], [0, maxhist], 'r-', alpha=0.3)
    plt.ylim(0.1, maxhist)
    plt.legend(loc='best')
    plt.xlabel('Position Error')
    plt.ylabel('N frames')

    if plotfile is not None:
        log.debug(f"  Saving Plot File")
        plt.savefig(plotfile, bbox_inches='tight', pad_inches=0.1)
        log.debug(f"  Saving Results File")
        results_file_name = plotfile.name.replace('.png', '.txt')
        results_file = plotfile.parent / results_file_name
        if results_file.exists(): results_file.unlink()
        with open(results_file, 'w') as f:
            f.write(yaml.dump(results))
    else:
        plt.show()
    log.info('Done.')


##-------------------------------------------------------------------------
## generate_cube_gif
##-------------------------------------------------------------------------
def generate_cube_gif(file, giffile):
    log.info('Generating animation')
    t, metadata, cube = read_file(file)
    if t is None: return

    start = datetime.fromisoformat(metadata['DATE-BEG'])
    end = datetime.fromisoformat(metadata['DATE-END'])
    duration = (end - start).total_seconds()
    fps = metadata['FPS']
    nf, ny, nx = cube.shape
    norm = vis.ImageNormalize(cube,
                          interval=vis.AsymmetricPercentileInterval(1.5,99.99),
                          stretch=vis.LogStretch())

    fig = plt.figure(figsize=(8,8))
    fps = 10
    if sys.platform == 'darwin':
#         writer = animation.ImageMagickWriter(fps=fps)
#         writer = animation.ImageMagickFileWriter(fps=fps)
        writer = animation.FFMpegWriter(fps=fps)
#         writer = animation.PillowWriter(fps=fps)
    else:
        writer = animation.ImageMagickWriter(fps=fps)

    # ims is a list of lists, each row is a list of artists to draw in the
    # current frame; here we are just animating one artist, the image, in
    # each frame
    log.info('Building individual frames')
    ims = []
    for j,im in enumerate(cube):
        plt.title(f"{file.name}: {duration:.1f} s, {nf:d} frames")
        im = plt.imshow(im, origin='lower', cmap='gray', norm=norm, animated=True)
        frametext = plt.text(nx-20, ny-5, f"{j:04d}/{nf:04d}", color='r')
        xtpix = nx/2
        ytpix = ny/2
        tlines = plt.plot(xtpix, ytpix, 'bx')
        lines = []
        if t[j]['object1_x'] > 0 and t[j]['object1_y'] > 0:
            xpix = t[j]['object1_x'] - (t[j]['target_x'] - nx/2)
            ypix = t[j]['object1_y'] - (t[j]['target_y'] - ny/2)
            lines = plt.plot(xpix, ypix, 'r+')
        newim = [im] + [frametext] + lines + tlines
        ims.append(newim)

    log.info('Building animation')
    ani = animation.ArtistAnimation(fig, ims, interval=1000/fps, blit=True,
                                    repeat_delay=1000)
    log.info(f'Writing {giffile} using {writer}')
    p = Path(giffile)
    if p.expanduser().exists(): p.unlink()
    ani.save(f"{giffile}", writer)
    log.info('Done')


def find_viewer_command(args):
    viewer_command = None
    if args.get('view', False) is True:
        viewer_commands = ['eog', 'open']
        for cmd in viewer_commands:
            rtn = subprocess.call(['which', cmd])
            if rtn == 0:
                viewer_command = cmd
    return viewer_command


##-------------------------------------------------------------------------
## AnalyzeTipTiltPerformance
##-------------------------------------------------------------------------
class AnalyzeTipTiltPerformance(KPFTranslatorFunction):
    '''
    ARGS:
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        viewer_command = find_viewer_command(args)
        for file in args.get('files'):
            file = Path(file).expanduser()
            if file.exists() is False:
                log.error(f"Could not find file {args.get('file')}")
            plotfile = Path(str(file.name).replace('.fits', '.png'))
            plot_tiptilt_stats(file, plotfile=plotfile,
                               start=args.get('start', None),
                               end=args.get('end', None),
                               )

            if viewer_command is not None:
                log.info(f"Opening {plotfile} using {viewer_command}")
                proc = subprocess.Popen([viewer_command, f"{plotfile}"])

            if args.get('gif') is True:
                giffile = Path(str(file.name).replace('.fits', '.gif'))
                generate_cube_gif(file, giffile)

                if viewer_command is not None:
                    log.info(f"Opening {giffile} using {viewer_command}")
                    proc = subprocess.Popen([viewer_command, f"{giffile}"])

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('files', type=str, nargs='*',
            help="The FITS files to analyze")
        parser.add_argument("-g", "--gif", dest="gif",
            default=False, action="store_true",
            help="Generate the animated GIF of frames (computationally expensive)")
        parser.add_argument("--view", dest="view",
            default=False, action="store_true",
            help="Open a viewer once the file is generated")
        parser.add_argument("--start", dest="start", type=float,
            help="Zoom the plot in to this start time (in seconds).")
        parser.add_argument("--end", dest="end", type=float,
            help="Zoom the plot in to this end time (in seconds).")
        return super().add_cmdline_args(parser, cfg)


##-------------------------------------------------------------------------
## if __name__ == '__main__':
##-------------------------------------------------------------------------
if __name__ == '__main__':
    ##-------------------------------------------------------------------------
    ## Parse Command Line Arguments
    ##-------------------------------------------------------------------------
    ## create a parser object for understanding command-line arguments
    import argparse
    p = argparse.ArgumentParser(description='''
    ''')
    ## add arguments
    p.add_argument('files', type=str, nargs='*',
                   help="The FITS files to analyze")
    p.add_argument("-g", "--gif", dest="gif",
        default=False, action="store_true",
        help="Generate the animated GIF of frames (computationally expensive)")
    p.add_argument("--view", dest="view",
        default=False, action="store_true",
        help="Open a viewer once the file is generated")
    p.add_argument("--start", dest="start", type=float,
        help="Zoom the plot in to this start time (in seconds).")
    p.add_argument("--end", dest="end", type=float,
        help="Zoom the plot in to this end time (in seconds).")
    args = p.parse_args()

    viewer_command = find_viewer_command(args)
    for file in args.files:
        file = Path(file).expanduser()
        if file.exists() is False:
            log.error(f"Could not find file {args.file}")
        plotfile = Path(str(file.name).replace('.fits', '.png'))
        plot_tiptilt_stats(file, plotfile=plotfile)

        if viewer_command is not None:
            log.info(f"Opening {plotfile} using {viewer_command}")
            proc = subprocess.Popen([viewer_command, f"{plotfile}"])

        if args.gif is True:
            giffile = Path(str(file.name).replace('.fits', '.gif'))
            generate_cube_gif(file, giffile)

            if viewer_command is not None:
                log.info(f"Opening {giffile} using {viewer_command}")
                proc = subprocess.Popen([viewer_command, f"{giffile}"])
