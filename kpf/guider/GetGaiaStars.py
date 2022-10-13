from collections import OrderedDict
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

# Suppress astropy log messages
from astropy import log as astropylog
astropylog.setLevel('ERROR')
import warnings
from astropy.io.fits.verify import VerifyWarning
warnings.simplefilter('ignore', category=VerifyWarning)

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

class GetGaiaStars(KPFTranslatorFunction):
    '''Build a ds9 region file of Gaia catalog stars which ought to be present
    in the specified guider image.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        file = Path(args.get('file', '/tmp/CRED2.fits')).expanduser().absolute()
        return (Vizier is not None) and (file.exists() is True)

    @classmethod
    def perform(cls, args, logger, cfg):
        cfg = cls._load_config(cls, cfg)
        catalog_id = cfg.get('stellar_catalog', 'catalog_id',
                             fallback='I/345/gaia2')
        search_radius = cfg.getfloat('stellar_catalog', 'search_radius',
                                     fallback=28)
        ds9_color = cfg.get('stellar_catalog', 'ds9_color',
                            fallback='cyan')
        ds9_font = cfg.get('stellar_catalog', 'ds9_font',
                           fallback='helvetica 10 normal roman')

        file = Path(args.get('file', './junk.fits')).expanduser().absolute()
        hdul = fits.open(file)
        w = WCS(hdul[0].header)
        cntr = w.pixel_to_world(hdul[0].data.shape[0]/2, hdul[0].data.shape[1]/2)
        gaia = Vizier.query_region(cntr, radius=search_radius*u.arcsec,
                                   catalog=catalog_id)[0]
        regions = [f'# Region file format: DS9 version 4.1',
                   f'global color={ds9_color} dashlist=8 3 width=1 font="{ds9_font}"',
                  ]
        for star in gaia:
            sc = SkyCoord(star['RA_ICRS'], star['DE_ICRS'], unit=(u.deg, u.deg), frame='icrs')
            coord_string = sc.to_string('hmsdms', sep=':', precision=2).replace(' ', ',')
            newline = f"circle({coord_string},0.5\")"# \# text=\{"#\}"
            newline += " # text={"
            newline += f"{star['RPmag']:.1f}"
            newline += "}"
            regions.append(newline)
        region_file = Path('~/.CRED2_auto_regions.reg').expanduser()
        if region_file.exists(): region_file.unlink()
        with open(region_file, 'w') as FO:
            for line in regions:
                FO.write(line+'\n')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        """
        The arguments to add to the command line interface.
        """
        args_to_add = OrderedDict()
        args_to_add['file'] = {'type': str,
                               'help': 'The CRED2 file to retrieve stars for.'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
