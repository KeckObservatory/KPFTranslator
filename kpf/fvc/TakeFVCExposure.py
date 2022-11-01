from pathlib import Path
from collections import OrderedDict

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log
from . import fvc_is_ready


class TakeFVCExposure(KPFTranslatorFunction):
    '''Take an exposure with the specified fiber viewing camera
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        camera = args.get('camera', 'SCI')
        return fvc_is_ready(camera=camera)

    @classmethod
    def perform(cls, args, logger, cfg):
        camera = args.get('camera', 'SCI')
        kpffvc = ktl.cache('kpffvc')
        exptime = kpffvc[f'{camera}EXPTIME'].read(binary=True)
        kpffvc[f'{camera}EXPOSE'].write('yes', wait=args.get('wait', True))

        if args.get('wait', True) is True:
            lastfile = kpffvc[f'{camera}LASTFILE']
            lastfile.monitor()
            timeout = cfg.get('times', 'fvc_command_timeout', fallback=5)
            lastfile.wait(timeout=exptime+timeout) # Wait for update which signals a new file

    @classmethod
    def post_condition(cls, args, logger, cfg):
        camera = args.get('camera', 'SCI')
        kpffvc = ktl.cache('kpffvc')
        lastfile = kpffvc[f'{camera}LASTFILE']
        lastfile.monitor()
        new_file = Path(f"{lastfile}")
        log.debug(f"{camera}FVC LASTFILE: {new_file}")
        return new_file.exists()

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        """
        The arguments to add to the command line interface.
        """
        args_to_add = OrderedDict()
        args_to_add['camera'] = {'type': str,
                                 'help': 'The camera to use (SCI, CAHK, CAL, EXT).'}
        parser = cls._add_args(parser, args_to_add, print_only=False)

        parser = cls._add_bool_arg(parser, 'wait',
            'Return only after exposure is finished?', default=True)

        return super().add_cmdline_args(parser, cfg)
