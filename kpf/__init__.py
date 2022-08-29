from pathlib import Path

from ddoitranslatormodule.BaseInstrument import InstrumentBase

from .utils import *

class KPFTranslatorFunction(InstrumentBase):
    def _config_location(cls, args):
    """
    Return the fullpath + filename of default configuration file.
    """
    cfg_path_base = Path(__file__)
    config_file = cfg_path_base / Path('kpf_config.ini')
    if config_file.exists() is True:
        return [f"{config_file}"]
    else:
        return []
