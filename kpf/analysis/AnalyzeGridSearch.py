#!python3

## Import General Tools
from pathlib import Path
import argparse
import logging

from pathlib import Path
import numpy as np
from astropy.io import fits
from astropy import visualization as viz
from astropy import units as u
from astropy.table import Table
from astropy import stats
from astropy.nddata import CCDData
import photutils
from photutils.centroids import centroid_com, centroid_2dg

from matplotlib import pyplot as plt


##-------------------------------------------------------------------------
## Parse Command Line Arguments
##-------------------------------------------------------------------------
## create a parser object for understanding command-line arguments
p = argparse.ArgumentParser(description='''
''')
## add flags
p.add_argument("-v", "--verbose", dest="verbose",
    default=False, action="store_true",
    help="Be verbose! (default = False)")
## add options
# p.add_argument("--input", dest="input", type=str,
#     help="The input.")
## add arguments
# p.add_argument('argument', type=int,
#                help="A single argument")
# p.add_argument('allothers', nargs='*',
#                help="All other arguments")
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
                        log_path=Path(f'~/KPF_Engineering/logs').expanduser(),
                        datadir=None,
                        FVCs=['SCI'],
                        ):
    ks = [0,1,2,3]

    cred2_pixels = {'EMSky': (160, 256),
                    'Science': (335, 256),
                    'Sky': (510, 256)}[fiber]
    fvcsci_pixels = {'EMSky': None,
                     'Science': (800, 600),
                     'Sky': None}[fiber]
    fvcext_pixels = {'EMSky': None,
                     'Science': (650, 600),
                     'Sky': None}[fiber]
    if flux_prefix is None:
        flux_prefix = {'EMSky': 'bck',
                       'Science': 'cur',
                       'Sky': None}[fiber]


    if datadir is None:
        # Try to munge up the crappy Keck date string
        months = {1: 'jan', 2: 'feb', 3: 'mar', 4: 'apr', 5: 'may', 6: 'jun',
                  7: 'jul', 8: 'aug', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dec'}
        date_str = f"{date_time_string[0:4]}{months[int(date_time_string[4:6])]}{int(date_time_string[6:8])-1:02d}"
        datadir = Path('/s/sdata1701/kpfeng/') / date_str

    fluxes_file = log_path / Path(f'FiberGridSearch_fluxes_{date_time_string}.txt')
    images_file = log_path / Path(f'FiberGridSearch_images_{date_time_string}.txt')
    log_file = log_path / Path(f'FiberGridSearch_{date_time_string}.log')
    ouput_cred2_image_file = Path(f"{date_time_string}_CRED2_images.png")
    ouput_sci_image_file = Path(f"{date_time_string}_SCI_images.png")
    ouput_ext_image_file = Path(f"{date_time_string}_EXT_images.png")
    ouput_analysis_image_file = Path(f"{date_time_string}_fiber_location.png")

    flux_table = Table.read(fluxes_file, format='ascii.csv')
    log.info(f"Read in {fluxes_file.name} with {len(flux_table)} lines")

    images = Table.read(images_file, format='ascii.csv')
    nx = len(set(set(images['dx'])))
    ny = len(set(set(images['dy'])))
    log.info(f"Read in {images_file.name} with {len(images)} lines ({nx} x {ny} grid)")

    with open(log_file) as FO:
        lines = FO.readlines()
    comment = lines[1][30:].strip('\n')
    log.info(f"Log Comment: {comment}")

    xoffset = np.zeros((len(set(flux_table['i'])), len(set(flux_table['j']))))
    yoffset = np.zeros((len(set(flux_table['i'])), len(set(flux_table['j']))))
    # Prep ExpMeter flux analysis
    fluxes = np.zeros((4, len(set(flux_table['i'])), len(set(flux_table['j']))))
    # Prep CRED2 Analysis
    cred2_images_fig = plt.figure(figsize=(12,14))
    xcred2 = np.zeros((len(set(flux_table['i'])), len(set(flux_table['j']))))
    ycred2 = np.zeros((len(set(flux_table['i'])), len(set(flux_table['j']))))
    # Prep FVC Analysis
    if 'SCI' in FVCs:
        sci_FVC_images_fig = plt.figure(figsize=(12,12))
    if 'EXT' in FVCs:
        ext_FVC_images_fig = plt.figure(figsize=(12,12))

    # Loop over positions
    for imno,flux_entry in enumerate(flux_table):
        i = flux_entry['i']
        j = flux_entry['j']
        xoffset[j, i] = flux_entry['dx']
        yoffset[j, i] = flux_entry['dy']
        for k in ks:
            fluxes[k, j, i] = flux_entry[f'{flux_prefix}{k+1}']
        log.debug(f"  Determining CRED2 pixel for {flux_entry['dx']:.2f}, {flux_entry['dy']:.2f}")
        log.debug(f"  Centering image on {cred2_pixels}")
        x, y = show_CRED2_image(flux_entry['dx'], flux_entry['dy'],
                                images, flux_table,
                                datadir=datadir/'CRED2',
                                x0=cred2_pixels[0], y0=cred2_pixels[1],
                                fig=cred2_images_fig, imno=imno+1)
        xcred2[j, i] = x
        ycred2[j, i] = y
        if 'SCI' in FVCs and fvcsci_pixels is not None:
            log.debug(f"  Generating SCI FVC image centered on {fvcsci_pixels}")
            show_FVC_image(flux_entry['dx'], flux_entry['dy'],
                           images, flux_table, camera='SCI',
                           datadir=datadir/'FVC1',
                           x0=fvcsci_pixels[0], y0=fvcsci_pixels[1],
                           fig=sci_FVC_images_fig, imno=imno+1)
        if 'EXT' in FVCs and fvcext_pixels is not None:
            log.debug(f"  Generating EXT FVC image centered on {fvcext_pixels}")
            show_FVC_image(flux_entry['dx'], flux_entry['dy'],
                           images, flux_table, camera='EXT',
                           datadir=datadir/'FVC4',
                           x0=fvcext_pixels[0], y0=fvcext_pixels[1],
                           fig=ext_FVC_images_fig, imno=imno+1)

    # Plot CRED2 Positions of each offset
    plt.figure(num=cred2_images_fig.number)
    plt.subplot(ny+1,nx,nx*ny+2)
    plt.title('Grid positions in CRED2 pixel space', size=8)
    plt.plot(xcred2, ycred2, 'k+')
    plt.grid()
    plt.xlabel('CRED2 X')
    plt.xlabel('CRED2 Y')
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
    if 'EXT' in FVCs:
        log.info(f"Saving: {ouput_ext_image_file}")
        plt.figure(num=ext_FVC_images_fig.number)
        if ouput_ext_image_file.exists() is True:
            ouput_ext_image_file.unlink()
        plt.savefig(ouput_ext_image_file, bbox_inches='tight', pad_inches=0.10)

    # Generate figure of Flux values on offset grid and estimated fiber position
    cred2_pixel_of_fiber = []
    plt.figure(figsize=(10,14))
    for k in [0,1,2,3]:
        plt.subplot(3,2,k+1)
        # Find offset position of peak flux
        flux_map = fluxes[k,:,:]
        peak_pos_j, peak_pos_i = np.unravel_index(flux_map.argmax(), flux_map.shape)
        peak_xoffset = xoffset[peak_pos_j, peak_pos_i]
        peak_yoffset = yoffset[peak_pos_j, peak_pos_i]
        peak_xcred2 = xcred2[peak_pos_j, peak_pos_i]
        peak_ycred2 = ycred2[peak_pos_j, peak_pos_i]
        cred2_pixel_of_fiber.append((peak_xcred2, peak_ycred2))
        # Show image of exposure meter flux grid
        if k == 0:
            plot_title = f"{date_time_string}: {comment}\n"
        else:
            plot_title = ''
        plot_title += (f"ExpMeter band {k+1}\n"
                       f"Grid Pos = ({peak_xoffset:.2f}, {peak_yoffset:.2f}), "
                       f"CRED2 Pixel = ({peak_xcred2:5.1f}, {peak_ycred2:5.1f})\n"
                       f'Flux: (min, max) = ({min(flux_map.ravel()):.1e}, {max(flux_map.ravel()):.1e})'
                       )
        plt.title(plot_title, size=9)
        plt.imshow(flux_map, cmap='gray')
        plt.plot(peak_pos_i, peak_pos_j, 'r+')
        plt.gca().set_yticks([])
        plt.gca().set_xticks([])

    cred2_pixel_of_fiber = np.array(cred2_pixel_of_fiber)
    avg_x = cred2_pixel_of_fiber[:,0].mean()
    avg_y = cred2_pixel_of_fiber[:,1].mean()
    cred2_deltas_pix = np.array([(coord[0]-avg_x, coord[1]-avg_y) for coord in cred2_pixel_of_fiber])
    pixel_scale = 58 #mas/pix
    xrms = np.std(cred2_pixel_of_fiber[:,0])*pixel_scale
    yrms = np.std(cred2_pixel_of_fiber[:,1])*pixel_scale
    log.info(f"CRED2 X Deviations {xrms:.0f} mas RMS: {cred2_deltas_pix[:,0]*pixel_scale}")
    log.info(f"CRED2 X Deviations {yrms:.0f} mas RMS: {cred2_deltas_pix[:,1]*pixel_scale}")
    log.info(f"Saving: {ouput_analysis_image_file}")

    plt.subplot(3,2,(5,6))
    plt.title(f"CRED2 Positions in ExpMeter Bands: RMS=({xrms:.0f}, {yrms:.0f} mas)")
    symbols = ['b+', 'gx', 'yo', 'r^']
    for k in [0,1,2,3]:
        plt.plot(cred2_pixel_of_fiber[k,0], cred2_pixel_of_fiber[k,1], symbols[k],
                 label=f"ExpMeter Band {k+1}",
                 markersize=10)
    plt.plot(avg_x, avg_y, 'ko', markersize=20, alpha=0.4,
             label=f'Avg. Position ({avg_x:.1f}, {avg_y:.1f})')
#     plt.gca().set_aspect(1)
    plt.legend(loc='best')
    plt.grid()
    plt.xlabel('CRED2 X')
    plt.xlabel('CRED2 Y')

    if ouput_analysis_image_file.exists() is True:
        ouput_analysis_image_file.unlink()
    plt.savefig(ouput_analysis_image_file, bbox_inches='tight', pad_inches=0.10)

    return cred2_pixel_of_fiber


##-------------------------------------------------------------------------
## show_CRED2_image
##-------------------------------------------------------------------------
def show_CRED2_image(x, y, images, fluxes,
                     datadir='/s/sdata1701/kpfeng/2022oct16/CRED2',
                     x0=320, y0=256,
                     iterate=True,
                     fig=None, imno=1):
    datadir = Path(datadir)
    nx = len(set(set(images['dx'])))
    ny = len(set(set(images['dy'])))
    tol = 0.001
    original_cred2_files = images[(abs(images['dx'] - x) < tol) & (abs(images['dy'] - y) < tol) & (images['camera'] == 'CRED2')]['file']
    original_cred2_file = Path(original_cred2_files[0])
    cred2_file = original_cred2_file.name
    log.debug(f"  Found {len(original_cred2_files)} CRED2 files.  Using {cred2_file}")

    hdul = fits.open(datadir / cred2_file)

    # Create and Subtract Background
    ccddata = CCDData.read(datadir / cred2_file, unit="adu", memmap=False)
    source_mask = photutils.make_source_mask(hdul[0].data, 10, 100)
    bkg = photutils.Background2D(ccddata,
                                 box_size=128,
                                 mask=source_mask,
                                 sigma_clip=stats.SigmaClip())
    image_data = ccddata.data - bkg.background.value
#     image_data = ccddata.data - np.percentile(ccddata.data, 48)
    log.debug(f"  CRED2 mode = {mode(ccddata.data)} ({mode(image_data)} after background sub)")

    dx = 40
    dy = 40
    subframe = image_data[y0-dy:y0+dy,x0-dx:x0+dx]
    dx1, dy1 = centroid_com(subframe)
#     dx1, dy1 = centroid_2dg(subframe)
    x1 = x0 - dx + dx1
    y1 = y0 - dy + dy1

    # Iterate on fit with smaller box
    if iterate is True:
        dx = 25
        dy = 25
        subframe = image_data[int(y1)-dy:int(y1)+dy,int(x1)-dx:int(x1)+dx]
        dx2, dy2 = centroid_com(subframe)
    #     dx1, dy1 = centroid_2dg(subframe)
        x2 = int(x1) - dx + dx2
        y2 = int(y1) - dy + dy2
    else:
        x2 = x1
        y2 = y1

    # Third iteration
    if iterate is True:
        dx = 25
        dy = 25
        subframe = image_data[int(y2)-dy:int(y2)+dy,int(x2)-dx:int(x2)+dx]
        dx3, dy3 = centroid_com(subframe)
    #     dx1, dy1 = centroid_2dg(subframe)
        x3 = int(x2) - dx + dx3
        y3 = int(y2) - dy + dy3
    else:
        x3 = x1
        y3 = y1

    if fig is not None:
        plt.figure(num=fig.number)
        plt.subplot(ny+1,nx,imno)
        title_string = f"{cred2_file}:\nx,y = ({x1:.1f}, {y1:.1f})"
#         title_string = f"{cred2_file}"
        plt.title(title_string, size=8)
        norm = viz.ImageNormalize(hdul[0].data, interval=viz.AsymmetricPercentileInterval(1.5,100),
                                  stretch=viz.LogStretch())
        plt.imshow(subframe, cmap='gray', origin='lower', norm=norm)
#         plt.plot(dx1, dy1, 'rx', alpha=0.3)
        plt.plot(dx3, dy3, 'r+')
        plt.gca().set_yticks([])
        plt.gca().set_xticks([])

    return x2, y2


##-------------------------------------------------------------------------
## show_FVC_image
##-------------------------------------------------------------------------
def show_FVC_image(x, y, images, fluxes, camera='SCI',
                   datadir='/s/sdata1701/kpfeng/2022oct16/FVC1',
                   x0=800, y0=600,
                   fig=None, imno=1):
    datadir = Path(datadir)
    nx = len(set(set(images['dx'])))
    ny = len(set(set(images['dy'])))
    tol = 0.001
    original_fvc_files = images[(abs(images['dx'] - x) < tol) & (abs(images['dy'] - y) < tol) & (images['camera'] == camera)]['file']
    original_fvc_file = Path(original_fvc_files[0])
    fvc_file = original_fvc_file.name
    log.debug(f"  Found {len(original_fvc_files)} {camera} FVC files.  Using {fvc_file}")

    hdul = fits.open(datadir / fvc_file)
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
        plt.gca().set_yticks([])
        plt.gca().set_xticks([])


if __name__ == '__main__':
    # Oct 6
#     analyze_grid_search('20221007at122438', flux_prefix='f', fiber='Science', FVCs=['SCI', 'EXT'])
#     analyze_grid_search('20221007at123043', flux_prefix='f', fiber='Science', FVCs=['SCI', 'EXT'])
#     analyze_grid_search('20221007at123800', flux_prefix='f', fiber='Science', FVCs=['SCI', 'EXT'])
#     analyze_grid_search('20221007at125522', flux_prefix='f', fiber='Science', FVCs=['SCI', 'EXT'])
#     analyze_grid_search('20221007at133243', flux_prefix='f', fiber='Science', FVCs=['SCI', 'EXT'])
#     analyze_grid_search('20221007at134116', flux_prefix='f', fiber='Science', FVCs=['SCI', 'EXT'])
#     analyze_grid_search('20221007at134957', flux_prefix='f', fiber='Science', FVCs=['SCI', 'EXT'])
    analyze_grid_search('20221007at143218', flux_prefix='f', fiber='Science', FVCs=['SCI', 'EXT'])
    analyze_grid_search('20221007at144431', flux_prefix='f', fiber='Science', FVCs=['SCI', 'EXT'])
    # analyze_grid_search('20221007at122115', flux_prefix='f', x0=160, y0=256, FVCs=['SCI', 'EXT']) # Failed grid

    # Oct 16
#     analyze_grid_search('20221017at054732', fiber='EMSky', FVCs=[])
#     analyze_grid_search('20221017at055940', fiber='EMSky', FVCs=[])
#     analyze_grid_search('20221017at060401', fiber='EMSky', FVCs=[])
#     analyze_grid_search('20221017at061708', fiber='EMSky', FVCs=[])
#     analyze_grid_search('20221017at073300', fiber='EMSky', FVCs=[])
#     analyze_grid_search('20221017at080015', fiber='EMSky', FVCs=[])
#     analyze_grid_search('20221017at082551', fiber='EMSky', FVCs=[])
#     analyze_grid_search('20221017at084907', fiber='EMSky', FVCs=[])
#     analyze_grid_search('20221017at085828', fiber='EMSky', FVCs=[])
#     analyze_grid_search('20221017at091540', fiber='EMSky', FVCs=[])
#     analyze_grid_search('20221017at093334', fiber='EMSky', FVCs=[])
#     analyze_grid_search('20221017at094948', fiber='EMSky', FVCs=[])
    # analyze_grid_search('20221017at062242', x0=160, y0=256) # Failed grid
    # analyze_grid_search('20221017at063907', x0=160, y0=256) # Failed grid
    # analyze_grid_search('20221017at065709', x0=160, y0=256) # Failed grid
    # analyze_grid_search('20221017at082305', x0=160, y0=256) # Failed grid
