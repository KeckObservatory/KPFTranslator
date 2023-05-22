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
from astropy import nddata
from astropy.table import Table, Column
from astropy import visualization as vis
from astropy.modeling import models, fitting
import sep

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
LogConsoleHandler.setLevel(logging.DEBUG)
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
            guider_cube = nddata.CCDData(hdu.data, unit='adu')
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


def add_parameters(t):
    n_frames = len(t)
    coef = 2*np.sqrt(2*np.log(2))
    for obj in [1,2,3]:
        good = np.where(t[f'object{obj}_x'] > -998)[0]
        # FWHM
        fwhm = np.zeros(len(t))
        fwhm[good] = np.sqrt((coef*t[f'object{obj}_a'][good])**2 + (coef*t[f'object{obj}_b'][good])**2)
        t.add_column(Column(data=fwhm.data, name=f'object{obj}_fwhm', dtype=float))
        # ellipticity
        ellipticities = np.zeros(len(t))
        ellipticities[good] = t[f'object{obj}_a'][good]/t[f'object{obj}_b'][good]
        t.add_column(Column(data=ellipticities.data, name=f'object{obj}_ellipticity', dtype=float))

    # Count frames with no stars
    nostars = t[t['object1_x'] < -998]
    n_no_stars = len(nostars)
    frac_no_stars = n_no_stars / n_frames
    log.info(f"  {n_no_stars}/{n_frames} frames have no detected stars ({frac_no_stars:.1%})")

    # Count frames with multiple stars
    multiple_stars = t[t['object2_x'] > -998]
    n_multiple_stars = len(multiple_stars)
    frac_multiple = n_multiple_stars/n_frames
    log.info(f"  {n_multiple_stars}/{n_frames} frames have multiple stars ({frac_multiple:.1%})")

    return t, n_no_stars, n_multiple_stars, n_frames


