from time import sleep
from packaging import version
from pathlib import Path
from collections import OrderedDict
import yaml
import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log
from ..calbench.CalLampPower import CalLampPower


class ConfigureForCalOB(KPFTranslatorFunction):
    '''Script which configures the instrument for Cal OBs.
    
    Can be called by `ddoi_script_functions.configure_for_science`.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):

        # Use file input for OB instead of args (temporary)
        if args.get('OBfile', None) is not None:
            OBfile = Path(args.get('OBfile')).expanduser()
            if OBfile.exists() is True:
                OB = yaml.safe_load(open(OBfile, 'r'))
                log.warning(f"Using OB information from file {OBfile}")
        else:
            msg = 'Passing OB as args not implemented'
            log.error(msg)
            raise NotImplementedError(msg)

        # Check template name
        OB_name = OB.get('Template_Name', None)
        if OB_name is None:
            return False
        if OB_name != 'kpf_cal':
            return False
        # Check template version
#         OB_version = OB.get('Template_Version', None)
#         if OB_version is None:
#             return False
#         OB_version = version.parse(f"{OB_version}")
#         compatible_version = version.parse(cfg.get('templates', OB_name))
#         if compatible_version != OB_version:
#             return False
        return True

    @classmethod
    def perform(cls, args, logger, cfg):

        # Use file input for OB instead of args (temporary)
        if args.get('OBfile', None) is not None:
            OBfile = Path(args.get('OBfile')).expanduser()
            if OBfile.exists() is True:
                OB = yaml.safe_load(open(OBfile, 'r'))
                log.warning(f"Using OB information from file {OBfile}")
        else:
            msg = 'Passing OB as args not implemented'
            log.error(msg)
            raise NotImplementedError(msg)

        # Power up needed lamps
        sequence = OB.get('SEQ_Calibrations')
        lamps = [x['CalSource'] for x in sequence]
        for lamp in lamps:
            log.info(f'Turning on {lamp}')
            CalLampPower.execute({'lamp': lamp, 'power': 'on'})

    @classmethod
    def post_condition(cls, args, logger, cfg):

        # Use file input for OB instead of args (temporary)
        if args.get('OBfile', None) is not None:
            OBfile = Path(args.get('OBfile')).expanduser()
            if OBfile.exists() is True:
                OB = yaml.safe_load(open(OBfile, 'r'))
                log.info(f"WARNING: Using OB information from file {OBfile}")
        else:
            raise NotImplementedError('Passing OB as args not implemented')

        sequence = OB.get('SEQ_Calibrations')
        lamps = [x['CalSource'] for x in sequence]
        successes = []
        for lamp in lamps:
            expr = f"($kpflamps.{lamp} == on)"
            cfg = cls._load_config(cls, cfg)
            timeout = cfg.get('times', 'lamp_response_time', fallback=1)
            success = ktl.waitFor(expr, timeout=timeout)
            successes.append(success)
        return np.all(np.array(successes))

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        """
        The arguments to add to the command line interface.
        """
        args_to_add = OrderedDict()
        args_to_add['OBfile'] = {'type': str,
                                 'help': ('A YAML fortmatted file with the OB '
                                          'to be executed. Will override OB '
                                          'data delivered as args.')}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
