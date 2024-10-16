#!python3

## Import General Tools
from pathlib import Path
import logging
import re

from pathlib import Path
import numpy as np
import astropy
from astropy.io import fits
from astropy import visualization as viz
from astropy.table import Table, Column
from astropy.nddata import CCDData
from astropy.modeling import models, fitting

import warnings
warnings.filterwarnings('ignore', category=astropy.wcs.FITSFixedWarning, append=True)

from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator, FixedLocator

from kpf.KPFTranslatorFunction import KPFTranslatorFunction


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
log = logging.getLogger('MyLogger')
log.setLevel(logging.DEBUG)
## Set up console output
LogConsoleHandler = logging.StreamHandler()
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


##-----------------------------------------------------------------------------
## Function: mode
##-----------------------------------------------------------------------------
def mode(data):
    '''
    Return mode of image.  Assumes int values (ADU), so uses binsize of one.
    '''
    bmin = np.floor(min(data.ravel())) - 1./2.
    bmax = np.ceil(max(data.ravel())) + 1./2.
    bins = np.arange(bmin,bmax,1)
    hist, bins = np.histogram(data.ravel(), bins=bins)
    centers = (bins[:-1] + bins[1:]) / 2
    w = np.argmax(hist)
    mode = int(centers[w])
    return mode


def parse_CRED2_image_header(cred2_file):
    cred2_image_filename = Path(cred2_file).name
    hdul = fits.open(cred2_file)
    EL = float(hdul[0].header.get("EL"))
    va = np.arctan(hdul[0].header.get("CD1_1Y")/hdul[0].header.get("CD1_2Y"))*180/np.pi + 90
    return EL, va




