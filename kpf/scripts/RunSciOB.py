from time import sleep
from packaging import version
from pathlib import Path
import yaml

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log
from ..calbench.CalLampPower import CalLampPower
from ..calbench.SetCalSource import SetCalSource
from ..calbench.SetFlatFieldFiberPos import SetFlatFieldFiberPos
from ..calbench.SetND1 import SetND1
from ..calbench.SetND2 import SetND2
from ..calbench.WaitForCalSource import WaitForCalSource
from ..calbench.WaitForFlatFieldFiberPos import WaitForFlatFieldFiberPos
from ..calbench.WaitForND1 import WaitForND1
from ..calbench.WaitForND2 import WaitForND2
from ..fvc.FVCPower import FVCPower
from ..spectrograph.SetObject import SetObject
from ..spectrograph.SetExptime import SetExptime
from ..spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from ..spectrograph.SetTimedShutters import SetTimedShutters
from ..spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from ..spectrograph.StartExposure import StartExposure
from ..spectrograph.WaitForReady import WaitForReady
from ..spectrograph.WaitForReadout import WaitForReadout
from ..fiu.ConfigureFIU import ConfigureFIU
from ..fiu.WaitForConfigureFIU import WaitForConfigureFIU
from .WaitForLampsWarm import WaitForLampsWarm


class RunSciOB(KPFTranslatorFunction):
    '''Script which executes a science OB.
    
    Can be called by `ddoi_script_functions.execute_observation`.
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
            raise NotImplementedError('Passing OB as args not implemented')

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
            raise NotImplementedError('Passing OB as args not implemented')

        log.info('-------------------------')
        log.info(f"Running RunSciOB")
        for key in OB:
            if key not in ['SEQ_Darks', 'SEQ_Calibrations']:
                log.debug(f"  {key}: {OB[key]}")
            else:
                log.debug(f"  {key}:")
                for entry in OB[key]:
                    log.debug(f"    {entry}")
        log.info('-------------------------')

        observations = OB.get('SEQ_Observations', [])

        raise NotImplementedError("Science OBs not implemented yet")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['OBfile'] = {'type': str,
                                 'help': ('A YAML fortmatted file with the OB '
                                          'to be executed. Will override OB '
                                          'data delivered as args.')}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)