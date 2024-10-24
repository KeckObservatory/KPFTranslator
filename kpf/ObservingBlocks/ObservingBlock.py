from pathlib import Path
import yaml

from astropy import units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord
from astroquery.vizier import Vizier
from astroquery.simbad import Simbad

from kpf.ObservingBlocks.Calibration import Calibration
from kpf.ObservingBlocks.Observation import Observation
from kpf.ObservingBlocks.Target import Target

from kpf import log, KPFException, InvalidObservingBlock


class ObservingBlock(object):
    def __init__(self, OBinput):
        if isinstance(OBinput, dict):
            OBdict = OBinput
        elif isinstance(OBinput, ObservingBlock):
            OBdict = OBinput.to_dict()
        elif OBinput in ['', None]:
            OBdict = {}
        elif isinstance(OBinput, str):
            file = Path(OBinput).expanduser().absolute()
            if file.exists() is True:
                try:
                    with open(file, 'r') as f:
                        OBdict = yaml.safe_load(f)
                except Exception as e:
                    log.error(f'Unable to parse input as yaml file')
                    log.error(f'{OBinput}')
                    OBdict = {}
            else:
                log.error(f'Unable to locate file: {OBinput}')
                OBdict = {}
        else:
            log.error(f'Unable to parse input as ObservingBlock')
            log.error(f'{OBinput}')
            OBdict = {}

        # Target
        target = OBdict.get('Target', None)
        if target is None:
            self.Target = None
        else:
            self.Target = Target(target)
        # Observations
        observations = OBdict.get('Observations', [])
        self.Observations = [Observation(obs) for obs in observations]
        # Calibrations
        calibrations = OBdict.get('Calibrations', [])
        self.Calibrations = [Calibration(cal) for cal in calibrations]

    def validate(self):
        # Check that components are the correct types and are individually valid
        if self.Target is not None:
            if not isinstance(self.Target, Target):
                raise InvalidObservingBlock('Target component is not a Target object')
            if not self.Target.validate():
                raise InvalidObservingBlock('Target component is not a valid Target object')
        for i,observation in enumerate(self.Observations):
            if not isinstance(observation, Observation):
                raise InvalidObservingBlock(f'Observation component {i+1} is not a Observation object')
            if not observation.validate():
                raise InvalidObservingBlock('Observation component {i+1} is not a valid Observation object')
        for i,calibration in enumerate(self.Calibrations):
            if not isinstance(calibration, Calibration):
                raise InvalidObservingBlock(f'Calibration component {i+1} is not a Calibration object')
            if not calibration.validate():
                raise InvalidObservingBlock('Calibration component {i+1} is not a valid Calibration object')

        # If we have science observations, we must have a target
        if len(self.Observations) > 0:
            if self.Target is None:
                raise InvalidObservingBlock(f"contains observations without a target")

        # We should have at least one observation or calibration
        if len(self.Observations) == 0 and len(self.Calibrations) == 0:
            raise InvalidObservingBlock(f"contains no observations and no calibrations")

    def to_dict(self):
        OB = {}
        if self.Target is not None:
            OB['Target'] = self.Target.to_dict()
        if len(self.Observations) > 0:
            OB['Observations'] = [o.to_dict() for o in self.Observations]
        if len(self.Calibrations) > 0:
            OB['Calibrations'] = [c.to_dict() for c in self.Calibrations]


    def __str__(self):
        out = f"{self.Target.get('TargetName'):18s} {self.Target.get('RA'):14s} {self.Target.get('Dec'):14s}"
        for obs in self.Observations:
            out += f"{obs.get('nExp'):d}x{obs.get('ExpTime'):.0f}s"
        return out


    @classmethod
    def get_gaia_parameters(self, gaiaid):
        r = Vizier(catalog='I/350/gaiaedr3').query_constraints(Source=gaiaid)[0]
        plx = f"{float(r['Plx']):.2f}" if r['Plx'].mask[0] == False else '0'
        rv = f"{float(r['RVDR2']):.2f}" if r['RVDR2'].mask[0] == False else '0'
        Gmag = f"{float(r['Gmag']):.2f}" if r['Gmag'].mask[0] == False else ''
        Teff = f"{float(r['Tefftemp']):.0f}" if r['Tefftemp'].mask[0] == False else '45000'

        gaia_params = {'Parallax': plx,
                       'RadialVelocity': rv,
                       'Gmag': Gmag,
                       'Teff': Teff,
                       }

        target_coord = SkyCoord(float(r['RA_ICRS']), float(r['DE_ICRS']),
                                pm_ra_cosdec=float(r['pmRA'])*u.mas/u.yr,
                                pm_dec=float(r['pmDE'])*u.mas/u.yr,
                                obstime=Time(2016.0, format='decimalyear'),
                                unit=(u.deg, u.deg),
                                )

        return target_coord, gaia_params

    @classmethod
    def get_Jmag(self, twomassid):
        result = Vizier(catalog='II/246/out').query_object(twomassid, radius=1*u.arcsec)
        


#         result = Vizier(catalog='II/246/out').query_object(twomassid)
#         if len(result) == 0:
#             return {'Jmag': ''}
#         table = result[0]
#         table.sort('_r')
#         if float(table['_r'][0]) > 1: # find better threshold
#             return {'Jmag': ''}
#         if table['Jmag'].mask[0] == True:
#             return {'Jmag': ''}
#         Jmag = f"{table['Jmag'][0]:.2f}"
#         return {'Jmag': Jmag}


    @classmethod
    def resolve_target_name(self, target_name):
        target_dict = {'TargetName': target_name}

        names = Simbad.query_objectids(target_name)
        GaiaDR3 = None
        for objid in names['ID']:
            if objid.find('Gaia DR3') >= 0:
                GaiaDR3 = objid[9:]
        target_dict['GaiaID'] = GaiaDR3
        target_coord, gaia_params = self.get_gaia_parameters(GaiaDR3) if GaiaDR3 is not None else None

        twoMASSID = None
        for objid in names['ID']:
            if objid.find('2MASS') >= 0:
                twoMASSID = objid[6:]
        target_dict['2MASSID'] = twoMASSID
        


#         at2000 = Time('2000', format='decimalyear')
#         target_coord_2000 = result.apply_space_motion(new_obstime=at2000)

        ra_dec_string = target_coord.to_string('hmsdms', sep=':', precision=2)
        target_dict['RA'] = ra_dec_string.split()[0]
        target_dict['Dec'] = ra_dec_string.split()[1]
        target_dict['Equinox'] = 2000
        target_dict['PMRA'] = target_coord.pm_ra_cosdec.to(u.arcsec/u.year).value*15
        target_dict['PMDEC'] = target_coord.pm_dec.to(u.arcsec/u.year).value
        target_dict['Epoch'] = target_coord.obstime.decimalyear

        target_dict.update(gaia_params)

        return target_dict




