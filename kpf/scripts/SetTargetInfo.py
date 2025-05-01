import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


##-------------------------------------------------------------------------
## SetTargetInfo
##-------------------------------------------------------------------------
class SetTargetInfo(KPFScript):
    '''Set the target info keywords based on the target information in the OB.

    Note that there is a unit mismatch problem in this code, but it is accounted
    for elsewhere. The dcs units for parallax are arcsec, but we are writing a
    value in milliarcsec to the keyword. We found this in early 2025 and have
    decided to leave the behavior the same and just make sure that the FITS
    header comment is updated to reflect the units of milliarcsec for the value.
    This works because dcs is being used here only as a carrier of this
    information and both the source (the OB) and the destination (FITS header)
    are now in agreement on units.

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

        TARGET_TEFF = targ.get('Teff', 45000)
        try:
            kpf_expmeter['TARGET_TEFF'].write(float(TARGET_TEFF))
        except:
            log.warning(f"Unable to set kpf_expmeter.TARGET_TEFF to {TARGET_TEFF} ({type(TARGET_TEFF)})")

        # Handle DCS target values
        dcs = ktl.cache('dcs1')
        if dcs['INSTRUME'].read() != 'KPF':
            log.debug('Instrument is not KPF. Not setting DCS values.')
            return

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