##-------------------------------------------------------------------------
## build_FITS_cube
##-------------------------------------------------------------------------
def build_FITS_cube(images, comment, ouput_spec_cube, mode='TipTilt',
                    dar_offset=None):
    nx = len(set(images['x']))
    ny = len(set(images['y']))
    xs = sorted(set(images['x']))
    ys = sorted(set(images['y']))

    # Figure out of the table contains the filename for the 1D extracted spectra
    nexpmeter = len(images[images['camera'] == 'ExpMeter'])
    n1dspec = len(images[images['camera'] == 'ExpMeter_1Dspec'])
    onedspecfiles = (n1dspec >= nexpmeter)
    camname = {True: 'ExpMeter_1Dspec', False: 'ExpMeter'}[onedspecfiles]

    wavs = None
    nspectra = len(images[images['camera'] == camname])
    log.info(f'Building FITS cube using {nspectra} spectra')
    vas = []
    ELs = []
    for entry in images[images['camera'] == camname]:
        i = xs.index(entry['x'])
        j = ys.index(entry['y'])
        this_grid_pos = images[np.isclose(images['x'], entry['x']) & np.isclose(images['y'], entry['y'])]
        cred2_file = this_grid_pos[this_grid_pos['camera'] == 'CRED2']['file'][0]
        EL, va = parse_CRED2_image_header(cred2_file)
        ELs.append(EL)
        vas.append(va)
        Xpix = entry['x']
        Ypix = entry['y']

        # Figure out the 1d extracted exposure meter file if not recorded
        if onedspecfiles is False:
            p = Path(entry['file'])
            ismatch = re.search('(kpf_em_\d+)\.\d{3}\.fits', p.name)
            if ismatch:
                specfile = p.parent / f"{ismatch.groups(1)[0]}.fits"
            else:
                print(f'Failed Match: {p}')
        else:
            onedspecfile = Path(entry['file'])

        # If this is first file, pull the wavelengths out
        hdul = fits.open(onedspecfile)
        onedspec_table = Table(hdul[1].data)
        if wavs is None:
            wavs_strings = [k for k in onedspec_table.keys() if re.match('[\d\.]+', k.strip()) is not None]
            wavs = [float(k) for k in wavs_strings]
            dwav = [wav-wavs[i-1] for i,wav in enumerate(wavs) if i>0]
            nwav = len(wavs)
            spec_cube = np.zeros((nwav,ny,nx))
            posdata = np.zeros((8,ny,nx))
            index_450nm = np.argmin([abs(w-450) for w in wavs])
            index_550nm = np.argmin([abs(w-550) for w in wavs])
            index_650nm = np.argmin([abs(w-650) for w in wavs])

        all_EM_spectra = np.zeros((len(onedspec_table), nwav), dtype=float)
        individual_EM_fluxes = np.zeros(len(onedspec_table), dtype=float)
        for lineno,line in enumerate(onedspec_table):
            fluxes = np.array([float(line[key]) for key in wavs_strings])
            all_EM_spectra[lineno,:] = fluxes
            individual_EM_fluxes[lineno] = fluxes.sum()

        if len(onedspec_table) <= 4:
            log.warning(f'Number of EM spectra is low: {len(onedspec_table)}')
            mean_EM_spectrum = all_EM_spectra.mean(axis=0)
            std_of_EM_spectra = all_EM_spectra.std(axis=0)
            mean_of_EM_fluxes = individual_EM_fluxes.mean()
            std_of_EM_fluxes = individual_EM_fluxes.std()
        else:
            # Drop first and last
            mean_EM_spectrum = all_EM_spectra[1:-1,:].mean(axis=0)
            std_of_EM_spectra = all_EM_spectra[1:-1,:].std(axis=0)
            mean_of_EM_fluxes = individual_EM_fluxes[1:-1].mean()
            std_of_EM_fluxes = individual_EM_fluxes[1:-1].std()
        spec_cube[:,j,i] = np.array(mean_EM_spectrum)
        posdata[0,j,i] = Xpix
        posdata[1,j,i] = Ypix
        posdata[2,j,i] = entry['x']
        posdata[3,j,i] = entry['y']
        posdata[4,j,i] = 1 if np.isnan(mean_of_EM_fluxes) else mean_of_EM_fluxes
        posdata[5,j,i] = 0 if np.isnan(std_of_EM_fluxes) else std_of_EM_fluxes
        posdata[6,j,i] = mean_of_EM_fluxes/std_of_EM_fluxes if std_of_EM_fluxes > 0 else 0
        posdata[7,j,i] = len(onedspec_table)

    va = np.mean(vas)
    log.info(f"Mean VA = {va:.1f} deg")
    EL = np.mean(ELs)
    log.info(f"Mean EL = {EL:.1f} deg")
    norm_spec_cube = np.zeros((nwav,ny,nx))
    for w,spectral_slice in enumerate(spec_cube):
        norm_spec_cube[w,:,:] = spectral_slice / spectral_slice.mean()

    flux_map = np.sum(spec_cube, axis=0) / np.sum(spec_cube, axis=0).max()

    fluxcubehdu = fits.ImageHDU()
    fluxcubehdu.header.set('Name', 'Three_Color_Cube')
    fluxcubehdu.header.set('OBJECT', 'Three_Color_Cube')
    wavs = np.array(wavs)
    delta_w = 20
    wavbin_centers = np.arange(470,830,2*delta_w)
    color_images = np.zeros((len(wavbin_centers),ny,nx))
    for widx,wav_center in enumerate(wavbin_centers):
        w = np.where((wavs > wav_center-delta_w) & (wavs < wav_center+delta_w))[0]
        color_images[widx,:,:] = np.sum(spec_cube[w,:,:], axis=0)
        flux = np.sum(color_images[widx,:,:])
        log.info(f"  For {wav_center} nm, found {len(w)} bins with {flux:.1e} counts")
        fluxcubehdu.header.set(f'Layer{widx+1}', f'{wavbin_centers[widx]}nm')

    color_cube = np.zeros((2,ny,nx))
    color_cube[0,:,:] = color_images[0,:,:]/color_images[1,:,:]
    color_cube[1,:,:] = color_images[2,:,:]/color_images[1,:,:]

    hdu = fits.PrimaryHDU()
    hdu.header.set('Name', 'Spectral_Cube')
    hdu.header.set('OBJECT', 'Spectral_Cube')
    hdu.header.set('Comment', comment)
    hdu.header.set('VA', va, 'Mean Vertical Angle of input images')
    hdu.header.set('EL', EL, 'Mean Elevation of input images')
    hdu.header.set('DAROFF_X', dar_offset[0], 'DAR_OFFSET in X')
    hdu.header.set('DAROFF_Y', dar_offset[1], 'DAR_OFFSET in Y')
    hdu.data = spec_cube
    normcubehdu = fits.ImageHDU()
    normcubehdu.header.set('Name', 'Normalized_Spectral_Cube')
    normcubehdu.header.set('OBJECT', 'Normalized_Spectral_Cube')
    normcubehdu.data = norm_spec_cube
    fluxmaphdu = fits.ImageHDU()
    fluxmaphdu.header.set('Name', 'Normalized_Flux_Map')
    fluxmaphdu.header.set('OBJECT', 'Normalized_Flux_Map')
    fluxmaphdu.data = flux_map
    fluxcubehdu.data = color_images
    colormaphdu = fits.ImageHDU()
    colormaphdu.header.set('Name', 'Color_Map_Ratios')
    colormaphdu.header.set('OBJECT', 'Color_Map_Ratios')
    colormaphdu.header.set('Layer1', '450nm/550nm')
    colormaphdu.header.set('Layer2', '650nm/550nm')
    colormaphdu.data = color_cube
    poshdu = fits.ImageHDU()
    poshdu.header.set('Name', 'Spatial_Positions')
    poshdu.header.set('OBJECT', 'Spatial_Positions')
    poshdu.header.set('Comment', '1 X pixel')
    poshdu.header.set('Comment', '2 Y pixel')
    poshdu.header.set('Comment', '3 X pixel, original')
    poshdu.header.set('Comment', '4 Y pixel, original')
    poshdu.header.set('Comment', '5 mean flux map')
    poshdu.header.set('Comment', '6 StdDev map')
    poshdu.header.set('Comment', '7 SNR map')
    poshdu.header.set('Comment', '8 Number of EM exposures map')
    poshdu.data = posdata
    wavhdu = fits.ImageHDU()
    wavhdu.header.set('Name', 'Wavelength_Values')
    wavhdu.header.set('OBJECT', 'Wavelength_Values')
    wavhdu.data = np.array(wavs)
    hdul = fits.HDUList([hdu, normcubehdu, fluxmaphdu, fluxcubehdu, colormaphdu, poshdu, wavhdu])
    log.info(f'  Writing FITS cube {ouput_spec_cube}')
    hdul.writeto(f'{ouput_spec_cube}', overwrite=True)
    return hdul


