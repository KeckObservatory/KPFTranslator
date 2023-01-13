#!python3

## Import General Tools
from pathlib import Path
import argparse
import logging
import re

from pathlib import Path
import numpy as np
import astropy
from astropy.io import fits
from astropy import visualization as viz
from astropy.table import Table, Column
from astropy.nddata import CCDData

import warnings
warnings.filterwarnings('ignore', category=astropy.wcs.FITSFixedWarning, append=True)

from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator

##-------------------------------------------------------------------------
## Parse Command Line Arguments
##-------------------------------------------------------------------------
## create a parser object for understanding command-line arguments
p = argparse.ArgumentParser(description='''
''')
## add arguments
p.add_argument('logfile', type=str, nargs='*',
               help="The logfile or files of the grid search runs to analyze")
## add flags
p.add_argument("-v", "--verbose", dest="verbose",
    default=False, action="store_true",
    help="Be verbose! (default = False)")
p.add_argument("--skipcred2", dest="skipcred2",
    default=False, action="store_true",
    help="Skip building figure of CRED2 images")
p.add_argument("--skipFVCs", dest="skipFVCs",
    default=False, action="store_true",
    help="Skip building figures of FVC images")
## add options
p.add_argument("--fiber", dest="fiber", type=str,
    default='Science',
    help="The fiber being examined (Science, Sky, or EMSky).")
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


##-------------------------------------------------------------------------
## build_FITS_cube
##-------------------------------------------------------------------------
def build_FITS_cube(images, comment, ouput_spec_cube):
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
    log.info(f'  Building FITS cube using {nspectra} spectra')
    for entry in images[images['camera'] == camname]:
        i = xs.index(entry['x'])
        j = ys.index(entry['y'])
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
            wavs_strings = [k for k in onedspec_table.keys() if k not in ['Date-Beg', 'Date-End']]
            wavs = [float(k) for k in onedspec_table.keys() if k not in ['Date-Beg', 'Date-End']]
            dwav = [wav-wavs[i-1] for i,wav in enumerate(wavs) if i>0]
            nwav = len(wavs)
            spec_cube = np.zeros((nwav,ny,nx))
            posdata = np.zeros((2,ny,nx))
            index_450nm = np.argmin([abs(w-450) for w in wavs])
            index_550nm = np.argmin([abs(w-550) for w in wavs])
            index_650nm = np.argmin([abs(w-650) for w in wavs])

        all_EM_spectra = np.zeros((len(onedspec_table), nwav), dtype=float)
        for lineno,line in enumerate(onedspec_table):
            linewavs = np.array([float(line[key]) for key in wavs_strings])
            all_EM_spectra[lineno,:] = linewavs
#         mean_EM_spectrum = all_EM_spectra.mean(axis=0)
        mean_EM_spectrum_dropFL = all_EM_spectra[1:-1,:].mean(axis=0)
        spec_cube[:,j,i] = np.array(mean_EM_spectrum_dropFL)
        posdata[0,j,i] = entry['x']
        posdata[1,j,i] = entry['y']


    norm_spec_cube = np.zeros((nwav,ny,nx))
    for w,spectral_slice in enumerate(spec_cube):
        norm_spec_cube[w,:,:] = spectral_slice / spectral_slice.mean()

    flux_map = np.sum(spec_cube, axis=0)
    npix = 30
    color_images = np.zeros((3,ny,nx))
    color_images[0,:,:] = np.sum(spec_cube[index_450nm-npix:index_450nm+npix,:,:], axis=0)
    color_images[1,:,:] = np.sum(spec_cube[index_550nm-npix:index_550nm+npix,:,:], axis=0)
    color_images[2,:,:] = np.sum(spec_cube[index_650nm-npix:index_650nm+npix,:,:], axis=0)

    color_cube = np.zeros((2,ny,nx))
    color_cube[0,:,:] = color_images[0,:,:]/color_images[1,:,:]
    color_cube[1,:,:] = color_images[2,:,:]/color_images[1,:,:]

    hdu = fits.PrimaryHDU()
    hdu.header.set('Name', 'Spectral_Cube')
    hdu.header.set('OBJECT', 'Spectral_Cube')
    hdu.header.set('Comment', comment)
    hdu.data = spec_cube
    normcubehdu = fits.ImageHDU()
    normcubehdu.header.set('Name', 'Normalized_Spectral_Cube')
    normcubehdu.header.set('OBJECT', 'Normalized_Spectral_Cube')
    normcubehdu.data = norm_spec_cube
    fluxmaphdu = fits.ImageHDU()
    fluxmaphdu.header.set('Name', 'Flux_Map')
    fluxmaphdu.header.set('OBJECT', 'Flux_Map')
    fluxmaphdu.data = flux_map
    fluxcubehdu = fits.ImageHDU()
    fluxcubehdu.header.set('Name', 'Three_Color_Cube')
    fluxcubehdu.header.set('OBJECT', 'Three_Color_Cube')
    fluxcubehdu.header.set('Layer1', '450nm')
    fluxcubehdu.header.set('Layer2', '550nm')
    fluxcubehdu.header.set('Layer3', '650nm')
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
    poshdu.data = posdata
    wavhdu = fits.ImageHDU()
    wavhdu.header.set('Name', 'Wavelength_Values')
    wavhdu.header.set('OBJECT', 'Wavelength_Values')
    wavhdu.data = np.array(wavs)
    hdul = fits.HDUList([hdu, normcubehdu, fluxmaphdu, fluxcubehdu, colormaphdu, poshdu, wavhdu])
    log.info(f'  Writing {ouput_spec_cube}')
    hdul.writeto(f'{ouput_spec_cube}', overwrite=True)
    return hdul


