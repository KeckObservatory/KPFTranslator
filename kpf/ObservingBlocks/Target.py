from kpf.ObservingBlocks import BaseOBComponent

target_properties=[('TargetName', None, str),
                   ('GaiaID', None, str),
                   ('twoMASSID', None, str),
                   ('Parallax', 0, float),
                   ('RadialVelocity', 0, float),
                   ('Gmag', None, float),
                   ('Jmag', None, float),
                   ('Teff', None, float),
                   ('RA', None, str, 'hh:mm:ss.ss'),
                   ('Dec', None, str, 'dd:mm:ss.s'),
                   ('Equinox', 2000, float, 'Equinox of coordinates'),
                   ('PMRA', 0, float, 'Proper motion in RA in seconds-of-time/year'),
                   ('PMDEC', 0, float, 'Proper motion in Dec in arcsec/year'),
                   ('Epoch', 2000, float, 'Epoch of coordinates if proper motion is to be applied'),
                   ('DRA', None, float, 'Non sidereal tracking rate in RA in arcsec/hr divided by 15 (positive implies moving east'),
                   ('DDEC', None, float, 'Non sidereal tracking rate in Dec in arcsec/hr'),
                    ]

class Target(BaseOBComponent):
    def __init__(self, input_dict):
        super().__init__('Target', '2.0', properties=target_properties)
        self.from_dict(input_dict)