##-------------------------------------------------------------------------
## plot_tiptilt_stats
##-------------------------------------------------------------------------
def plot_tiptilt_stats(file, plotfile=None, start=None, end=None,
                       snr=None, minarea=None,
                       deblend_nthresh=None, deblend_cont=None):
    results = {'file': f"{file}"}
    ps = 56 # mas/pix
    log.info(f'Reading file: {file}')
    t, metadata, cube = read_file(file)
    # If requested, run additional SEP
    new = None
    if snr or minarea or deblend_nthresh or deblend_cont:
        if cube is not None:
            log.info('Running Source Extractor on cube with new parameters')
            new = run_new_sep_parameters(cube, t, snr=snr, minarea=minarea,
                                         deblend_nthresh=deblend_nthresh,
                                         deblend_cont=deblend_cont)

    if t is None: return
    log.info('Adding calculated parameters')
    t, n_no_stars, n_multiple_stars, n_frames = add_parameters(t)
    if new is not None:
        log.info('Adding calculated parameters to new source extractor table')
        new, new_n_no_stars, new_n_multiple_stars, n_frames = add_parameters(new)
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
    fwhm = t['object1_fwhm']*ps/1000
    mean_fwhm = np.mean(fwhm)

    results['FWHM (arcsec)'] = float(mean_fwhm)

    # Mean Flux
    mean_flux = np.nanmean(t['object1_flux'][~maskall])
    mean_peak = np.nanmean(t['object1_peak'][~maskall])

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
    w_extra_detections = np.where(nstars > median_nstars)[0]
    nframes_extra_detections = len(w_extra_detections)
    w_fewer_detections = np.where(nstars < median_nstars)[0]
    nframes_fewer_detections = len(w_fewer_detections)

    results['Nframes'] = int(len(nstars))
    results['Median Nstars'] = int(median_nstars)
    results['Nframes extra detections'] = int(nframes_extra_detections)
    results['Nframes fewer detections'] = int(nframes_fewer_detections)

    plt.figure(figsize=(16,12))

    # Flux and Peak Plot
    log.debug(f"  Generating Flux Plot")
    plt.subplot(3,2,1)
    title_line1 = f"{len(t)} frames: {nframes_extra_detections} frames w/ extra stars, {nframes_fewer_detections} frames w/ fewer"
    title_line2 = ''
    if metadata['Gmag'] is not None:
        title_line2 += f"{targname}: Gmag={Gmag}, Jmag={Jmag}, FWHM={mean_fwhm:.2f}"
    plt.title(f"{title_line1}\n{title_line2}")
    plt.fill_between([0, times[-1]], [0,0], [5000,5000],
                     color='r', alpha=0.2, linewidth=0)
    plt.fill_between([0, times[-1]], [5000,5000], [10000,10000],
                     color='y', alpha=0.2, linewidth=0)
    try:
        flux_plot_max = 1.1*max(t['object1_flux'][~maskall])
    except ValueError:
        flux_plot_max = 20000
    for instance in w_extra_detections:
        plt.plot([times[instance], times[instance]], [0,flux_plot_max], 'r-', alpha=0.05)
    for instance in w_fewer_detections:
        plt.plot([times[instance], times[instance]], [0,flux_plot_max], 'b-', alpha=0.05)
    flux_line = plt.plot(times[~maskall],
                         t['object1_flux'][~maskall],
                         'k-', alpha=0.5, drawstyle='steps-mid',
                         label=f'flux ({mean_flux:.1e})')
    if start is not None and end is not None:
        plt.xlim(start, end)
    else:
        plt.xlim(0,times[-1])
    plt.ylabel('Flux (ADU)')
    plt.ylim(0,flux_plot_max)

    ax_peak = plt.gca().twinx()
    peak_line = ax_peak.plot(times[~maskall],
                             t['object1_peak'][~maskall],
                             'g-', alpha=0.3, drawstyle='steps-mid',
                             label=f'peak ({mean_peak:.1e})')
    plt.ylabel('Peak (ADU)')
    plt.legend(handles=[flux_line[0], peak_line[0]], loc='lower center')

    # FWHM Plot
    plt.subplot(3,2,2)
    log.debug('Generating FWHM Plot')
    log.debug(f"  Mean FWHM = {mean_fwhm:.1f} arcsec")
    fwhm_line = plt.plot(times[~maskall], fwhm[~maskall], 'k-',
                         alpha=0.5, drawstyle='steps-mid',
                         label=f'FWHM ({mean_fwhm:.1f} arcsec)')
    if new is not None:
        newfwhm = new['object1_fwhm']*ps/1000
        newmean_fwhm = np.mean(fwhm)
        log.debug(f"  Mean New FWHM = {newmean_fwhm:.1f} arcsec")
        newfwhm_line = plt.plot(times[~maskall], newfwhm[~maskall], 'g-',
                                alpha=0.5, drawstyle='steps-mid',
                                label=f'new FWHM ({newmean_fwhm:.1f} arcsec)')
        plt.legend(handles=[fwhm_line[0], newfwhm_line[0]], loc='best')
    else:
        plt.legend(loc='best')
    if start is not None and end is not None:
        plt.xlim(start, end)
    else:
        plt.xlim(0,times[-1])
    plt.yticks(np.arange(0,3.2,0.5))
    plt.ylim(0,1.6)
    plt.ylabel('FWHM (arcsec)')

    # Re-analysis Flux and Peak
    if new is not None:
        log.debug(f"  Generating Flux Plot for New Source Extractor Results")
        plt.subplot(3,2,3)

        maskx = new['object1_x']<-998
        masky = new['object1_y']<-998
        maskall = maskx | masky

        # Count number of stars
        nstars = []
        for entry in new:
            star_count = 0
            for i in [1,2,3]:
                if entry[f'object{i}_x'] > -998:
                    star_count +=1
            nstars.append(star_count)
        nstars = np.array(nstars, dtype=int)
        median_nstars = int(np.median(nstars))
        w_extra_detections = np.where(nstars > median_nstars)[0]
        nframes_extra_detections = len(w_extra_detections)
        w_fewer_detections = np.where(nstars < median_nstars)[0]
        nframes_fewer_detections = len(w_fewer_detections)

        title_line1_parts = []
        if snr is not None: title_line1_parts.append(f"snr={snr:.0f}")
        if minarea is not None: title_line1_parts.append(f"minarea={minarea:.0f}")
        if deblend_nthresh is not None: title_line1_parts.append(f"deblend_nthresh={deblend_nthresh:.0f}")
        if deblend_cont is not None: title_line1_parts.append(f"deblend_cont={deblend_cont:.2f}")
        title_line1 = ",".join(title_line1_parts)
        title_line2 = f"{len(t)} frames: {nframes_extra_detections} frames w/ extra stars, {nframes_fewer_detections} frames w/ fewer"
        plt.title(f"{title_line1}\n{title_line2}")
        mean_flux = np.nanmean(new['object1_flux'][~maskall])
        mean_peak = np.nanmean(new['object1_peak'][~maskall])
        plt.fill_between([0, times[-1]], [0,0], [5000,5000],
                         color='r', alpha=0.2, linewidth=0)
        plt.fill_between([0, times[-1]], [5000,5000], [10000,10000],
                         color='y', alpha=0.2, linewidth=0)
        for instance in w_extra_detections:
            plt.plot([times[instance], times[instance]], [0,flux_plot_max], 'r-', alpha=0.05)
        for instance in w_fewer_detections:
            plt.plot([times[instance], times[instance]], [0,flux_plot_max], 'b-', alpha=0.05)
        flux_line = plt.plot(times[~maskall],
                             new['object1_flux'][~maskall],
                             'k-', alpha=0.5, drawstyle='steps-mid',
                             label=f'flux ({mean_flux:.1e})')
        if start is not None and end is not None:
            plt.xlim(start, end)
        else:
            plt.xlim(0,times[-1])
        plt.ylabel('Flux (ADU)')

        try:
            new_flux_plot_max = 1.1*max(new['object1_flux'][~maskall])
            if max(new['object1_flux'][~maskall]) > flux_plot_max:
                flux_plot_max = 1.1*max(new['object1_flux'][~maskall])
        except ValueError:
            pass
        plt.ylim(0,flux_plot_max)
        ax_peak = plt.gca().twinx()
        peak_line = ax_peak.plot(times[~maskall],
                                 new['object1_peak'][~maskall],
                                 'g-', alpha=0.3, drawstyle='steps-mid',
                                 label=f'peak ({mean_peak:.1e})')
        plt.ylabel('Peak (ADU)')
        plt.legend(handles=[flux_line[0], peak_line[0]], loc='lower center')


    # Position Error Plot
    log.debug(f"  Generating Positional Error Plot")
    plt.subplot(3,2,5)
    plt.title(f"rms={rrms:.2f} pix ({rrms*ps:.1f} mas), bias={rbias:.2f} pix ({rbias*ps:.1f} mas)")
    plt.plot(times[~maskall], objectxerr[~maskall], 'g-',
             alpha=0.5, drawstyle='steps-mid', label=f'Xpos-Xtarg')
    for badt in times[maskall]:
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

    # PSD Plot
    log.debug(f"  Generating PSD Plot")
    plt.subplot(3,2,4)
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

    # Position Error Histogram
    log.debug(f"  Generating Positional Error Histogram")
    plt.subplot(3,2,6)