##-------------------------------------------------------------------------
## build_cube_graphic
##-------------------------------------------------------------------------
# def build_cube_graphic(hdul, ouput_cube_graphic):
#     Xprojection = hdul[0].data.mean(axis=1)
#     Xpeaks = []
#     for i,cut in enumerate(Xprojection):
#         Xpeaks.append(np.argmax(cut))
#         Xprojection[i,:] /= Xprojection[i,:].mean()
#     Xprojection = Xprojection.transpose()
#     Xprojection.shape
# 
#     Yprojection = hdul[0].data.mean(axis=2)
#     Ypeaks = []
#     for i,cut in enumerate(Yprojection):
#         Ypeaks.append(np.argmax(cut))
#         Yprojection[i,:] /= Yprojection[i,:].mean()
#     Yprojection = Yprojection.transpose()
#     Yprojection.shape


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
    log.info(f'  Building CRED2 graphic with {nimages} images')
    for fig_index,entry in enumerate(images[images['camera'] == 'CRED2']):
        i = xs.index(entry['x'])
        j = ys.index(entry['y'])
        cred2_file = Path(entry['file'])

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
        title_string = f"{cube_number}: x,y={entry['x']:.1f}, {entry['y']:.1f}"
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
    log.info(f'  Building {FVC}FVC graphic with {nimages} images')
    for fig_index,entry in enumerate(images[images['camera'] == FVC]):
        i = xs.index(entry['x'])
        j = ys.index(entry['y'])
        fvc_file = Path(entry['file'])
        hdul = fits.open(fvc_file)
        dx = 50
        dy = 50
        subframe = hdul[0].data[int(y0)-dy:int(y0)+dy,int(x0)-dx:int(x0)+dx]
        plt.subplot(ny,nx,fig_index+1)
        title_string = f"{fvc_file.name.replace('.fits','').replace('fvc','')}: {entry['x']:.1f}, {entry['y']:.1f}"
        log.debug(f"Building frame: {title_string}")
        plt.title(title_string, size=8)
        norm = viz.ImageNormalize(subframe,
                                  interval=viz.AsymmetricPercentileInterval(40,99.9),
#                                   interval=viz.MinMaxInterval(),
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
def analyze_grid_search(logfile, fiber='Science',
                        skipcred2=False, skipFVCs=False):

    logfile = Path(logfile)
    assert logfile.exists()
    assert logfile.suffix == '.log'
    log.info(f"Analyzing {logfile.name}")
    data_path = logfile.parent.parent

    # Check for images table name to determine mode
    mode = None
    tiptilt_images_file = logfile.parent / logfile.name.replace('GridSearch', 'TipTiltGridSearch_images').replace('.log', '.txt')
    sciADC_images_file = logfile.parent / logfile.name.replace('GridSearch', 'SciADCGridSearch_images').replace('.log', '.txt')
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
        for line in lines[:20]:
            m = re.search("comment: (.*)", line)
            if m is not None:
                comment = m.groups()[0].strip('\n')
        log.info(f"  Log Comment: {comment}")
    except:
        comment = ''
        log.error('Could not find comment in log file')

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
    hdul = build_FITS_cube(images, comment, ouput_spec_cube)
#     ouput_cube_graphic = logfile.name.replace('.log', '.png')
#     build_cube_graphic(hdul, ouput_cube_graphic)

    # Build graphic of CRED2 Images
    if skipcred2 is not True and len(images[images['camera'] == 'CRED2']) > 0:
        ouput_cred2_image_file = Path(f"{mode}{logfile.name.replace('.log', '_CRED2_images.png')}")
        cred2_pixels = {'EMSky': (160, 256),
                        'Science': (335, 256),
                        'Sky': (510, 256)}[fiber]
        build_CRED2_graphic(images, comment, ouput_cred2_image_file, data_path,
                            x0=cred2_pixels[0], y0=cred2_pixels[1])

    # Build graphic of FVC Images
    if skipFVCs is not True:
        FVCs = ['SCI', 'CAHK', 'EXT']
        fvc_pixels = {'SCI': {'EMSky': None,
                              'Science': (803.5, 607.0),
                              'Sky': None},
                      'CAHK': {'EMSky': None,
                               'Science': (800, 600),
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
                                  y0=fvc_pixels[FVC][fiber][1])
    return


if __name__ == '__main__':
    for logfile in args.logfile:
        analyze_grid_search(logfile,
                            skipcred2=args.skipcred2,
                            fiber=args.fiber,
                            )
