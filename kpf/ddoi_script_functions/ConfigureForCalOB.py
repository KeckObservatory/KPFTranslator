from time import sleep
from packaging import version
import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from ..calbench import lamp_has_warmed_up
from ..calbench.CalLampPower import CalLampPower


class ConfigureForCalOB(KPFTranslatorFunction):
    '''Script which configures the instrument for Cal OBs.
    
    Can be called by `ddoi_script_functions.configure_for_science`.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
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
        OB_version = version.parse(OB_version)
        cfg = cls._load_config(cls, cfg)
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


if __name__ == '__main__':
    description = '''Runs script bypassing the translator command line tools. 
    Uses a YAML input file to get OB contents.
    '''
    p = argparse.ArgumentParser(description=description)
    p.add_argument('OBfile', type=int,
                   help="A yaml file describing the cal OB")
    args = p.parse_args()
    
    calOB = yaml.safe_load(open(args.OBfile, 'r'))
    ConfigureForCalSequence.execute(OB)