#     plt.title(f"rms={rrms:.2f} pix ({rrms*ps:.1f} mas), bias={rbias:.2f} pix ({rbias*ps:.1f} mas)")
    nx, binsx, foox = plt.hist(objectxerr[~maskall], bins=100, label='X',
                               color='g', alpha=0.6, log=True)
    ny, binsy, fooy = plt.hist(objectyerr[~objectyerr.mask], bins=100, label='Y',
                               color='b', alpha=0.3, log=True)
    maxhist = 1.1*max([max(nx), max(ny)])
    plt.plot([0,0], [0, maxhist], 'r-', alpha=0.3)
    plt.ylim(0.5, max([maxhist,1]))
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


def run_new_sep_parameters(cube, original, snr=5, minarea=50, binning=1,
                           deblend_nthresh=32, deblend_cont=0.005):
    if snr is None: snr = 5
    if minarea is None: minarea = 50
    if deblend_nthresh is None: deblend_nthresh = 32
    if deblend_cont is None: deblend_cont = 0.005
    if binning is None: binning = 1

    new = Table(names=original.keys(), dtype=original.dtype)
    subframes = []
    objectids = []
    objectcount = []
    background_rms = []
    target_x = []
    target_y = []
    plotcount = 0
    n_no_stars = 0
    for s,subframe in enumerate(cube.data):
        subframe = nddata.block_reduce(subframe, binning)
        subframe = np.array(subframe, dtype=float)
        # Default background parameters: bw=64, bh=64, fw=3, fh=3, fthresh=0.0
        background = sep.Background(subframe)
        subtracted = subframe - background
        objects = sep.extract(subtracted, snr, minarea=minarea,
                              err=background.globalrms,
                              deblend_nthresh=deblend_nthresh, # default is 32
                              deblend_cont=deblend_cont,
                              # Minimum contrast ratio used for object deblending.
                              # Default is 0.005. To entirely disable deblending, set to 1.0.
                              )
        objects = Table(objects)
        sep_result = {'subframe_id': s}
        if len(objects) > 0:
            sep_result['object1_flux'] = objects[0]['flux']
            sep_result['object1_tnpix'] = objects[0]['tnpix']
            sep_result['object1_npix'] = objects[0]['npix']
            sep_result['object1_peak'] = objects[0]['peak']
            sep_result['object1_x'] = objects[0]['x']
            sep_result['object1_y'] = objects[0]['y']
            sep_result['object1_a'] = objects[0]['a']
            sep_result['object1_b'] = objects[0]['b']
            sep_result['object1_theta'] = objects[0]['theta']
            sep_result['object1_errxy'] = objects[0]['errxy']
            sep_result['object1_thresh'] = objects[0]['thresh']
        else:
            sep_result['object1_flux'] = -999
            sep_result['object1_tnpix'] = -999
            sep_result['object1_npix'] = -999
            sep_result['object1_peak'] = -999
            sep_result['object1_x'] = -999
            sep_result['object1_y'] = -999
            sep_result['object1_a'] = -999
            sep_result['object1_b'] = -999
            sep_result['object1_theta'] = -999
            sep_result['object1_errxy'] = -999
            sep_result['object1_thresh'] = -999
        if len(objects) > 1:
            sep_result['object2_flux'] = objects[1]['flux']
            sep_result['object2_tnpix'] = objects[1]['tnpix']
            sep_result['object2_npix'] = objects[1]['npix']
            sep_result['object2_peak'] = objects[1]['peak']
            sep_result['object2_x'] = objects[1]['x']
            sep_result['object2_y'] = objects[1]['y']
            sep_result['object2_a'] = objects[1]['a']
            sep_result['object2_b'] = objects[1]['b']
            sep_result['object2_theta'] = objects[1]['theta']
            sep_result['object2_errxy'] = objects[1]['errxy']
            sep_result['object2_thresh'] = objects[1]['thresh']
        else:
            sep_result['object2_flux'] = -999
            sep_result['object2_tnpix'] = -999
            sep_result['object2_npix'] = -999
            sep_result['object2_peak'] = -999
            sep_result['object2_x'] = -999
            sep_result['object2_y'] = -999
            sep_result['object2_a'] = -999
            sep_result['object2_b'] = -999
            sep_result['object2_theta'] = -999
            sep_result['object2_errxy'] = -999
            sep_result['object2_thresh'] = -999
        if len(objects) > 2:
            sep_result['object3_flux'] = objects[2]['flux']
            sep_result['object3_tnpix'] = objects[2]['tnpix']
            sep_result['object3_npix'] = objects[2]['npix']
            sep_result['object3_peak'] = objects[2]['peak']
            sep_result['object3_x'] = objects[2]['x']
            sep_result['object3_y'] = objects[2]['y']
            sep_result['object3_a'] = objects[2]['a']
            sep_result['object3_b'] = objects[2]['b']
            sep_result['object3_theta'] = objects[2]['theta']
            sep_result['object3_errxy'] = objects[2]['errxy']
            sep_result['object3_thresh'] = objects[2]['thresh']
        else:
            sep_result['object3_flux'] = -999
            sep_result['object3_tnpix'] = -999
            sep_result['object3_npix'] = -999
            sep_result['object3_peak'] = -999
            sep_result['object3_x'] = -999
            sep_result['object3_y'] = -999
            sep_result['object3_a'] = -999
            sep_result['object3_b'] = -999
            sep_result['object3_theta'] = -999
            sep_result['object3_errxy'] = -999
            sep_result['object3_thresh'] = -999
        new.add_row(sep_result)

    return new


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
                               snr=args.get('snr', None),
                               minarea=args.get('minarea', None),
                               deblend_nthresh=args.get('deblend_nthresh', None),
                               deblend_cont=args.get('deblend_cont', None),
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
        parser.add_argument("--snr", dest="snr", type=float,
            help="Run source extractor again with this SNR threshold")
        parser.add_argument("--minarea", dest="minarea", type=float,
            help="Run source extractor again with this minarea parameter")
        parser.add_argument("--deblend_nthresh", dest="deblend_nthresh", type=float,
            help="Run source extractor again with this deblend_nthresh")
        parser.add_argument("--deblend_cont", dest="deblend_cont", type=float,
            help="Run source extractor again with this deblend_cont parameter")
        return super().add_cmdline_args(parser, cfg)