##-------------------------------------------------------------------------
## build_cube_graphic
##-------------------------------------------------------------------------
def build_cube_graphic(hdul, ouput_cube_graphic, mode=mode,
                       model='Fiber Coupling Model seeing 0.70 arcsec.csv',
                       xfit=None, yfit=None):
    log.info(f"Building cube graphic")
    if mode == 'TipTilt':
        # Build Coupling Model
        # Uses data from Steve Gibson
        this_location = Path(__file__).parent
        model_file = this_location / Path(model)
        t = Table.read(f"{model_file}", format='ascii.csv')
        pix_scale = 0.058
        model_pix = np.array(t['Fiber_offset_arcsec'])/pix_scale
        model_flux = np.array(t['Percent_thru'])/max(t['Percent_thru'])
        fit0 = models.Polynomial1D(degree=4)
        fitter = fitting.LinearLSQFitter()
        fit = fitter(fit0, model_pix, model_flux)

    # Build Plots from on sky data
    va = hdul[0].header.get('VA')
    flux_map = hdul[5].data[4]
    color_maps = hdul[3].data
    color_maps_colors = [hdul[3].header.get(f"Layer{i}") for i in [1,2,3]]
    snr_map = hdul[5].data[6]
    emcount_map = hdul[5].data[7]
    nlayers, ny, nx = hdul[5].data.shape
    nplots = ny if nx > ny else nx
    plot_axis_name = 'X' if nx > ny else 'Y'
    xplot_values = hdul[5].data[0][0,:] if nx > ny else hdul[5].data[1][:,0]
    xplot_strings = [f"{val:.1f}" for val in xplot_values]
    iterated_pix_values = hdul[5].data[1][:,0] if nx > ny else hdul[5].data[0][0,:]
    iterated_pix_strings = [f"{val:.1f}" for val in iterated_pix_values]
    iterated_axis_name = 'Y' if nx > ny else 'X'
    log.info(f"  Plots will be cuts across {plot_axis_name} axis")

    plt.figure(figsize=(15,15))

    plt.subplot(3,1,1)
    norm = viz.ImageNormalize(flux_map,
                              interval=viz.MinMaxInterval(),
                              stretch=viz.LinearStretch())
    plt.title(f'Flux Map: fiber at {xfit:.1f} {yfit:.1f}')
    plt.imshow(flux_map, interpolation='none', cmap='gray', origin='lower', norm=norm)
    plt.xlabel(f"X pixels")
    plt.ylabel(f"Y pixels")
    xplot_ticks = [i for i in range(len(xplot_strings))]
    iterated_pix_ticks = [i for i in range(len(iterated_pix_strings))]
    if plot_axis_name == 'X':
        plt.gca().set_yticks(iterated_pix_ticks)
        plt.gca().set_yticklabels(iterated_pix_strings)
        plt.gca().set_xticks(xplot_ticks)
        plt.gca().set_xticklabels(xplot_strings)
    else:
        plt.gca().set_xticks(iterated_pix_ticks)
        plt.gca().set_xticklabels(iterated_pix_strings)
        plt.gca().set_yticks(xplot_ticks)
        plt.gca().set_yticklabels(xplot_strings)

    if xfit is not None and yfit is not None:
        arrow_length = 0.5
        if plot_axis_name == 'X':
            xifit = np.interp(xfit, xplot_values, xplot_ticks)
            yifit = np.interp(yfit, iterated_pix_values, iterated_pix_ticks)
            log.info(f"Overplotting {xfit:.1f} {yfit:.1f} as {xifit:.1f} {yifit:.1f}")
            if xfit > min(xplot_values)-0.5 and xfit < max(xplot_values)+0.5:
                plt.plot([xifit]*2, [min(iterated_pix_ticks)-0.5, max(iterated_pix_ticks)+0.5], 'r-', alpha=0.2)
            if yfit > min(iterated_pix_values)-0.5 and yfit < max(iterated_pix_values)+0.5:
                plt.plot([min(iterated_pix_ticks)-0.5, max(iterated_pix_ticks)+0.5], [yifit]*2, 'r-', alpha=0.2)
            arrow_dx = -arrow_length*np.cos((va-90)*np.pi/180)
            arrow_dy = -arrow_length*np.sin((va-90)*np.pi/180)
            plt.arrow(xifit, yifit, arrow_dx, arrow_dy,
                      head_width=arrow_length/5, color='r')

        else:
            xifit = np.interp(xfit, iterated_pix_values, iterated_pix_ticks)
            yifit = np.interp(yfit, xplot_values, xplot_ticks)
            log.info(f"Overplotting {xfit:.1f} {yfit:.1f} as {xifit:.1f} {yifit:.1f}")
            if xfit > min(iterated_pix_values)-0.5 and xfit < max(iterated_pix_values)+0.5:
                plt.plot([xifit]*2, [min(iterated_pix_ticks)-0.5, max(iterated_pix_ticks)+0.5], 'r-', alpha=0.2)
            if yfit > min(xplot_values)-0.5 and yfit < max(xplot_values)+0.5:
                plt.plot([min(iterated_pix_ticks)-0.5, max(iterated_pix_ticks)+0.5], [yifit]*2, 'r-', alpha=0.2)
            arrow_dx = -arrow_length*np.cos((va-90)*np.pi/180)
            arrow_dy = -arrow_length*np.sin((va-90)*np.pi/180)
            plt.arrow(xifit, yifit, arrow_dx, arrow_dy,
                      head_width=arrow_length/5, color='b')


    ax1 = plt.subplot(3,1,2)
    ax1.set_xticks(xplot_values)
    ax1.set_xticklabels(xplot_strings)
    plt.ylim(0,flux_map.max()*1.15)
    xpmin = xplot_values.min()
    xpmax = xplot_values.max()
    xlim = (xpmin-(xpmax-xpmin)*0.04,
            xpmax+(xpmax-xpmin)*0.04)
    plt.xlim(xlim)
    plt.ylabel('Flux')

    ax2 = plt.subplot(3,1,3)
    ax2.set_xticks(xplot_values)
    ax2.set_xticklabels(xplot_strings)
    plt.ylim(0,flux_map.max()*1.15)
    xpmin = xplot_values.min()
    xpmax = xplot_values.max()
    xlim = (xpmin-(xpmax-xpmin)*0.04,
            xpmax+(xpmax-xpmin)*0.04)
    plt.xlim(xlim)
    plt.ylabel('Flux')

    for i in range(nplots):
        iterated_pix_value = iterated_pix_values[i]
        if plot_axis_name == 'X':
            flux_map_i = flux_map[i,:]
            color_maps_i = color_maps[:,i,:]
            snr_map_i = snr_map[i,:]
            emcount_map_i = emcount_map[i,:]
        else:
            flux_map_i = flux_map[:,i]
            color_maps_i = color_maps[:,:,i]
            snr_map_i = snr_map[:,i]
            emcount_map_i = emcount_map[:,i]
        if i == 0:
            line = ax1.plot(xplot_values, flux_map_i,
                     marker='o', color='k', ds='steps-mid', alpha=1,
                     label=f'Flux {iterated_axis_name}={iterated_pix_value:.1f}')

        if nplots == 1:
            markers = {0: 'bx-', 1: 'g^-', 2: 'r+-'}
            for l in [0,1,2]:
                color_maps_il = color_maps_i[l,:]
                color_maps_il /= color_maps_il.max()
                color_maps_il *= flux_map_i.max()
                lineb = ax2.plot(xplot_values, color_maps_il, f"{markers[l]}",
                                 ds='steps-mid', alpha=0.5,
                                 label=f"{color_maps_colors[l]}")

        peak_index = np.argmax(flux_map_i)
        if mode == 'TipTilt':
            if plot_axis_name == 'X':
                if xfit == None:
                    model_center = xplot_values[peak_index]
                else:
                    model_center = xfit
            elif plot_axis_name == 'Y':
                if yfit == None:
                    model_center = xplot_values[peak_index]
                else:
                    model_center = yfit
            ax1.plot(model_pix+model_center, fit(model_pix)*flux_map_i[peak_index],
                     color=line[0].get_c(), linestyle=':', alpha=0.7,
                     label=f'Model, center={model_center:.1f}')
            ax1.plot(model_pix+model_center, fit(model_pix+1)*flux_map_i[peak_index],
                     color=line[0].get_c(), linestyle=':', alpha=0.3)
            ax1.plot(model_pix+model_center, fit(model_pix-1)*flux_map_i[peak_index],
                     color=line[0].get_c(), linestyle=':', alpha=0.3)

            if nplots == 1:
                ax2.plot(model_pix+model_center, fit(model_pix)*flux_map_i[peak_index],
                         color=line[0].get_c(), linestyle=':', alpha=0.7,
                         label=f'Model, center={model_center:.1f}')
                ax2.plot(model_pix+model_center, fit(model_pix+1)*flux_map_i[peak_index],
                         color=line[0].get_c(), linestyle=':', alpha=0.3)
                ax2.plot(model_pix+model_center, fit(model_pix-1)*flux_map_i[peak_index],
                         color=line[0].get_c(), linestyle=':', alpha=0.3)

    ax1.grid()
    ax1.legend(loc='best')
    ax2.grid()
    ax2.legend(loc='best')

    log.info(f"  Saving: {ouput_cube_graphic}")
    plt.savefig(ouput_cube_graphic, bbox_inches='tight', pad_inches=0.10)


