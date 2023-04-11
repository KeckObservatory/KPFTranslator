import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


##-------------------------------------------------------------------------
## SetTargetInfo
##-------------------------------------------------------------------------
class SetTargetInfo(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, OB, logger, cfg):
        log.info(f"Setting target parameters")
        kpfconfig['TARGET_NAME'].write(OB.get('TargetName', ''))
        kpfconfig['TARGET_GAIA'].write(OB.get('GaiaID', ''))
        kpfconfig['TARGET_2MASS'].write(OB.get('2MASSID', ''))
        kpfconfig['TARGET_GMAG'].write(OB.get('Gmag', ''))
        kpfconfig['TARGET_JMAG'].write(OB.get('Jmag', ''))
        kpf_expmeter['TARGET_TEFF'].write(float(OB.get('Teff', 0)))
        dcs['TARGPLAX'].write(OB.get('Parallax', 0))
        dcs['TARGRADV'].write(OB.get('RadialVelocity', 0))

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
