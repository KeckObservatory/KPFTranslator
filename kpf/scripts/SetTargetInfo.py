import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


##-------------------------------------------------------------------------
## SetTargetInfo
##-------------------------------------------------------------------------
class SetTargetInfo(KPFScript):
    '''Set the target info keywords based on the target information in the OB.

    ### ARGS
    **OB**: (`dict`) A fully specified observing block (OB) or at least the
            target components of an OB.
    '''
    @classmethod
    def pre_condition(cls, args, OB=None):
        pass

    @classmethod
    def perform(cls, args, OB=None):
        if OB is None:
            targ = args
        else:
            targ = OB.Target.to_dict()

        log.info(f"Setting target parameters")
        kpfconfig = ktl.cache('kpfconfig')
        kpf_expmeter = ktl.cache('kpf_expmeter')
        kpfconfig['TARGET_NAME'].write(targ.get('TargetName', ''))
        kpfconfig['TARGET_GAIA'].write(targ.get('GaiaID', ''))
        kpfconfig['TARGET_2MASS'].write(targ.get('2MASSID', ''))
        kpfconfig['TARGET_GMAG'].write(targ.get('Gmag', ''))
        kpfconfig['TARGET_JMAG'].write(targ.get('Jmag', ''))
        TARGPLAX = OB.get('Parallax', 0)
        kpfconfig['TARGET_PAR'].write(f"{TARGPLAX:.3f}")
        TARGRADV = OB.get('RadialVelocity', 0)
        kpfconfig['TARGET_RADV'].write(f"{TARGRADV:.3f}")

        TARGET_TEFF = targ.get('Teff', 45000)
        try:
            kpf_expmeter['TARGET_TEFF'].write(float(TARGET_TEFF))
        except:
            log.warning(f"Unable to set kpf_expmeter.TARGET_TEFF to {TARGET_TEFF} ({type(TARGET_TEFF)})")

    @classmethod
    def post_condition(cls, args, OB=None):
        pass