##-------------------------------------------------------------------------
## build_CRED2_graphic
##-------------------------------------------------------------------------
def build_CRED2_graphic(images, comment, ouput_cred2_image_file, data_path,
                        iterate=True, x0=335, y0=256):
    ouput_cred2_image_file = Path(ouput_cred2_image_file)
    import ccdproc
    import photutils
    from photutils.centroids import centroid_com, centroid_2dg

    nx = len(set(images['x']))
    ny = len(set(images['y']))
    xs = sorted(set(images['x']))
    ys = sorted(set(images['y']))

    fig = plt.figure(figsize=(15,15))
    nimages = len(images[images['camera'] == 'CRED2'])
    log.info(f'Building CRED2 graphic with {nimages} images')
    for fig_index,entry in enumerate(images[images['camera'] == 'CRED2']):
        i = xs.index(entry['x'])
        j = ys.index(entry['y'])
        cred2_file = Path(entry['file'])
        EL, va = parse_CRED2_image_header(cred2_file)
        Xpix = entry['x']
        Ypix = entry['y']

        # Create and Subtract Background
        ccddata = CCDData.read(entry['file'], unit="adu", memmap=False)
        source_mask = photutils.make_source_mask(ccddata.data, 10, 100)
        bkg = photutils.Background2D(ccddata,
                                     box_size=128,
                                     mask=source_mask,
                                     sigma_clip=astropy.stats.SigmaClip())
        image_data = ccddata.data - bkg.background.value
        log.debug(f"  CRED2 mode = {mode(ccddata.data)} ({mode(image_data)} after background sub)")

        log.debug("Running median CR reject to get rid of bad pixels")
        image_data, mask = ccdproc.cosmicray_median(image_data, mbox=7, gbox=0, rbox=7)

        # Pull largeish subframe and centroid
        dx = 60
        dy = 50
        subframe = image_data[y0-dy:y0+dy,x0-dx:x0+dx]
        dx1, dy1 = centroid_com(subframe)
        x1 = x0 - dx + dx1
        y1 = y0 - dy + dy1
        log.debug(f"  Iteration 1: {x1:.1f} {y1:.1f} ({entry['x']:.1f} {entry['y']:.1f})")

        # Iterate on fit with smaller box
        if iterate is True:
            dx = 35
            dy = 30
            subframe = image_data[int(y1)-dy:int(y1)+dy,int(x1)-dx:int(x1)+dx]
            dx2, dy2 = centroid_com(subframe)
            x2 = int(x1) - dx + dx2
            y2 = int(y1) - dy + dy2
        else:
            x2 = x1
            y2 = y1
        log.debug(f"  Iteration 2: {x2:.1f} {y2:.1f} ({entry['x']:.1f} {entry['y']:.1f})")

        # Third iteration
        if iterate is True:
            dx = 35
            dy = 30
            subframe = image_data[int(y2)-dy:int(y2)+dy,int(x2)-dx:int(x2)+dx]
            dx3, dy3 = centroid_com(subframe)
            x3 = int(x2) - dx + dx3
            y3 = int(y2) - dy + dy3
        else:
            x3 = x1
            y3 = y1
        log.debug(f"  Iteration 3: {x3:.1f} {y3:.1f} ({entry['x']:.1f} {entry['y']:.1f})")

        # Add plot to figure
        plt.subplot(ny,nx,fig_index+1)
        cube_number = cred2_file.name.replace('kpfguide_cube_', '').replace('.fits', '')
        title_string = f"{cube_number}: x,y={Xpix:.1f}, {Ypix:.1f}"
        log.debug(f"Building frame: {title_string}")
        plt.title(title_string, size=8)
        norm = viz.ImageNormalize(image_data,
                                  interval=viz.AsymmetricPercentileInterval(1.5,100),
                                  stretch=viz.LogStretch())
        plt.imshow(subframe, interpolation='none', cmap='gray', origin='lower', norm=norm)

        plt.plot(entry['x'] - x2 + dx, entry['y'] - y2 + dy, 'bx')
        if iterate is True:
            plt.arrow(entry['x'] - x2 + dx, entry['y'] - y2 + dy,
                      dx3-(entry['x'] - x2 + dx),
                      dy3-(entry['y'] - y2 + dy),
                      color='g', alpha=0.5,
                      head_width=0.1, length_includes_head=True)
            plt.plot(dx3, dy3, 'r+')
        plt.gca().set_aspect('equal', 'box')
        plt.gca().set_yticks([])
        plt.gca().set_xticks([])

    log.info(f"  Saving: {ouput_cred2_image_file}")
    if ouput_cred2_image_file.exists() is True:
        ouput_cred2_image_file.unlink()
    plt.savefig(ouput_cred2_image_file, bbox_inches='tight', pad_inches=0.10)


