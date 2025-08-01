from pathlib import Path

from astropy.io import fits
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
from astropy import units as u
try:
    from astroquery.vizier import Vizier
    Vizier.ROW_LIMIT=100
except:
    Vizier = None

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class GetGaiaStars(KPFFunction):
    '''Build a ds9 region file of Gaia catalog stars which ought to be present
    in the specified guider image.

    Args:
        file (str): The file to retrieve stars for.
    '''
    @classmethod
    def pre_condition(cls, args):
        if Vizier is None:
            raise FailedPreCondition('Unable to import astroquery.vizier')
        file = Path(args.get('file', '/tmp/CRED2.fits')).expanduser().absolute()
        if file.exists() is False:
            raise FailedPreCondition(f'Fould not find input file: {file}')

    @classmethod
    def perform(cls, args):
        catalog_id = cfg.get('stellar_catalog', 'catalog_id',
                             fallback='I/345/gaia2')
        search_radius = cfg.getfloat('stellar_catalog', 'search_radius',
                                     fallback=28)
        ds9_color = cfg.get('stellar_catalog', 'ds9_color',
                            fallback='cyan')
        ds9_font = cfg.get('stellar_catalog', 'ds9_font',
                           fallback='helvetica 10 normal roman')
        requery_threshold = cfg.getfloat('stellar_catalog', 'requery_threshold',
                                         fallback=5)
        region_file = Path('~/.CRED2_auto_regions.reg').expanduser()
        cntr_file = Path('~/.CRED2_auto_regions.cntr').expanduser()

        file = Path(args.get('file', './junk.fits')).expanduser().absolute()
#         hdul = fits.open(file)
        header = fits.getheader(file)
        w = WCS(header)
#         cntr = w.pixel_to_world(hdul[0].data.shape[0]/2, hdul[0].data.shape[1]/2)
        cntr = w.pixel_to_world(int(header.get('NAXIS2'))/2, int(header.get('NAXIS1'))/2)
        if cntr_file.exists() is False:
            with open(cntr_file, 'w') as FO:
                FO.write(cntr.to_string('hmsdms', precision=2))
        else:
            with open(cntr_file, 'r') as FO:
                cntr_file_string = FO.readlines()
            file_cntr = SkyCoord(cntr_file_string, unit=(u.hourangle, u.deg),
                                 frame='icrs')
            sep = file_cntr.separation(cntr)
            # If we're in a new position, query for a new catalog of stars and
            # write a new region file
            if sep[0].to(u.arcsec).value > requery_threshold:
                print(f'Querying for catalog: {cntr.to_string("hmsdms", precision=2)}')
                gaia = Vizier.query_region(cntr, radius=search_radius*u.arcsec,
                                           catalog=catalog_id)[0]
                regions = [f'# Region file format: DS9 version 4.1',
                           f'global color={ds9_color} dashlist=8 3 width=1 font="{ds9_font}"',
                          ]
                for star in gaia:
                    sc = SkyCoord(star['RA_ICRS'], star['DE_ICRS'],
                                  unit=(u.deg, u.deg), frame='icrs')
                    coord_string = sc.to_string('hmsdms', sep=':', precision=2).replace(' ', ',')
                    newline = f"circle({coord_string},0.5\")"# \# text=\{"#\}"
                    newline += " # text={"
                    newline += f"{star['RPmag']:.1f}"
                    newline += "}"
                    regions.append(newline)
                if region_file.exists(): region_file.unlink()
                with open(region_file, 'w') as FO:
                    for line in regions:
                        FO.write(line+'\n')

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('file', type=str,
                            help='The CRED2 file to retrieve stars for')
        return super().add_cmdline_args(parser)
