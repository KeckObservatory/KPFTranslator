from pathlib import Path

from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
from astropy import units as u
try:
    from astroquery.vizier import Vizier
    Vizier.ROW_LIMIT=100
except:
    Vizier = None
    

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

class GetGaiaStars(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        file = Path(args.get('file', './junk.fits')).expanduser().absolute()
        return (Vizier is not None) and (file.exists() is True)

    @classmethod
    def perform(cls, args, logger, cfg):
        file = Path(args.get('file', './junk.fits')).expanduser().absolute()
        hdul = fits.open(file)
        w = WCS(hdul[0].header)
        cntr = w.pixel_to_world(hdul[0].data.shape[0]/2, hdul[0].data.shape[1]/2)
        sc = SkyCoord(cntr[0], cntr[1], unit=(u.deg, u.deg), frame='icrs')

#         sc = SkyCoord('05 35 16.5 -05 23 22.9', unit=(u.hourangle, u.deg),
#                       frame='icrs')
        gaia = Vizier.query_region(sc, radius=30*u.arcsec,
                                   catalog='I/345/gaia2')[0]




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
