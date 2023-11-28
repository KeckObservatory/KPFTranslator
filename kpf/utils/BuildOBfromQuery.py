import re
from astropy.coordinates import SkyCoord
from astroquery.vizier import Vizier
from astroquery.simbad import Simbad

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.OB_GUI.OBs import ScienceOB


def get_names_from_gaiaid(gaiaid):
    # Using Gaia ID, query for HD number and query for 2MASS ID
    hdnumber = ''
    twomassid = ''
    names = Simbad.query_objectids(f"Gaia DR3 {gaiaid}")
    if names is None:
        return None
    for name in names:
        is2mass = re.match('^2MASS\s+(J[\d\+\-]+)', name[0])
        if is2mass is not None:
            twomassid = is2mass.group(1)
        ishd = re.match('^HD\s+([\d\+\-]+)', name[0])
        if ishd is not None:
            hdnumber = ishd.group(1)
    return {'TargetName': hdnumber, '2MASSID': twomassid,
            'all': [x[0] for x in names]}


def get_Jmag(twomassid):
    cat = 'II/246/out'
    cols = ['2MASS', 'Jmag', 'RAJ2000', 'DEJ2000', '_r']
    result = Vizier(catalog=cat, columns=cols).query_object(twomassid)
    if len(result) == 0:
        return {'Jmag': ''}
    table = result[0]
    table.sort('_r')
    if float(table['_r'][0]) > 1: # find better threshold
        return {'Jmag': ''}
    if table['Jmag'].mask[0] == True:
        return {'Jmag': ''}
    Jmag = f"{table['Jmag'][0]:.2f}"
    return {'Jmag': Jmag}


def get_gaia_parameters(gaiaid):
    cat = 'I/350/gaiaedr3'
    cols = ['RA_ICRS', 'DE_ICRS', 'Source', 'Plx', 'Gmag', 'RVDR2', 'Tefftemp']
    r = Vizier(catalog=cat, columns=cols).query_constraints(Source=gaiaid)[0]
    plx = f"{float(r['Plx']):.2f}" if r['Plx'].mask[0] == False else '0'
    rv = f"{float(r['RVDR2']):.2f}" if r['RVDR2'].mask[0] == False else '0'
    Gmag = f"{float(r['Gmag']):.2f}" if r['Gmag'].mask[0] == False else ''
    Teff = f"{float(r['Tefftemp']):.0f}" if r['Tefftemp'].mask[0] == False else '45000'
    gaia_params = {'Parallax': plx,
                   'RadialVelocity': rv,
                   'Gmag': Gmag,
                   'Teff': Teff,
                   'RA_ICRS': float(r['RA_ICRS']),
                   'DE_ICRS': float(r['DE_ICRS']),
                   }
    return gaia_params


def form_starlist_line(name, ra, dec, vmag=None, frame='icrs', unit='deg'):
    coord = SkyCoord(float(ra), float(dec), frame=frame, unit=unit)
    coord_string = coord.to_string('hmsdms', sep=' ', precision=2)
    line = f"{name:15s} {coord_string} 2000.0"
    if vmag not in [None, '']:
        try:
            line += f" vmag={float(vmag):.2f}"
        except:
            pass
    return line


##-------------------------------------------------------------------------
## BuildOBfromQuery
##-------------------------------------------------------------------------
class BuildOBfromQuery(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'GaiaID')

    @classmethod
    def perform(cls, args, logger, cfg):
        gaiaid = args.get('GaiaID')
        observation = {'ExpMeterMode': "monitor",
                       'AutoExpMeter': "False",
                       'TakeSimulCal': "True"}
        OB = ScienceOB({'GaiaID': f"DR3 {gaiaid}",
                        'SEQ_Observations': [observation]})

        # Get target name and 2MASS ID from Gaia ID
        names = get_names_from_gaiaid(gaiaid)
        if names is None:
            log.warning(f"Query for {gaiaid} failed to return names")
            return
        OB.set('TargetName', f"{names['TargetName']}")
        OB.set('2MASSID', f"{names['2MASSID']}")
        # Using 2MASS ID query for Jmag
        twomass_params = get_Jmag(names['2MASSID'])
        OB.set('Jmag', f"{twomass_params['Jmag']}")
        # Using Gaia ID, query for Gaia parameters
        gaia_params = get_gaia_parameters(gaiaid)
        OB.set('Parallax', f"{gaia_params['Parallax']}")
        OB.set('RadialVelocity', f"{gaia_params['RadialVelocity']}")
        OB.set('Gmag', f"{gaia_params['Gmag']}")
        OB.set('Teff', f"{gaia_params['Teff']}")

        # Defaults
        OB.set('GuideMode', "auto")
        OB.set('TriggerCaHK', "True")
        OB.set('TriggerGreen', "True")
        OB.set('TriggerRed', "True")

        # Build Starlist line
        OB.star_list_line = form_starlist_line(names['TargetName'],
                                               gaia_params['RA_ICRS'],
                                               gaia_params['DE_ICRS'],
                                               vmag=gaia_params['Gmag'])
        print(OB)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('GaiaID', type=str,
                            help='Gaia DR3 ID to query for (e.g. "35227046884571776")')
        return super().add_cmdline_args(parser, cfg)
