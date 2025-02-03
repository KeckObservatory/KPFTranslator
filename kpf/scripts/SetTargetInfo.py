import ktl

from kpf import log, cfg, check_input
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
        dcs = ktl.cache('dcs1')
        kpfconfig['TARGET_NAME'].write(targ.get('TargetName', ''))
        kpfconfig['TARGET_GAIA'].write(targ.get('GaiaID', ''))
        kpfconfig['TARGET_2MASS'].write(targ.get('2MASSID', ''))
        kpfconfig['TARGET_GMAG'].write(targ.get('Gmag', ''))
        kpfconfig['TARGET_JMAG'].write(targ.get('Jmag', ''))

        TARGET_TEFF = targ.get('Teff', 45000)
        try:
            kpf_expmeter['TARGET_TEFF'].write(float(TARGET_TEFF))
        except:
            log.warning(f"Unable to set kpf_expmeter.TARGET_TEFF to {TARGET_TEFF} ({type(TARGET_TEFF)})")

        TARGPLAX = targ.get('Parallax', 0)
        try:
            dcs['TARGPLAX'].write(float(TARGPLAX))
        except:
            log.warning(f"Unable to set dcs.TARGPLAX to {TARGPLAX} ({type(TARGPLAX)})")

        TARGRADV = targ.get('RadialVelocity', 0)
        try:
            dcs['TARGRADV'].write(float(TARGRADV))
        except:
            log.warning(f"Unable to set dcs.TARGRADV to {TARGRADV} ({type(TARGRADV)})")

    @classmethod
    def post_condition(cls, args, OB=None):
        pass
