import argparse
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

from matplotlib import animation
from matplotlib import pyplot as plt


##-------------------------------------------------------------------------
## Parse Command Line Arguments
##-------------------------------------------------------------------------
## create a parser object for understanding command-line arguments
p = argparse.ArgumentParser(description='''
''')
## add arguments
p.add_argument('file', type=str,
               help="Input FITS file with guider cube")
args = p.parse_args()


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
            print(f"Found: {hdu.name}")
            guide_origins_hdu = hdu
        if hdu.name == 'guider_avg':
            print(f"Found: {hdu.name}")
            guide_cube_header_hdu = hdu
        if hdu.name == 'PRIMARY':
            print(f"Found: {hdu.name}")
            L0_header_hdu = hdu
        if hdu.name == 'guider_cube':
            print(f"Found: {hdu.name}")
            guider_cube = nddata.CCDData(hdu.data, unit='adu')
    # Assemble metadata
    metadata = {'FPS': guide_cube_header_hdu.header.get('FPS', None),
                'DATE-BEG': guide_cube_header_hdu.header.get('DATE-BEG', None),
                'DATE-END': guide_cube_header_hdu.header.get('DATE-END', None),
                'IMTYPE': L0_header_hdu.header.get('IMTYPE', None),
                'Gmag': L0_header_hdu.header.get('GAIAMAG', None),
                'Jmag': L0_header_hdu.header.get('2MASSMAG', None),
                'TARGNAME': L0_header_hdu.header.get('FULLTARG', None),
                'IMTYPE': L0_header_hdu.header.get('IMTYPE', None),
                'GAIN': guide_cube_header_hdu.header.get('Gain', None)
               }
    if metadata['FPS'] is None:
        # Assume 100 FPS
        metadata['FPS'] = 100
    if metadata['DATE-BEG'] is None:
        metadata['DATE-BEG'] = L0_header_hdu.header.get('DATE-BEG', None)
    if metadata['DATE-END'] is None:
        metadata['DATE-END'] = L0_header_hdu.header.get('DATE-END', None)

#     if metadata['IMTYPE'] not in [None, 'Object']:
#         return None, None, None
    if guide_origins_hdu is None:
        return None, metadata, guider_cube
    else:
        return Table(guide_origins_hdu.data), metadata, guider_cube



##-------------------------------------------------------------------------
## generate_cube_gif
##-------------------------------------------------------------------------
def generate_cube_gif(file, giffile):
    print('Generating animation')
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
#         writer = animation.ImageMagickWriter(fps=fps)
#         writer = animation.ImageMagickFileWriter(fps=fps)
#         writer = animation.FFMpegWriter(fps=fps)
        writer = animation.PillowWriter(fps=fps)

    # ims is a list of lists, each row is a list of artists to draw in the
    # current frame; here we are just animating one artist, the image, in
    # each frame
    print('Building individual frames')
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

    print('Building animation')
    ani = animation.ArtistAnimation(fig, ims, interval=1000/fps, blit=True,
                                    repeat_delay=1000)
    print(f'Writing {giffile} using {writer}')
    p = Path(giffile)
    if p.expanduser().exists(): p.unlink()
    ani.save(f"{giffile}", writer)
    print('Done')


if __name__ == '__main__':
    file = Path(args.file)
    giffile = file.name.replace('.fits', '.gif')
    generate_cube_gif(file, giffile)
