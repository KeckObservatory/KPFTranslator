from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from .. import check_guider_is_saving, check_guider_is_active


class TakeSingleGuiderExposure(KPFTranslatorFunction):
    '''Take 
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return not check_guider_is_active() and not check_guider_is_saving()

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        exptime = kpfguide['EXPTIME'].read(binary=True)
        kpfguide['EXPOSE'].write('yes')
        lastfile = kpfguide['LASTFILE']
        lastfile.monitor()
        lastfile.wait(timeout=exptime+1) # Wait for update which signals a new file

    @classmethod
    def post_condition(cls, args, logger, cfg):
        lastfile = kpfguide['LASTFILE']
        lastfile.monitor()
        new_file = Path(outdir) / Path(f"{lastfile}")
        print(f"{new_file}")
        return new_file.exists()
