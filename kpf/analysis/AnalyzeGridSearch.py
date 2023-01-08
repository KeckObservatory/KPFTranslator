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
from astropy.table import Table, Column
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
p.add_argument("--FVCs", dest="FVCs", type=str,
    default='',
    help="A comma separated list of FVC cameras to trigger (SCI, CAHK, EXT).")
p.add_argument("--data_path", dest="data_path", type=str,
    default='/s/sdata1701/kpfeng/2022dec14',
    help="The path to the data directory with logs and CRED2 sub-directories")
# p.add_argument("--log_path", dest="log_path", type=str,
#     default='/s/sdata1701/kpfeng/2022nov06/script_logs',
#     help="The path to the directory containing the logs")
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
## analyze_grid_search
##-------------------------------------------------------------------------
def analyze_grid_search(date_time_string, flux_prefix=None, fiber='Science',
                        data_path=Path('/s/sdata1701/kpfeng/2022dec14'),
                        FVCs=['SCI'],
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

    fluxes_file = data_path / Path('script_logs') / Path(f'TipTiltGridSearch_fluxes_{date_time_string}.txt')
    images_file = data_path / Path('script_logs') / Path(f'TipTiltGridSearch_images_{date_time_string}.txt')
    log_file = data_path / Path('script_logs') / Path(f'GridSearch_{date_time_string}.log')
    ouput_spec_cube = Path(f"{date_time_string}_spec_cube.fits")
    ouput_spec_cube_norm = Path(f"{date_time_string}_spec_cube_norm.fits")
    ouput_cred2_image_file = Path(f"{date_time_string}_CRED2_images.png")
    ouput_sci_image_file = Path(f"{date_time_string}_SCI_images.png")
    ouput_cahk_image_file = Path(f"{date_time_string}_CAHK_images.png")
    ouput_ext_image_file = Path(f"{date_time_string}_EXT_images.png")
    ouput_analysis_image_file = Path(f"{date_time_string}_fiber_location.png")

    flux_table = Table.read(fluxes_file, format='ascii.csv')
    log.info(f"Read in {fluxes_file.name} with {len(flux_table)} lines")
    if 'dx' in flux_table.keys():
        log.warning('Renaming old column names')
        # This is an old file with old column names
        flux_table.add_column(Column(name='x', data=flux_table['dx'].data))
        flux_table.add_column(Column(name='y', data=flux_table['dy'].data))

    images = Table.read(images_file, format='ascii.csv')
    if 'dx' in images.keys():
        log.warning('Renaming old column names')
        # This is an old file with old column names
        images.add_column(Column(name='x', data=images['dx'].data))
        images.add_column(Column(name='y', data=images['dy'].data))
    nx = len(set(set(images['x'])))
    ny = len(set(set(images['y'])))
    log.info(f"Read in {images_file.name} with {len(images)} lines ({nx} x {ny} grid)")

    cameras = set(images['camera'])
    log.info(f"Found cameras: {cameras}")

    dxs = set(flux_table['x'])
    if len(dxs) > 1:
        deltax = (max(dxs) - min(dxs))/(len(dxs)-1)
    else:
        deltax = 0
    dys = set(flux_table['y'])
    if len(dys) > 1:
        deltay = (max(dys) - min(dys))/(len(dys)-1)
    else:
        deltay = 0

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

    xoffset = np.zeros((len(set(flux_table['i'])), len(set(flux_table['j']))))
    yoffset = np.zeros((len(set(flux_table['i'])), len(set(flux_table['j']))))
    
    # Prep ExpMeter flux analysis
    fluxes = np.zeros((4, len(set(flux_table['i'])), len(set(flux_table['j']))))
    # Prep CRED2 Analysis
    if 'CRED2' in cameras:
        cred2_images_fig = plt.figure(figsize=(12,14))
        xcred2 = np.zeros((len(set(flux_table['i'])), len(set(flux_table['j']))))
        ycred2 = np.zeros((len(set(flux_table['i'])), len(set(flux_table['j']))))
    # Prep FVC Analysis
    if 'SCI' in FVCs:
        sci_FVC_images_fig = plt.figure(figsize=(12,12))
    if 'CAHK' in FVCs:
        sci_CAHK_images_fig = plt.figure(figsize=(12,12))
    if 'EXT' in FVCs:
        ext_FVC_images_fig = plt.figure(figsize=(12,12))


    # Build 3D Spectral Cube
    nexpmeter = len(images[images['camera'] == 'ExpMeter'])
    n1dspec = len(images[images['camera'] == 'ExpMeter_1Dspec'])
    specfiles = (n1dspec == nexpmeter)
    if specfiles is True:
        camname = 'ExpMeter_1Dspec'
    else:
        camname = 'ExpMeter'

    nwav = 421
    index_for_550nm = 184
    spec_cube = np.zeros((nwav,ny,nx))
    spec_cube_norm = np.zeros((nwav,ny,nx))
    dxs = sorted(set(images['x']))
    assert len(dxs) == nx
    dys = sorted(set(images['y']))
    assert len(dys) == ny
    hdu = fits.PrimaryHDU()
    posdata = np.zeros((2,ny,nx))
    hdu.header.set('Name', 'Spectral Cube')
    hdu.header.set('Comment', comment)
    hdu_norm = fits.PrimaryHDU()
    hdu_norm.header.set('Name', 'Spectral Cube')
    hdu_norm.header.set('Comment', comment)
    for entry in images[images['camera'] == camname]:
        i = dxs.index(entry['x'])
        j = dys.index(entry['y'])
        if specfiles is False:
            p = Path(entry['file'])
            ismatch = re.search('(kpf_em_\d+)\.\d{3}\.fits', p.name)
            if ismatch:
                specfile = p.parent / f"{ismatch.groups(1)[0]}.fits"
            else:
                print(f'Failed Match: {p}')
        else:
            specfile = Path(entry['file'])
        hdul = fits.open(specfile)
        spec_table = Table(hdul[1].data)
        spectrum = []
        wavelengths = []
        k = 0
        for key in spec_table.keys():
            if key not in ['Date-Beg', 'Date-End']:
                k+=1
                wav = float(key)
                hdu.header.set(f"{k}", key)
                hdu_norm.header.set(f"{k}", key)
                spectrum.append(np.median(spec_table[key]))

        spec_cube[:,j,i] = np.array(spectrum)
        posdata[0,j,i] = entry['x']
        posdata[1,j,i] = entry['y']

    # Build flux map 
    flux_map = np.sum(spec_cube, axis=0)
    # Build flux map for 550nm
    npix = 30
    flux_map_550 = np.sum(spec_cube[index_for_550nm-npix:index_for_550nm+npix,:,:], axis=0)
#     index_for_675nm = 61
#     flux_map_675 = np.sum(spec_cube[index_for_675nm-npix:index_for_675nm+npix,:,:], axis=0)
#     index_for_450nm = 405
#     flux_map_450 = np.sum(spec_cube[index_for_450nm-npix:index_for_450nm+npix,:,:], axis=0)

    max_index = np.unravel_index(flux_map.argmax(), flux_map.shape)
    max_spec = spec_cube[:,max_index[0], max_index[1]]
#     avg_spec = np.mean(np.mean(spec_cube, axis=1), axis=1)
    for entry in images[images['camera'] == camname]:
        i = dxs.index(entry['x'])
        j = dys.index(entry['y'])
        spec_cube_norm[:,j,i] = spec_cube[:,j,i]/spec_cube[index_for_550nm,j,i]/(max_spec/max_spec[index_for_550nm])

    if ouput_spec_cube.exists() is True: ouput_spec_cube.unlink()
    log.info(f"Saving: {ouput_spec_cube}")
    hdu.data=spec_cube
    hdul = fits.HDUList([hdu])
    hdu_norm.data=spec_cube_norm
    hdu_norm.header.set('Name', 'Normalized Spectral Cube')
    hdul.append(hdu_norm)
    poshdu = fits.ImageHDU()
    poshdu.data = posdata
    poshdu.header.set('COMMENT', 'X and Y positions')
    hdul.append(poshdu)
    fluxhdu = fits.ImageHDU()
    fluxhdu.data = flux_map
    fluxhdu.header.set('COMMENT', 'Total flux map')
    hdul.append(fluxhdu)
    flux550hdu = fits.ImageHDU()
    flux550hdu.data = flux_map_550
    flux550hdu.header.set('COMMENT', 'Flux map near 550nm')
    hdul.append(flux550hdu)

    hdul.writeto(f'{ouput_spec_cube}')

    # Loop over positions
    for imno,flux_entry in enumerate(flux_table):
        j = flux_entry['i']
        i = flux_entry['j']
        xoffset[j, i] = flux_entry['x']
        yoffset[j, i] = flux_entry['y']
        for k in ks:
            fluxes[k, j, i] = flux_entry[f'{flux_prefix}{k+1}']

        if 'CRED2' in cameras:
            log.debug(f"  Determining CRED2 pixel for {flux_entry['x']:.2f}, {flux_entry['y']:.2f}")
            log.debug(f"  Centering image on {cred2_pixels}")
            x, y = show_CRED2_image(flux_entry['x'], flux_entry['y'],
                                    images, flux_table,
                                    data_path=data_path/Path('CRED2'),
                                    x0=cred2_pixels[0], y0=cred2_pixels[1],
                                    fig=cred2_images_fig, imno=imno+1,
                                    initial_x=flux_entry['x'],
                                    initial_y=flux_entry['y'],
                                    )
            xcred2[j, i] = x
            ycred2[j, i] = y
        if 'SCI' in FVCs and fvcsci_pixels is not None:
            log.debug(f"  Generating SCI FVC image centered on {fvcsci_pixels}")
            show_FVC_image(flux_entry['x'], flux_entry['y'],
                           images, flux_table, camera='SCI',
                           data_path=data_path/Path('FVC1'),
                           x0=fvcsci_pixels[0], y0=fvcsci_pixels[1],
                           fig=sci_FVC_images_fig, imno=imno+1)
        if 'CAHK' in FVCs and fvccahk_pixels is not None:
            log.debug(f"  Generating SCI FVC image centered on {fvcsci_pixels}")
            show_FVC_image(flux_entry['x'], flux_entry['y'],
                           images, flux_table, camera='CAHK',
                           data_path=data_path/Path('FVC2'),
                           x0=fvccahk_pixels[0], y0=fvccahk_pixels[1],
                           fig=sci_CAHK_images_fig, imno=imno+1)
        if 'EXT' in FVCs and fvcext_pixels is not None:
            log.debug(f"  Generating EXT FVC image centered on {fvcext_pixels}")
            show_FVC_image(flux_entry['x'], flux_entry['y'],
                           images, flux_table, camera='EXT',
                           data_path=data_path/Path('FVC4'),
                           x0=fvcext_pixels[0], y0=fvcext_pixels[1],
                           fig=ext_FVC_images_fig, imno=imno+1)

    if 'CRED2' in cameras:
        # Plot CRED2 Positions of each offset
        plt.figure(num=cred2_images_fig.number)
        plt.subplot(nx+2,ny,nx*ny+2)
        plt.title('Grid positions in CRED2 pixel space', size=8)
        plt.plot(xcred2, ycred2, 'r+', alpha=0.5)
        plt.plot(flux_table['x'], flux_table['y'], 'bx', alpha=0.5)
        for imno,flux_entry in enumerate(flux_table):
            j = flux_entry['i']
            i = flux_entry['j']
    #         print(i, j, flux_entry['x'], flux_entry['y'])
            plt.arrow(flux_entry['x'], flux_entry['y'],
                      xcred2[j, i]-flux_entry['x'],
                      ycred2[j, i]-flux_entry['y'],
                      color='g', alpha=0.5,
                      head_width=0.1, length_includes_head=True)
        plt.gca().xaxis.set_major_locator(MultipleLocator(base=1.0))
        plt.gca().yaxis.set_major_locator(MultipleLocator(base=1.0))
        plt.grid()
        plt.xlabel('CRED2 X (pix)')
        plt.ylabel('CRED2 Y (pix)')
        plt.gca().axis('equal')
        log.info(f"Saving: {ouput_cred2_image_file}")
        if ouput_cred2_image_file.exists() is True:
            ouput_cred2_image_file.unlink()
        plt.savefig(ouput_cred2_image_file, bbox_inches='tight', pad_inches=0.10)

    # Save FVC Images Figure
    if 'SCI' in FVCs:
        log.info(f"Saving: {ouput_sci_image_file}")
        plt.figure(num=sci_FVC_images_fig.number)
        if ouput_sci_image_file.exists() is True:
            ouput_sci_image_file.unlink()
        plt.savefig(ouput_sci_image_file, bbox_inches='tight', pad_inches=0.10)
    if 'CAHK' in FVCs:
        log.info(f"Saving: {ouput_cahk_image_file}")
        plt.figure(num=sci_CAHK_images_fig.number)
        if ouput_cahk_image_file.exists() is True:
            ouput_cahk_image_file.unlink()
        plt.savefig(ouput_cahk_image_file, bbox_inches='tight', pad_inches=0.10)
    if 'EXT' in FVCs:
        log.info(f"Saving: {ouput_ext_image_file}")
        plt.figure(num=ext_FVC_images_fig.number)
        if ouput_ext_image_file.exists() is True:
            ouput_ext_image_file.unlink()
        plt.savefig(ouput_ext_image_file, bbox_inches='tight', pad_inches=0.10)

    # Generate figure of Flux values on offset grid and estimated fiber position
    cred2_pixel_of_fiber = []
    plt.figure(figsize=(10,14))
    symbols = ['b^', 'gx', 'yo', 'r^']
    for k in [0,1,2,3]:
        plt.subplot(3,2,k+1)
        # Find offset position of peak flux
        flux_map = fluxes[k,:,:]
        peak_pos_j, peak_pos_i = np.unravel_index(flux_map.argmax(), flux_map.shape)
        peak_xoffset = xoffset[peak_pos_j, peak_pos_i]
        peak_yoffset = yoffset[peak_pos_j, peak_pos_i]
        if 'CRED2' in cameras:
            peak_xcred2 = xcred2[peak_pos_j, peak_pos_i]
            peak_ycred2 = ycred2[peak_pos_j, peak_pos_i]
        else:
            peak_xcred2 = 0
            peak_ycred2 = 0
        cred2_pixel_of_fiber.append((peak_xcred2, peak_ycred2))

        # Show image of exposure meter flux grid
        if k == 0:
            plot_title = f"{date_time_string}: {comment}\n"
        else:
            plot_title = ''
        plot_title += (f"ExpMeter band {k+1}\n"
                       f"Grid Pos = ({peak_xoffset:.2f}, {peak_yoffset:.2f}), "
                       f"CRED2 Pixel = ({peak_xcred2:5.1f}, {peak_ycred2:5.1f})\n"
                       f'FluxRatio: max/min = {max(flux_map.ravel())/min(flux_map.ravel()):.1e} (FluxMax = {max(flux_map.ravel()):.1e})'
                       )
        plt.title(plot_title, size=9)
        plt.imshow(flux_map.transpose(), cmap='gray', origin='lower')
        plt.plot(peak_pos_j, peak_pos_i, symbols[k])
        plt.gca().set_yticks([])
        plt.gca().set_xticks([])

    cred2_pixel_of_fiber = np.array(cred2_pixel_of_fiber)
    avg_x = cred2_pixel_of_fiber[:,0].mean()
    avg_y = cred2_pixel_of_fiber[:,1].mean()
    cred2_deltas_pix = np.array([(coord[0]-avg_x, coord[1]-avg_y) for coord in cred2_pixel_of_fiber])
    pixel_scale = 58 #mas/pix
    xrms = np.std(cred2_pixel_of_fiber[:,0])*pixel_scale
    yrms = np.std(cred2_pixel_of_fiber[:,1])*pixel_scale
    log.debug(f"CRED2 X Deviations {xrms:.0f} mas RMS: {cred2_deltas_pix[:,0]*pixel_scale}")
    log.debug(f"CRED2 X Deviations {yrms:.0f} mas RMS: {cred2_deltas_pix[:,1]*pixel_scale}")
    log.info(f"Saving: {ouput_analysis_image_file}")

    plt.subplot(3,2,(5,6))
    plt.title(f"CRED2 Positions in ExpMeter Bands: RMS=({xrms:.0f}, {yrms:.0f} mas)")

    plt.plot(flux_table['x'], flux_table['y'], 'k+')

    for k in [0,1,2,3]:
        xpix = cred2_pixel_of_fiber[k,0]
        ypix = cred2_pixel_of_fiber[k,1]
        plt.plot(xpix, ypix, symbols[k],
                 label=f"Band {k+1} ({xpix:.1f}, {ypix:.1f})",
                 markersize=10)
#     plt.plot(avg_x, avg_y, 'ko', markersize=20, alpha=0.4,
#              label=f'Avg. Position ({avg_x:.1f}, {avg_y:.1f})')
    plt.gca().axis('equal')
    plt.legend(loc='best')
    plt.gca().xaxis.set_major_locator(MultipleLocator(base=max([deltax, deltay])))
    plt.gca().yaxis.set_major_locator(MultipleLocator(base=max([deltax, deltay])))
    plt.grid()
    plt.xlabel('CRED2 X (pix)')
    plt.ylabel('CRED2 Y (pix)')

    if ouput_analysis_image_file.exists() is True:
        ouput_analysis_image_file.unlink()
    plt.savefig(ouput_analysis_image_file, bbox_inches='tight', pad_inches=0.10)

    return cred2_pixel_of_fiber


##-------------------------------------------------------------------------
## show_CRED2_image
##-------------------------------------------------------------------------
def show_CRED2_image(x, y, images, fluxes,
                     data_path='/s/sdata1701/kpfeng/2022oct16/CRED2',
                     x0=320, y0=256,
                     iterate=True,
                     fig=None, imno=1,
                     initial_x=None, initial_y=None):
    data_path = Path(data_path)
    nx = len(set(set(images['x'])))
    ny = len(set(set(images['y'])))
    tol = 0.001
    original_cred2_files = images[(abs(images['x'] - x) < tol) & (abs(images['y'] - y) < tol) & (images['camera'] == 'CRED2')]['file']
    original_cred2_file = Path(original_cred2_files[-1])
    cred2_file = original_cred2_file.name
    log.debug(f"  Found {len(original_cred2_files)} CRED2 files.  Using {cred2_file}")

    hdul = fits.open(data_path / cred2_file)

    # Create and Subtract Background
    ccddata = CCDData.read(data_path / cred2_file, unit="adu", memmap=False)
    source_mask = photutils.make_source_mask(hdul[0].data, 10, 100)
    bkg = photutils.Background2D(ccddata,
                                 box_size=128,
                                 mask=source_mask,
                                 sigma_clip=stats.SigmaClip())
    image_data = ccddata.data - bkg.background.value
#     image_data = ccddata.data - np.percentile(ccddata.data, 48)
    log.debug(f"  CRED2 mode = {mode(ccddata.data)} ({mode(image_data)} after background sub)")

    log.debug("Running median CR reject to get rid of bad pixels")
    image_data, mask = ccdproc.cosmicray_median(image_data, mbox=7, gbox=0, rbox=7)

    dx = 60
    dy = 50
    subframe = image_data[y0-dy:y0+dy,x0-dx:x0+dx]
    dx1, dy1 = centroid_com(subframe)
#     dx1, dy1 = centroid_2dg(subframe)
    x1 = x0 - dx + dx1
    y1 = y0 - dy + dy1

    log.debug(f"  Iteration 1: {x1:.1f} {y1:.1f} ({initial_x:.1f} {initial_y:.1f})")

    # Iterate on fit with smaller box
    if iterate is True:
        dx = 35
        dy = 30
        subframe = image_data[int(y1)-dy:int(y1)+dy,int(x1)-dx:int(x1)+dx]
        dx2, dy2 = centroid_com(subframe)
    #     dx2, dy2 = centroid_2dg(subframe)
        x2 = int(x1) - dx + dx2
        y2 = int(y1) - dy + dy2
    else:
        x2 = x1
        y2 = y1

    log.debug(f"  Iteration 2: {x2:.1f} {y2:.1f} ({initial_x:.1f} {initial_y:.1f})")

    # Third iteration
    if iterate is True:
        dx = 35
        dy = 30
        subframe = image_data[int(y2)-dy:int(y2)+dy,int(x2)-dx:int(x2)+dx]
        dx3, dy3 = centroid_com(subframe)
    #     dx3, dy3 = centroid_2dg(subframe)
        x3 = int(x2) - dx + dx3
        y3 = int(y2) - dy + dy3
    else:
        x3 = x1
        y3 = y1

    log.debug(f"  Iteration 3: {x3:.1f} {y3:.1f} ({initial_x:.1f} {initial_y:.1f})")

    if fig is not None:
        plt.figure(num=fig.number)
        plt.subplot(ny+1,nx,imno)
        title_string = f"{cred2_file}:\nx,y = ({x3:.1f}, {y3:.1f}) ({initial_x:.1f}, {initial_y:.1f})"
#         title_string = f"{cred2_file}"
        plt.title(title_string, size=8)
        norm = viz.ImageNormalize(hdul[0].data, interval=viz.AsymmetricPercentileInterval(1.5,100),
                                  stretch=viz.LogStretch())
        plt.imshow(subframe, interpolation='none', cmap='gray', origin='lower', norm=norm)
#         plt.plot(dx1, dy1, 'rx', alpha=0.3)
        if initial_x is not None and initial_y is not None:
            plt.plot(initial_x - x2 + dx, initial_y - y2 + dy, 'bx')
            plt.arrow(initial_x - x2 + dx, initial_y - y2 + dy,
                      dx3-(initial_x - x2 + dx),
                      dy3-(initial_y - y2 + dy),
                      color='g', alpha=0.5,
                      head_width=0.1, length_includes_head=True)
        plt.plot(dx3, dy3, 'r+')
        plt.gca().set_aspect('equal', 'box')
#         plt.gca().set_yticks([])
#         plt.gca().set_xticks([])
    log.debug(f"  X: {initial_x:.1f} --> {x3:.1f}")
    log.debug(f"  Y: {initial_y:.1f} --> {y3:.1f}")

    return x3, y3


##-------------------------------------------------------------------------
## show_FVC_image
##-------------------------------------------------------------------------
def show_FVC_image(x, y, images, fluxes, camera='SCI',
                   data_path='/s/sdata1701/kpfeng/2022oct16/FVC1',
                   x0=800, y0=600,
                   fig=None, imno=1):
    data_path = Path(data_path)
    nx = len(set(set(images['x'])))
    ny = len(set(set(images['y'])))
    tol = 0.001
    original_fvc_files = images[(abs(images['x'] - x) < tol) & (abs(images['y'] - y) < tol) & (images['camera'] == camera)]['file']
    original_fvc_file = Path(original_fvc_files[0])
    fvc_file = original_fvc_file.name
    log.debug(f"  Found {len(original_fvc_files)} {camera} FVC files.  Using {fvc_file}")

    hdul = fits.open(data_path / fvc_file)
    image_data = hdul[0].data
    dx = 200
    dy = 200
    subframe = image_data[y0-dy:y0+dy,x0-dx:x0+dx]

    if fig is not None:
        plt.figure(num=fig.number)
        plt.subplot(ny+1,nx,imno)
        title_string = f"{fvc_file}"
        plt.title(title_string, size=8)
        norm = viz.ImageNormalize(hdul[0].data, interval=viz.AsymmetricPercentileInterval(0.2,99.9),
                                  stretch=viz.LogStretch())
        plt.imshow(subframe, cmap='gray', origin='lower', norm=norm)
        radius = {'EXT': 27, 'SCI': 40, 'CAHK': 40}[camera]
        circ = plt.Circle((dx, dy), radius=radius, alpha=0.25,
                          edgecolor='red', fill=False)
        plt.plot(dx, dy, 'r+', alpha=0.25)
        plt.gca().add_patch(circ)
        plt.gca().set_yticks([])
        plt.gca().set_xticks([])


if __name__ == '__main__':
    analyze_grid_search(args.datetimestr,
                        flux_prefix=args.flux_prefix,
                        fiber=args.fiber,
                        FVCs=args.FVCs.split(','),
                        data_path=args.data_path)
