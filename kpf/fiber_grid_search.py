from pathlib import Path
import logging
from datetime import datetime
import time

from astropy.table import Table, Row

import ktl
import keygrabber

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from .fiu.InitializeTipTilt import InitializeTipTilt


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
this_file_name = Path(__file__).name.replace(".py", "")

log = logging.getLogger(f'{this_file_name}')
log.setLevel(logging.DEBUG)
## Set up console output
LogConsoleHandler = logging.StreamHandler()
LogConsoleHandler.setLevel(logging.INFO)
LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
LogConsoleHandler.setFormatter(LogFormat)
log.addHandler(LogConsoleHandler)
## Set up file output
now = datetime.utcnow()
now_str = now.strftime('%Y%m%dat%H%M%S')
LogFileName = Path(f'~/joshw/logs/{this_file_name}_{now_str}.log').expanduser()
LogFileHandler = logging.FileHandler(LogFileName)
LogFileHandler.setLevel(logging.DEBUG)
LogFileHandler.setFormatter(LogFormat)
log.addHandler(LogFileHandler)


##-------------------------------------------------------------------------
## fiber_grid_search
##-------------------------------------------------------------------------
class fiber_grid_search(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        log.info("###########")
        if args.get('comment', '') != '': log.info(args.get('comment', ''))
        log.info("args = {args}")
        log.info("###########")

        images_file = Path(f'~/logs/{this_file_name}_images_{now_str}.txt').expanduser()
        fluxes_file = Path(f'~/logs/{this_file_name}_fluxes_{now_str}.txt').expanduser()

        images = Table(names=('file', 'camera', 'dx', 'dy'),
                       dtype=('a90',  'a10',    'f4', 'f4'))
        expmeter_flux = Table(names=('dx', 'dy', 'f1', 'f2', 'f3', 'f4'),
                              dtype=('f4', 'f4', 'f4', 'f4', 'f4', 'f4'))

        nx = args.get('nx', 3)
        ny = args.get('ny', 3)
        dx = args.get('dx', 0.25)
        dy = args.get('dy', 0.25)
        xis = [xi for xi in range(int(-nx/2),int((nx+1)/2),1)]
        yis = [yi for yi in range(int(-ny/2),int((ny+1)/2),1)]
        xs = [xi*dx for xi in xis]
        ys = [yi*dy for yi in yis]

        # Set up tip tilt system
        InitializeTipTilt.execute({})


    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        """
        The arguments to add to the command line interface.
        """
        args_to_add = OrderedDict()
        args_to_add['nx'] = {'type': int,
                    'help': 'Number of grid points in the X direction'}
        args_to_add['ny'] = {'type': int,
                    'help': 'Number of grid points in the Y direction'}
        args_to_add['dx'] = {'type': float,
                    'help': 'Distance (arcsec) between grid points in X'}
        args_to_add['dy'] = {'type': float,
                    'help': 'Distance (arcsec) between grid points in Y'}
        args_to_add['CRED2'] = {'type': bool,
                    'help': 'Use the CRED2/guide camera'}
        args_to_add['SCI'] = {'type': bool,
                    'help': 'Use the SCI FVC camera'}
        args_to_add['CAHK'] = {'type': bool,
                    'help': 'Use the CAHK FVC camera'}
        args_to_add['EXT'] = {'type': bool,
                    'help': 'Use the EXT FVC camera'}
        args_to_add['ExpMeter'] = {'type': bool,
                    'help': 'Use the ExpMeter'}
        args_to_add['comment'] = {'type': str,
                    'help': 'Comment for log'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
