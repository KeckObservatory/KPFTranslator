from pathlib import Path
import yaml
import numpy as np
from astropy import units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, Angle, ICRS, FK5
from astroquery.vizier import Vizier
from astroquery.simbad import Simbad


from kpf.ObservingBlocks import BaseOBComponent


def parse_time_input(input_value):
    # Handle Epoch formats
    if input_value[0] == 'J':
        timeformat = 'jyear_str'
    elif input_value[0] == 'B':
        timeformat = 'byear_str'
    else:
        timeformat = 'decimalyear'
    return Time(input_value, format=timeformat)


class Target(BaseOBComponent):
    def __init__(self, input_dict):
        properties_file = Path(__file__).parent / 'TargetProperties.yaml'
        with open(properties_file, 'r') as f:
            properties = yaml.safe_load(f.read())
        super().__init__('Target', '2.0', properties=properties)
        self.from_dict(input_dict)
        self.coord = None
        self.build_SkyCoord()


    def get_pruning_guide(self):
        return [(abs(self.get('DRA')) < 0.001 and abs(self.get('DDEC')) < 0.001, ['DRA', 'DDEC']),
                ]


    def build_SkyCoord(self):
        # Build astropy.coordinates.SkyCoord
        try:
            ra = Angle(self.RA.value, unit=u.hourangle)
            dec = Angle(self.Dec.value, unit=u.degree)
            pm_ra_cosdec = (self.PMRA.value*15*np.cos(dec.to(u.radian).value))*u.arcsec/u.yr
            equinox = parse_time_input(self.Equinox.value)
            epoch = parse_time_input(self.Epoch.value)
            self.coord = SkyCoord(ra, dec, frame=FK5(equinox=equinox),
                                  pm_ra_cosdec=pm_ra_cosdec,
                                  pm_dec=self.PMDEC.value*u.arcsec/u.yr,
                                  obstime=epoch,
                                  )
        except Exception as e:
            print(e)
            self.coord = None


    def check_property(self, pname):
        if pname in ['RA', 'Dec']:
            if self.coord is None:
                return True, ' # ERROR: Invalid SkyCoord'
        elif pname == 'TargetName':
            if self.get(pname) in ['', None]:
                return True, ' # ERROR: TargetName is empty'
        elif pname == 'GaiaID':
            if self.get(pname) in ['', None]:
                return False, ' # GaiaID is empty'
        elif pname == 'twoMASSID':
            if self.get(pname) in ['', None]:
                return False, ' # 2MASSID is empty'
        elif pname == 'Teff':
            if self.get('Teff') < 2600 or self.get('Teff') > 45000:
                return True, ' # ERROR: Teff invalid'
            elif self.get('Teff') < 2700 or self.get('Teff') > 6600:
                return False, ' # AutoNDFilters needs 2700-6600'
        return False, ''


    def add_comment(self, pname):
        error, comment = self.check_property(pname)
        return comment


    def validate(self):
        '''
        '''
        valid = True
        for p in self.properties:
            error, comment = self.check_property(p['name'])
            if error == True:
                print(f"{p['name']} is INVALID: {comment}")
                valid = False
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


    def to_star_list(self):
        '''Return a string which is a Keck formatted star list line
        '''
        try:
            pmcoord = self.coord.apply_space_motion(new_obstime=Time.now())
            rastr = pmcoord.ra.to_string(unit=u.hourangle, sep=' ', precision=raprecision)
            decstr = pmcoord.dec.to_string(unit=u.deg, sep=' ', precision=decprecision, alwayssign=True)
        except:
            rastr = str(self.RA).replace(':', ' ')
            decstr = str(self.Dec).replace(':', ' ')
        out = f"{self.TargetName.value:15s} {rastr} {decstr}"
        if str(self.Equinox) == 'J2000':
            out += f" 2000"
        else:
            out += f" {self.Equinox}"
        if abs(self.DRA.value) > 0 or abs(self.DDEC.value) > 0:
               out += f" dra={self.DRA:.3f} ddec={self.DDEC:.3f}"
#         out += f" # Gmag={str(self.Gmag)} Jmag={str(self.Jmag)}"
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
        gaia_params = {}
        if names is None:
            print(f'Simbad query returned no objects for "{target_name}"')
            return Target({})
        else:
            for objid in names['ID']:
                if objid.find('Gaia DR3') >= 0:
                    GaiaDR3 = objid[9:]
        if GaiaDR3 is not None:
            print(f'Querying Gaia catalog for DR3 ID {GaiaDR3}')
            target_dict['GaiaID'] = f"DR3 {GaiaDR3}"
            target_coord, gaia_params = self.get_gaia_parameters(GaiaDR3)
        else:
            try:
                simbad_results = Simbad.query_object(target_name)
                target_coord = SkyCoord(f"{simbad_results['RA'][0]} {simbad_results['DEC'][0]}",
                                        unit=(u.hourangle, u.deg)
                                        )
                print(target_coord)
            except Exception as e:
                print('Simbad query failed')
                print(e)
                return Target({})

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
