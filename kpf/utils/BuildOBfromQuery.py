import re
from astropy.coordinates import SkyCoord
from astroquery.vizier import Vizier
from astroquery.simbad import Simbad

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import FailedPostCondition, check_input


def get_names_from_gaiaid(gaiaid):
    # Using Gaia ID, query for HD number and query for 2MASS ID
    hdnumber = '?'
    twomassid = '?'
    names = Simbad.query_objectids(f"Gaia DR3 {gaiaid}")
    for name in names:
        is2mass = re.match('^2MASS\s+(J[\d\+\-]+)', name[0])
        if is2mass is not None:
            twomassid = is2mass.group(1)
        ishd = re.match('^HD\s+([\d\+\-]+)', name[0])
        if ishd is not None:
            hdnumber = ishd.group(1)
    return {'TargetName': hdnumber, '2MASSID': twomassid}


def get_Jmag(twomassid):
    cat = 'II/246/out'
    cols = ['2MASS', 'Jmag']
    r = Vizier(catalog=cat, columns=cols).query_constraints(Source=twomassid)[0]
    Jmag_masked = r['Jmag'].mask[0]
    Jmag = f"{r['Jmag'][0]:.2f}" if Jmag_masked == False else '?'
    return {'Jmag': Jmag}


def get_gaia_parameters(gaiaid):
    cat = 'I/350/gaiaedr3'
#     cols = ['RA_ICRS', 'DE_ICRS', 'Source', 'Plx',
#             'PM', 'pmRA', 'e_pmRA', 'pmDE', 'e_pmDE',
#             'Gmag', 'e_Gmag', 'RVDR2', 'e_RVDR2',
#             'Tefftemp', 'loggtemp',
#             'GmagCorr', 'e_GmagCorr']
    cols = ['RA_ICRS', 'DE_ICRS', 'Source', 'Plx', 'Gmag', 'RVDR2', 'Tefftemp']
    r = Vizier(catalog=cat, columns=cols).query_constraints(Source=gaiaid)[0]
    plx = f"{float(r['Plx']):.2f}" if r['Plx'].mask[0] == False else '?'
    rv = f"{float(r['RVDR2']):.2f}" if r['RVDR2'].mask[0] == False else '?'
    Gmag = f"{float(r['Gmag']):.2f}" if r['Gmag'].mask[0] == False else '?'
    Teff = f"{float(r['Tefftemp']):.0f}" if r['Tefftemp'].mask[0] == False else '?'
    gaia_params = {'Parallax': plx,
                   'RadialVelocity': rv,
                   'Gmag': Gmag,
                   'Teff': Teff,
                   'RA_ICRS': float(r['RA_ICRS']),
                   'DE_ICRS': float(r['DE_ICRS']),
                   }
    return gaia_params


##-------------------------------------------------------------------------
## BuildOBfromQuery
##-------------------------------------------------------------------------
class BuildOBfromQuery(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'GaiaID')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        gaiaid = args.get('GaiaID')
        OB = ["# Built using BuildOBfromQuery tool",
              "# --> Observer must replace all ? below with real values <--",
              "Template_Name: kpf_sci",
              "Template_Version: 0.6",
              ""]

        # Get target name and 2MASS ID from Gaia ID
        names = get_names_from_gaiaid(gaiaid)

        # Using 2MASS ID query for Jmag
        twomass_params = get_Jmag(names['2MASSID'])
        
        # Using Gaia ID, query for Gaia parameters
        gaia_params = get_gaia_parameters(gaiaid)

        OB.append("# Target Info")
        OB.append(f"TargetName: {names['TargetName']}")
        OB.append(f"GaiaID: DR3 {gaiaid}")
        OB.append(f"2MASSID: {names['2MASSID']}")
        OB.append(f"Parallax: {gaia_params['Parallax']} # mas")
        OB.append(f"RadialVelocity: {gaia_params['RadialVelocity']} # km/s")
        OB.append(f"Gmag: {gaia_params['Gmag']}")
        OB.append(f"Jmag: {twomass_params['Jmag']}")
        OB.append(f"Teff: {gaia_params['Teff']}")
        OB.append("")
        OB.append("# Guider Setup")
        OB.append("GuiderMode: auto         # auto or manual. If manual, gain and FPS values below will be used")
        OB.append("GuiderCamGain: high      # Options are low, medium, high")
        OB.append("GuiderFPS: 100           # Frames per second")
        OB.append("")
        OB.append("# Spectrograph Setup")
        OB.append("TriggerCaHK: True        # Take data with the Ca H&K detector")
        OB.append("TriggerGreen: True       # Take data with the Green detector")
        OB.append("TriggerRed: True         # Take data with the Red detector")
        OB.append("")
        OB.append("# Observations (repeat the indented block below to take multiple observations)")
        OB.append("SEQ_Observations:")
        OB.append(" - Object: ?             # Free text field for notes")
        OB.append("   nExp: ?               # Number of exposures")
        OB.append("   Exptime: ?            # Individual exposure time")
        OB.append("   ExpMeterMode: monitor # Only monitor is supported for now")
        OB.append("   ExpMeterExpTime: ?    # Exposure time for exposure meter")
        OB.append("   TakeSimulCal: ?       # True or False, take simultaneous calibration data?")
        OB.append("   CalND1: ?             # Which ND filter to put in wheel 1")
        OB.append("   CalND2: ?             # Which ND filter to put in wheel 2")

        for line in OB:
            print(line)

        # Build Starlist line

        coord = SkyCoord(float(gaia_params['RA_ICRS']), float(gaia_params['DE_ICRS']), frame='icrs', unit='deg')
        coord_string = coord.to_string('hmsdms', sep=' ', precision=1)
        starlist_line = f"{names['TargetName']:16s}{coord_string} 2000 vmag={gaia_params['Gmag']}"
        print()
        print("Line for Keck star list:")
        print(starlist_line)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['GaiaID'] = {'type': str,
                                 'help': 'Gaia DR3 ID to query for (e.g. "35227046884571776")'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