##-------------------------------------------------------------------------
## build_FVC_graphic
##-------------------------------------------------------------------------
def build_FVC_graphic(FVC, images, comment, ouput_FVC_image_file, data_path,
                      x0=335, y0=256):
    data_path = Path(data_path)
    ouput_FVC_image_file = Path(ouput_FVC_image_file)

    nx = len(set(images['x']))
    ny = len(set(images['y']))
    xs = sorted(set(images['x']))
    ys = sorted(set(images['y']))

    fig = plt.figure(figsize=(15,15))
    nimages = len(images[images['camera'] == FVC])
    log.info(f'Building {FVC}FVC graphic with {nimages} images')
    for fig_index,entry in enumerate(images[images['camera'] == FVC]):
        i = xs.index(entry['x'])
        j = ys.index(entry['y'])
        new_fig_index = (i+1) + nx*(ny-j-1)
        this_grid_pos = images[np.isclose(images['x'], entry['x']) & np.isclose(images['y'], entry['y'])]
        cred2_file = this_grid_pos[this_grid_pos['camera'] == 'CRED2']['file'][0]
        EL, va = parse_CRED2_image_header(cred2_file)
        Xpix = entry['x']
        Ypix = entry['y']

        fvc_file = Path(entry['file'])
        hdul = fits.open(fvc_file)
        dx = 50
        dy = 50
        subframe = hdul[0].data[int(y0)-dy:int(y0)+dy,int(x0)-dx:int(x0)+dx]
        plt.subplot(ny,nx,new_fig_index)
