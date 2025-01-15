from pathlib import Path
import yaml
import numpy as np
from astropy import units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, Angle
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
        self.name_overrides={'2MASSID': 'twoMASSID'}
        # Build astropy.coordinates.SkyCoord
        try:
            ra = Angle(self.RA.value, unit=u.hourangle)
            dec = Angle(self.Dec.value, unit=u.degree)
            pm_ra_cosdec = (self.PMRA.value*15*np.cos(dec.to(u.radian).value))*u.arcsec/u.yr
            self.coord = SkyCoord(ra, dec,
                                  pm_ra_cosdec=pm_ra_cosdec,
                                  pm_dec=self.PMDEC.value*u.arcsec/u.yr,
                                  obstime=Time(self.Epoch.value, format='decimalyear'),
                                  )
        except:
            self.coord = None

    def to_lines(self, comments=False):
        lines = []
        for ptuple in self.properties:
            pname = ptuple['name']
            if self.get(pname) is not None:
                p = getattr(self, pname)
                lines.append(f"  {pname}: {str(p)}")
        return lines

    def __str__(self):
        try:
            radec_str = self.coord.to_string('hmsdms', sep=':', precision=1)
        except:
            radec_str = f"{str(self.RA)} {str(self.Dec)}"
        out = (f"{self.TargetName.value:16s} {radec_str} "
               f"{str(self.Gmag):>5s} {str(self.Jmag):>5s}")
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

        try:
            ra_dec_string = target_coord.to_string('hmsdms', sep=':', precision=2)
            target_dict['RA'] = ra_dec_string.split()[0]
            target_dict['Dec'] = ra_dec_string.split()[1]
            target_dict['Equinox'] = 2000
            target_dict['PMRA'] = target_coord.pm_ra_cosdec.to(u.arcsec/u.year).value*15
            target_dict['PMDEC'] = target_coord.pm_dec.to(u.arcsec/u.year).value
            target_dict['Epoch'] = target_coord.obstime.decimalyear
        except:
            pass

        target_dict.update(gaia_params)
        newtarg = Target(target_dict)

        return newtarg
