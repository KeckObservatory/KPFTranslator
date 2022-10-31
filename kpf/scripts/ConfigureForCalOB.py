from time import sleep
from packaging import version
from pathlib import Path
from collections import OrderedDict
import yaml
import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from ..calbench.CalLampPower import CalLampPower


class ConfigureForCalOB(KPFTranslatorFunction):
    '''Script which configures the instrument for Cal OBs.
    
    Can be called by `ddoi_script_functions.configure_for_science`.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        if args.get('OBfile', None) is not None:
            OBfile = Path(args.get('OBfile')).expanduser()
            if OBfile.exists() is True:
                OB = yaml.safe_load(open(OBfile, 'r'))
                print(f"WARNING: Using OB information from file {OBfile}")
                args = OB

        # Check template name
        OB_name = args.get('Template_Name', None)
        if OB_name is None:
            return False
        if OB_name != 'kpf_cal':
            return False
        # Check template version
        OB_version = args.get('Template_Version', None)
        if OB_version is None:
            return False
        OB_version = version.parse(f"{OB_version}")
        cfg = cls._load_config(cls, cfg)
        print(cfg.sections())
        print(cfg['ob_keys'].sections())
        print(cfg.get('templates', OB_name))
        compatible_version = version.parse(cfg.get('templates', OB_name))
        if compatible_version != OB_version:
            return False
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # Power up needed lamps
        lamps = [x['CalSource'] for x in args.get('SEQ_Calibrations')]
        for lamp in lamps:
            CalLampPower.execute({'lamp': lamp, 'power': 'on'})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        lamps = [x['CalSource'] for x in args.get('SEQ_Calibrations')]
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