#         title_string = f"{fvc_file.name.replace('.fits','').replace('fvc','')}: {Xpix:.1f}, {Ypix:.1f}"
        title_string = f"{Xpix:.1f}, {Ypix:.1f}"
        log.debug(f"Building frame: {title_string}")
        plt.title(title_string, size=8)
        norm = viz.ImageNormalize(subframe,
                                  interval=viz.AsymmetricPercentileInterval(40,100),
                                  stretch=viz.LinearStretch())
        plt.imshow(subframe, cmap='gray', origin='lower', norm=norm)
        radius = {'EXT': 27, 'SCI': 12, 'CAHK': 40}[FVC]
        circ = plt.Circle((dx, dy), radius=radius, alpha=0.5,
                          edgecolor='blue', fill=False)
        plt.gca().add_patch(circ)
        plt.gca().set_yticks([])
        plt.gca().set_xticks([])

    log.info(f"  Saving: {ouput_FVC_image_file}")
    if ouput_FVC_image_file.exists() is True:
        ouput_FVC_image_file.unlink()
    plt.savefig(ouput_FVC_image_file, bbox_inches='tight', pad_inches=0.10)


##-------------------------------------------------------------------------
## analyze_grid_search
##-------------------------------------------------------------------------
def analyze_grid_search(logfile, fiber='Science', model_seeing='0.7',
                        xfit=None, yfit=None,
                        generate_cred2=False):
    if f"{float(model_seeing):.2f}" not in ['0.50', '0.70', '0.90']:
        print(f"Seeing models only available for 0.50, 0.70, and 0.90 arcsec")
        return
    model_seeing = float(model_seeing)
    model = f"Fiber Coupling Model seeing {model_seeing:.2f} arcsec.csv"
    logfile = Path(logfile)
    assert logfile.exists()
    log.info("")
    log.info(f"Analyzing {logfile.name}")
    data_path = logfile.parent.parent

    # Parse log file name
    logfilenamematch = re.match('(\d{8}at\d{6})_GridSearch.log', logfile.name)
    if logfilenamematch is None:
        print('Failed to parse log file name for timestamp')
        return
    else:
        ts = logfilenamematch.group(1)

    # Check for images table name to determine mode
    mode = None
    tiptilt_images_file = logfile.parent / f"TipTiltGridSearch_images_{ts}.txt"
    sciADC_images_file = logfile.parent / f"SciADCGridSearch_images_{ts}.txt"
    if tiptilt_images_file.exists():
        mode = 'TipTilt'
        images_file = tiptilt_images_file
    elif sciADC_images_file.exists():
        mode = 'SciADC'
        images_file = sciADC_images_file
    else:
        mode = 'TipTilt'
        images_file = logfile.parent / logfile.name.replace('GridSearch', 'GridSearch_images').replace('.log', '.txt')
    if images_file.exists():
        log.info(f"  Found: {images_file}")
    else:
        log.error('Unable to find an images table, skipping this run')
        return

    # Determine comment string from log file
    try:
        with open(logfile) as FO:
            lines = FO.readlines()
        for line in lines[:60]:
            m_comment = re.search("comment: (.*)", line)
            if m_comment is not None:
                comment = m_comment.groups()[0].strip('\n')
        log.info(f"  Log Comment: {comment}")
    except:
        comment = ''

    # Determine DAR offset from log file
    try:
        with open(logfile) as FO:
            lines = FO.readlines()
        for line in lines[:60]:
            m_daroffset = re.search("DAR_OFFSET = ([\d\.]+),? ([\d\.]+)", line)
            if m_daroffset is not None:
                dar_offset = (float(m_daroffset.groups()[0]), float(m_daroffset.groups()[1]))
        log.info(f"  Log DAR Offset: {dar_offset}")
    except:
        log.warning("  Failed to find DAR_OFFSET in log")
        dar_offset = None

    # Load images table and fix old bad naming
    images = Table.read(images_file, format='ascii.csv')
    if 'dx' in images.keys():
        log.warning('Renaming old column names')
        # This is an old file with old column names
        images.add_column(Column(name='x', data=images['dx'].data))
        images.add_column(Column(name='y', data=images['dy'].data))
    nx = len(set(set(images['x'])))
    ny = len(set(set(images['y'])))
    log.info(f"  Read in {images_file.name} with {len(images)} lines ({nx} x {ny} grid)")

    # Build output FITS cube file name
    ouput_spec_cube = f"{mode}{logfile.name.replace('.log', '.fits')}"
    hdul = build_FITS_cube(images, comment, ouput_spec_cube, mode=mode,
                           dar_offset=dar_offset)

    # Build graphic of cube fluxes
    ouput_cube_graphic = f"{mode}{logfile.name.replace('.log', '_fluxmap.png')}"
    build_cube_graphic(hdul, ouput_cube_graphic, mode=mode, xfit=xfit, yfit=yfit)

    # Build graphic of CRED2 Images
    if len(images[images['camera'] == 'CRED2']) > 0 and mode == 'TipTilt' and generate_cred2 is True:
        ouput_cred2_image_file = Path(f"{mode}{logfile.name.replace('.log', '_CRED2_images.png')}")
        cred2_pixels = {'EMSky': (160, 256),
                        'Science': (335, 256),
                        'Sky': (510, 256)}[fiber]
        build_CRED2_graphic(images, comment, ouput_cred2_image_file, data_path,
                            x0=cred2_pixels[0], y0=cred2_pixels[1], applydar=applydar)

    # Build graphic of FVC Images
    if mode == 'TipTilt':
        FVCs = ['SCI', 'CAHK', 'EXT']
        fvc_pixels = {'SCI': {'EMSky': None,
                              'Science': (803.5, 607.0),
                              'Sky': None},
                      'CAHK': {'EMSky': None,
                               'Science': (770, 645),
                               'Sky': None},
                      'EXT': {'EMSky': None,
                              'Science': (620, 700),
                              'Sky': None}
                     }
        fvcsci_pixels = [fiber]
        fvccahk_pixels = [fiber]
        fvcext_pixels = [fiber]
        for FVC in FVCs:
            ouput_fvc_image_file = Path(f"{mode}{logfile.name.replace('.log', f'_{FVC}FVC_images.png')}")
            fvc_images = images[images['camera'] == FVC]
            if len(fvc_images) > 0:
                build_FVC_graphic(FVC, images, comment, ouput_fvc_image_file, data_path,
                                  x0=fvc_pixels[FVC][fiber][0],
                                  y0=fvc_pixels[FVC][fiber][1],
                                  )
    return


