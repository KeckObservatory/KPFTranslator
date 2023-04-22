import os
from pathlib import Path

from ddoitranslatormodule.BaseFunction import TranslatorModuleFunction

import ktl


class KPFTranslatorFunction(TranslatorModuleFunction):

    def _cfg_location(cls, args):
        """
        Return the fullpath + filename of default configuration file.

        :param args: <dict> The OB (or portion of OB) in dictionary form

        :return: <list> fullpath + filename of default configuration
        """
        cfg_path_base = os.path.dirname(os.path.abspath(__file__))

        inst = 'kpf'
        cfg = f"{cfg_path_base}/ddoi_configurations/{inst}_inst_config.ini"
        config_files = [cfg]

        return config_files

    @classmethod
    def abort_execution(cls, args, logger, cfg):
        if cls.abortable != True:
            log.warning('Abort recieved, but this method is not aboratble.')
            return False
        
        kpfconfig = ktl.cache('kpfconfig')
        this_file = Path(__file__).name.replace(".py", "")
        running_file = kpfconfig['SCRIPTNAME'].read()
        if this_file != running_file:
            log.warning(f'Abort recieved, but this method {this_file} is not '
                        f'the running script {running_file}.')
            return False

        log.warning('Abort recieved, setting kpfconfig.SCRTIPSTOP=Yes')
        kpfconfig['SCRIPTSTOP'].write('Yes')

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass