import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


##-------------------------------------------------------------------------
## SetTargetInfo
##-------------------------------------------------------------------------
class SetTargetInfo(KPFTranslatorFunction):
    '''Set the target info keywords based on the target information in the OB.

    ARGS:
    =====
    :OB: `dict` A fully specified observing block (OB) or at least the target
         components of an OB.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, OB, logger, cfg):
        log.info(f"Setting target parameters")
        kpfconfig = ktl.cache('kpfconfig')
        kpf_expmeter = ktl.cache('kpf_expmeter')
        dcs = ktl.cache('dcs1')
        kpfconfig['TARGET_NAME'].write(OB.get('TargetName', ''))
        kpfconfig['TARGET_GAIA'].write(OB.get('GaiaID', ''))
        kpfconfig['TARGET_2MASS'].write(OB.get('2MASSID', ''))
        kpfconfig['TARGET_GMAG'].write(OB.get('Gmag', ''))
        kpfconfig['TARGET_JMAG'].write(OB.get('Jmag', ''))

        TARGET_TEFF = OB.get('Teff', 45000)
        try:
            kpf_expmeter['TARGET_TEFF'].write(float(TARGET_TEFF))
        except:
            log.warning(f"Unable to set kpf_expmeter.TARGET_TEFF to {TARGET_TEFF} ({type(TARGET_TEFF)})")

        TARGPLAX = OB.get('Parallax', 0)
        try:
            dcs['TARGPLAX'].write(float(TARGPLAX))
        except:
            log.warning(f"Unable to set dcs.TARGPLAX to {TARGPLAX} ({type(TARGPLAX)})")

        TARGRADV = OB.get('RadialVelocity', 0)
        try:
            dcs['TARGRADV'].write(float(TARGRADV))
        except:
            log.warning(f"Unable to set dcs.TARGRADV to {TARGRADV} ({type(TARGRADV)})")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