##-------------------------------------------------------------------------
## AnalyzeGridSearch
##-------------------------------------------------------------------------
class AnalyzeGridSearch(KPFTranslatorFunction):
    '''# Description
    Tool to analyze engineering data taken by the `engineering.GridSearch` or
    `engineering.Run2DGridSearch` scripts.

    # Parameters
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        for logfile in args.get('logfile'):
            analyze_grid_search(logfile,
                                fiber=args.get('fiber'),
                                model_seeing=args.get('seeing'),
                                xfit=args.get('xfit'), yfit=args.get('yfit'),
                                generate_cred2=args.get('cred2'),
                                )

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('logfile', type=str, nargs='*',
            help="The logfile or files of the grid search runs to analyze")
        ## add flags
        parser.add_argument("--cred2", dest="cred2",
            default=False, action="store_true",
            help="Generate CRED2 plots? (default = False)")
        ## add options
        parser.add_argument("--fiber", dest="fiber", type=str,
            default='Science',
            help="The fiber being examined (Science, Sky, or EMSky).")
        parser.add_argument("--seeing", dest="seeing", type=str,
            choices=['0.5', '0.7', '0.9'],
            default='0.7',
            help="The seeing model to overlay on the fiber coupling plot.")
        parser.add_argument("--xfit", dest="xfit", type=float,
            default=335.5,
            help="The X pixel position to use as the center when overlaying the model.")
        parser.add_argument("--yfit", dest="yfit", type=float,
            default=258,
            help="The X pixel position to use as the center when overlaying the model.")

        return super().add_cmdline_args(parser, cfg)


if __name__ == '__main__':
    print('start')
    ##-------------------------------------------------------------------------
    ## Parse Command Line Arguments
    ##-------------------------------------------------------------------------
    ## create a parser object for understanding command-line arguments
    import argparse
    p = argparse.ArgumentParser(description='''
    ''')
    ## add arguments
    p.add_argument('logfile', type=str, nargs='*',
                   help="The logfile or files of the grid search runs to analyze")
    ## add flags
    p.add_argument("--cred2", dest="cred2",
        default=False, action="store_true",
        help="Generate CRED2 plots? (default = False)")
    ## add options
    p.add_argument("--fiber", dest="fiber", type=str,
        default='Science',
        help="The fiber being examined (Science, Sky, or EMSky).")
    p.add_argument("--seeing", dest="seeing", type=float,
        default=0.7,
        help="The seeing model to overlay on the fiber coupling plot.")
    p.add_argument("--xfit", dest="xfit", type=float,
        default=335.5,
        help="The X pixel position to use as the center when overlaying the model.")
    p.add_argument("--yfit", dest="yfit", type=float,
        default=258,
        help="The X pixel position to use as the center when overlaying the model.")
    args = p.parse_args()

    for logfile in args.logfile:
        analyze_grid_search(logfile,
                            fiber=args.fiber,
                            model_seeing=args.seeing,
                            xfit=args.xfit, yfit=args.yfit,
                            generate_cred2=args.cred2,
                            )
