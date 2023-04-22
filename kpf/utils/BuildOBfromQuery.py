import re
from astropy.coordinates import SkyCoord
from astroquery.vizier import Vizier
from astroquery.simbad import Simbad

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


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
    return {'TargetName': hdnumber, '2MASSID': twomassid,
            'all': [x[0] for x in names]}


def get_Jmag(twomassid):
    cat = 'II/246/out'
    cols = ['2MASS', 'Jmag', 'RAJ2000', 'DEJ2000', '_r']
    result = Vizier(catalog=cat, columns=cols).query_object(twomassid)
    if len(result) == 0:
        return {'Jmag': '?'}
    table = result[0]
    table.sort('_r')
    if float(table['_r'][0]) > 1: # find better threshold
        return {'Jmag': '?'}
    if table['Jmag'].mask[0] == True:
        return {'Jmag': '?'}
    Jmag = f"{table['Jmag'][0]:.2f}"
    return {'Jmag': Jmag}


def get_gaia_parameters(gaiaid):
    cat = 'I/350/gaiaedr3'
    cols = ['RA_ICRS', 'DE_ICRS', 'Source', 'Plx', 'Gmag', 'RVDR2', 'Tefftemp']
    r = Vizier(catalog=cat, columns=cols).query_constraints(Source=gaiaid)[0]
    plx = f"{float(r['Plx']):.2f}" if r['Plx'].mask[0] == False else '0'
    rv = f"{float(r['RVDR2']):.2f}" if r['RVDR2'].mask[0] == False else '0'
    Gmag = f"{float(r['Gmag']):.2f}" if r['Gmag'].mask[0] == False else '?'
    Teff = f"{float(r['Tefftemp']):.0f}" if r['Tefftemp'].mask[0] == False else '45000'
    gaia_params = {'Parallax': plx,
                   'RadialVelocity': rv,
                   'Gmag': Gmag,
                   'Teff': Teff,
                   'RA_ICRS': float(r['RA_ICRS']),
                   'DE_ICRS': float(r['DE_ICRS']),
                   }
    return gaia_params


def OBdict_to_lines(OB):
    obs = OB.get('SEQ_Observations')[0]
    lines = [f"# Built using KPF OB GUI tool",
             f"Template_Name: kpf_sci",
             f"Template_Version: 0.6",
             f"",
             f"# Target Info",
             f"TargetName: {OB.get('TargetName', '?')}",
             f"GaiaID: {OB.get('GaiaID', '?')}",
             f"2MASSID: {OB.get('2MASSID', '?')}",
             f"Parallax: {OB.get('Parallax', '?')}",
             f"RadialVelocity: {OB.get('RadialVelocity', '?')}",
             f"Gmag: {OB.get('Gmag', '?')}",
             f"Jmag: {OB.get('Jmag', '?')}",
             f"Teff: {OB.get('Teff', '?')}",
             f"",
             f"# Guider Setup",
             f"GuideMode: {OB.get('GuideMode', '?')}"]
    if OB.get('GuideMode', None) != 'auto':
        lines.extend([
          f"GuideCamGain: {OB.get('GuideCamGain', '?')}",
          f"GuideFPS: {OB.get('GuideFPS', '?')}",
          ])
    lines.extend([
          f"",
          f"# Spectrograph Setup",
          f"TriggerCaHK: {OB.get('TriggerCaHK', '?')}",
          f"TriggerGreen: {OB.get('TriggerGreen', '?')}",
          f"TriggerRed: {OB.get('TriggerRed', '?')}",
          f"",
          f"# Observations (repeat the indented block below to take multiple observations,",
          f"SEQ_Observations:",
          f" - Object: {obs.get('Object', '?')}",
          f"   nExp: {obs.get('nExp', '?')}",
          f"   ExpTime: {obs.get('ExpTime', '?')}",
          f"   ExpMeterMode: {obs.get('ExpMeterMode', '?')}",
          f"   AutoExpMeter: {obs.get('AutoExpMeter', '?')}",
          ])
    if obs.get('AutoExpMeter', False) not in [True, 'True']:
        lines.extend([
          f"   ExpMeterExpTime: {obs.get('ExpMeterExpTime', '?')}",
          ])
    lines.extend([
          f"   TakeSimulCal: {obs.get('TakeSimulCal', '?')}",
          ])
    if obs.get('TakeSimulCal', None) in [True, 'True']:
        if obs.get('AutoNDFilters', None) is not None:
            lines.extend([
              f"   AutoNDFilters: {obs.get('AutoNDFilters', '?')}",
              ])
        if obs.get('AutoNDFilters', None) not in [True, 'True']:
            lines.extend([
              f"   CalND1: {obs.get('CalND1', '?')}",
              f"   CalND2: {obs.get('CalND2', '?')}",
              ])

    if OB.get('starlist_entry', None) is not None:
        lines.extend(['', '# Starlist entry:', f"#{OB['starlist_entry']}"])
    return lines


def form_starlist_line(name, ra, dec, vmag=None, frame='icrs', unit='deg'):
    coord = SkyCoord(float(ra), float(dec), frame=frame, unit=unit)
    coord_string = coord.to_string('hmsdms', sep=' ', precision=2)
    line = f"{name:15s} {coord_string} 2000.0"
    if vmag is not None:
        line += f" vmag={float(vmag):.2f}"
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
        OB = {'SEQ_Observations': [{}]}

        gaiaid = args.get('GaiaID')
        OB['GaiaID'] = f"DR3 {gaiaid}"
        # Get target name and 2MASS ID from Gaia ID
        names = get_names_from_gaiaid(gaiaid)
        OB['TargetName'] = f"{names['TargetName']}"
        OB['2MASSID'] = f"{names['2MASSID']}"
        # Using 2MASS ID query for Jmag
        twomass_params = get_Jmag(names['2MASSID'])
        OB['Jmag'] = f"{twomass_params['Jmag']}"
        # Using Gaia ID, query for Gaia parameters
        gaia_params = get_gaia_parameters(gaiaid)
        OB['Parallax'] = f"{gaia_params['Parallax']}"
        OB['RadialVelocity'] = f"{gaia_params['RadialVelocity']}"
        OB['Gmag'] = f"{gaia_params['Gmag']}"
        OB['Teff'] = f"{gaia_params['Teff']}"

        # Defaults
        OB['GuideMode'] = "auto"
        OB['TriggerCaHK'] = "True"
        OB['TriggerGreen'] = "True"
        OB['TriggerRed'] = "True"
        OB['SEQ_Observations'][0]['ExpMeterMode'] = "monitor"
        OB['SEQ_Observations'][0]['AutoExpMeter'] = "False"
        OB['SEQ_Observations'][0]['TakeSimulCal'] = "True"

        # Build Starlist line
        OB['starlist_entry'] = form_starlist_line(names['TargetName'],
                                                  gaia_params['RA_ICRS'],
                                                  gaia_params['DE_ICRS'],
                                                  vmag=gaia_params['Gmag'])

        for line in OBdict_to_lines(OB):
            print(line)

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
