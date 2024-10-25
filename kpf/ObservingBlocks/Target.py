import numpy as np
from astropy import units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, Angle
from astroquery.vizier import Vizier
from astroquery.simbad import Simbad


from kpf.ObservingBlocks import BaseOBComponent


target_properties = [{'name': 'TargetName', 'value': '', 'valuetype': str,
                      'comment': ''},
                     {'name': 'GaiaID', 'value': '', 'valuetype': str,
                      'comment': ''},
                     {'name': 'twoMASSID', 'value': '', 'valuetype': str,
                      'comment': ''},
                     {'name': 'Parallax', 'value': 0, 'valuetype': float,
                      'comment': '[arcsec]', 'precision': 3},
                     {'name': 'RadialVelocity', 'value': 0, 'valuetype': float,
                      'comment': '[km/s]', 'precision': 3},
                     {'name': 'Gmag', 'value': 0, 'valuetype': float,
                      'comment': '[magnitude]', 'precision': 2},
                     {'name': 'Jmag', 'value': 0, 'valuetype': float,
                      'comment': '[magnitude]', 'precision': 2},
                     {'name': 'Teff', 'value': 0, 'valuetype': float,
                      'comment': '[K]', 'precision': 0},
                     {'name': 'RA', 'value': '', 'valuetype': str,
                      'comment': '[hh:mm:ss.ss]'},
                     {'name': 'Dec', 'value': '', 'valuetype': str,
                      'comment': '[dd:mm:ss.ss]'},
                     {'name': 'Equinox', 'value': 2000, 'valuetype': float,
                      'comment': '[decimal year] Equinox of the coordinate system (typically 2000)',
                      'precision': 1},
                     {'name': 'PMRA', 'value': 0, 'valuetype': float,
                      'comment': '[seconds-of-time/year] Proper motion in RA',
                      'precision': 3},
                     {'name': 'PMDEC', 'value': 0, 'valuetype': float,
                      'comment': '[arcsec/year] Proper motion in Dec',
                      'precision': 3},
                     {'name': 'Epoch', 'value': 2000, 'valuetype': float,
                      'comment': '[decimal year] Epoch of the coordinate measurement',
                      'precision': 2},
                     {'name': 'DRA', 'value': 0, 'valuetype': float,
                      'comment': '[arcsec/hr divided by 15] Non sidereal tracking rate in RA',
                      'precision': 3},
                     {'name': 'DDEC', 'value': 0, 'valuetype': float,
                      'comment': '[arcsec/hr] Non sidereal tracking rate in Dec',
                      'precision': 3},
                    ]


# target_properties=[('TargetName', None, str, '', None),
#                    ('GaiaID', None, str, '', None),
#                    ('twoMASSID', None, str, '', None),
#                    ('Parallax', 0, float, '', 2),
#                    ('RadialVelocity', 0, float, '', 3),
#                    ('Gmag', None, float, '', 2),
#                    ('Jmag', None, float, '', 2),
#                    ('Teff', None, float, '', 0),
#                    ('RA', None, str, 'hh:mm:ss.ss', None),
#                    ('Dec', None, str, 'dd:mm:ss.s', None),
#                    ('Equinox', 2000, float, 'Equinox of coordinates', 0),
#                    ('PMRA', 0, float, 'Proper motion in RA in seconds-of-time/year', 3),
#                    ('PMDEC', 0, float, 'Proper motion in Dec in arcsec/year', 3),
#                    ('Epoch', 2000, float, 'Epoch of coordinates if proper motion is to be applied', 0),
#                    ('DRA', None, float, 'Non sidereal tracking rate in RA in arcsec/hr divided by 15 (positive implies moving east'),
#                    ('DDEC', None, float, 'Non sidereal tracking rate in Dec in arcsec/hr'),
#                     ]

class Target(BaseOBComponent):
    def __init__(self, input_dict):
        super().__init__('Target', '2.0', properties=target_properties)
        self.from_dict(input_dict)
        ra = Angle(self.RA.value, unit=u.hourangle)
        dec = Angle(self.Dec.value, unit=u.degree)
        pm_ra_cosdec = (self.PMRA.value*15*np.cos(dec.to(u.radian).value))*u.arcsec/u.yr
        self.coord = SkyCoord(ra, dec,
                              pm_ra_cosdec=pm_ra_cosdec,
                              pm_dec=self.PMDEC.value*u.arcsec/u.yr,
                              obstime=Time(self.Epoch.value, format='decimalyear'),
                              )

    def to_lines(self, comments=False):
        lines = []
        for ptuple in self.properties:
            pname = ptuple['name']
            if self.get(pname) is not None:
                p = getattr(self, pname)
                lines.append(f"  {pname}: {str(p)}")
        return lines

    def __str__(self):
        return f"{self.TargetName.value:16s} {self.RA.value:13s} {self.Dec.value:13s}"

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
        if len(result) == 0:
            return None
        if result[0]['Jmag'].mask[0] == True:
            return None
        return float(result[0]['Jmag'])

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
        Jmag = None
        for objid in names['ID']:
            if objid.find('2MASS') >= 0:
                twoMASSID = objid[6:]
                Jmag = self.get_Jmag(twoMASSID)
        target_dict['2MASSID'] = twoMASSID
        target_dict['Jmag'] = Jmag

        ra_dec_string = target_coord.to_string('hmsdms', sep=':', precision=2)
        target_dict['RA'] = ra_dec_string.split()[0]
        target_dict['Dec'] = ra_dec_string.split()[1]
        target_dict['Equinox'] = 2000
        target_dict['PMRA'] = target_coord.pm_ra_cosdec.to(u.arcsec/u.year).value*15
        target_dict['PMDEC'] = target_coord.pm_dec.to(u.arcsec/u.year).value
        target_dict['Epoch'] = target_coord.obstime.decimalyear

        target_dict.update(gaia_params)

        newtarg = Target(target_dict)

        return newtarg
