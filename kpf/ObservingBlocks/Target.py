from pathlib import Path
import yaml
import numpy as np
from astropy import units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, Angle, ICRS, FK5
from astroquery.vizier import Vizier
from astroquery.simbad import Simbad


from kpf.ObservingBlocks import BaseOBComponent


class Target(BaseOBComponent):
    def __init__(self, input_dict):
        properties_file = Path(__file__).parent / 'TargetProperties.yaml'
        with open(properties_file, 'r') as f:
            properties = yaml.safe_load(f.read())
        super().__init__('Target', '2.0', properties=properties)
        self.from_dict(input_dict)
        self.coord = None
        self.pruning_guide = [(abs(self.get('DRA')) < 0.001 and abs(self.get('DDEC')) < 0.001, ['DRA', 'DDEC']),
                             ]
        self.build_SkyCoord()


    def build_SkyCoord(self):
        # Build astropy.coordinates.SkyCoord
        try:
            ra = Angle(self.RA.value, unit=u.hourangle)
            dec = Angle(self.Dec.value, unit=u.degree)
            pm_ra_cosdec = (self.PMRA.value*15*np.cos(dec.to(u.radian).value))*u.arcsec/u.yr
            self.coord = SkyCoord(ra, dec, frame=FK5(equinox=self.Equinox.value),
                                  pm_ra_cosdec=pm_ra_cosdec,
                                  pm_dec=self.PMDEC.value*u.arcsec/u.yr,
                                  obstime=Time(self.Epoch.value, format='decimalyear'),
                                  )
        except:
            self.coord = None


    def add_comment(self, pname):
        # Unable to form SkyCoord
        if self.coord is None:
            if pname in ['RA', 'Dec']:
                return ' # ERROR: Invalid SkyCoord'
        # TargetName is empty
        if self.get('TargetName') in [None, '']:
            if pname == 'TargetName':
                return ' # ERROR: TargetName is empty'
        # GaiaID is empty
        if self.get('GaiaID') in [None, '']:
            if pname == 'GaiaID':
                return ' # GaiaID is empty'
        # twoMASSID is empty
        if self.get('twoMASSID') in [None, '']:
            if pname == 'twoMASSID':
                return ' # twoMASSID is empty'
        # Teff out of range
        if self.get('Teff') < 2600 or self.get('Teff') > 45000:
            if pname == 'Teff':
                return ' # Teff range 2600-45000'
        # Teff out of range for Simulcal prediction 2700 - 6600
        elif self.get('Teff') < 2700 or self.get('Teff') > 6600:
            if pname == 'Teff':
                return ' # AutoNDFilters needs 2700-6600'
        return ''


    def validate(self):
        '''Validation checks:
        
        - TargetName is not empty
        - RA, Dec, and equinox can form an astropy `SkyCoord`
        
        Warnings (intended for RV targets):
        - GaiaID is empty
        - Teff: 2700 - 6600 Kelvin
        '''
        valid = True
        for p in self.properties:
            if self.get(p['name']) is None:
                print(f"ERROR: {p['name']} is undefined, default is {p['defaultvalue']}")
                valid = False
        # Check that we can build a SkyCoord
        self.build_SkyCoord()
        if self.coord is None:
            print(f'ERROR: Could not form a SkyCoord from target coordinates')
            valid = False
        # Check if TargetName is empty string
        if self.TargetName.value == '':
            print(f'ERROR: TargetName is empty')
            valid = False
        # Handle Warnings
        if self.GaiaID.value == '':
            print(f'WARNING: GaiaID is empty. This will impact PRV calculations.')
        if self.Teff.value <= 2700 or self.Teff.value >= 6600:
            print(f'WARNING: Teff is out of range. This will impact simulcal estimates.')
        return valid


    def __str__(self, raprecision=1, decprecision=0, magprecision=1):
        '''Show a one line representation similar to a Keck star list line.
        '''
        try:
            rastr = self.coord.ra.to_string(unit=u.hourangle, sep=':', precision=raprecision)
            decstr = self.coord.dec.to_string(unit=u.deg, sep=':', precision=decprecision, alwayssign=True)
#             radec_str = self.coord.to_string('hmsdms', sep=':', precision=1)
        except:
            rastr = str(self.RA)
            decstr = str(self.Dec)
        out = (f"{self.TargetName.value:16s} {rastr:>10s} {decstr:>9s} "
               f"{str(self.Gmag):>4s} {str(self.Jmag):>4s}")
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

        try:
            target_coord = SkyCoord(float(r['RA_ICRS']), float(r['DE_ICRS']),
                                    pm_ra_cosdec=float(r['pmRA'])*u.mas/u.yr,
                                    pm_dec=float(r['pmDE'])*u.mas/u.yr,
                                    obstime=Time(2016.0, format='decimalyear'),
                                    unit=(u.deg, u.deg),
                                    )
        except:
            target_coord = None
        return target_coord, gaia_params


    @classmethod
    def get_Jmag(self, twomassid):
        result = Vizier(catalog='II/246/out').query_object(twomassid, radius=1*u.arcsec)
        if len(result) == 0:
            return None
        if result[0]['Jmag'].mask[0] == True:
            return None
        return float(result[0]['Jmag'])


    @classmethod
    def resolve_name(self, target_name):
        target_dict = {'TargetName': target_name}

        names = Simbad.query_objectids(target_name)
        GaiaDR3 = None
        for objid in names['ID']:
            if objid.find('Gaia DR3') >= 0:
                GaiaDR3 = objid[9:]
        target_dict['GaiaID'] = f"DR3 {GaiaDR3}"
        target_coord, gaia_params = self.get_gaia_parameters(GaiaDR3) if GaiaDR3 is not None else None

        twoMASSID = None
        Jmag = None
        for objid in names['ID']:
            if objid.find('2MASS') >= 0:
                twoMASSID = objid[6:]
                Jmag = self.get_Jmag(twoMASSID)
        target_dict['2MASSID'] = twoMASSID
        target_dict['Jmag'] = Jmag

        try:
            ra_dec_string = target_coord.to_string('hmsdms', sep=':', precision=2)
            target_dict['RA'] = ra_dec_string.split()[0]
            target_dict['Dec'] = ra_dec_string.split()[1]
            target_dict['Equinox'] = 'J2000'
            target_dict['PMRA'] = target_coord.pm_ra_cosdec.to(u.arcsec/u.year).value*15
            target_dict['PMDEC'] = target_coord.pm_dec.to(u.arcsec/u.year).value
            target_dict['Epoch'] = target_coord.obstime.decimalyear
        except:
            pass

        target_dict.update(gaia_params)
        newtarg = Target(target_dict)

        return newtarg
