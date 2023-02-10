import re
import numpy as np
from astroquery.vizier import Vizier
from astroquery.simbad import Simbad

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


##-------------------------------------------------------------------------
## CalculateDAR
##-------------------------------------------------------------------------
class BuildOBfromQuery(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        gaiaid = args.get('GaiaID')

        # Using Gaia ID, query for 2MASS ID
        twomassid = None
        names = Simbad.query_objectids(f"Gaia DR3 {gaiaid}")
        for name in names:
            is2mass = re.match('^2MASS (J[\d\+\-]+)', name[0])
            if is2mass is not None:
                twomassid = is2mass.group(1)

        # Using 2MASS ID query for Jmag
        cat = 'II/246/out'
        cols = ['2MASS', 'Jmag']
        r = Vizier(catalog=cat, columns=cols).query_constraints(Source=gaiaid)[0]
        Jmag_masked = r['Jmag'].mask[0]
        Jmag = r['Jmag'][0] if Jmag_masked == False else None
        
        
        # Using Gaia ID, query for Gaia parameters
        cat = 'I/350/gaiaedr3'
#         cols = ['RA_ICRS', 'DE_ICRS', 'Source', 'Plx',
#                 'PM', 'pmRA', 'e_pmRA', 'pmDE', 'e_pmDE',
#                 'Gmag', 'e_Gmag', 'RVDR2', 'e_RVDR2',
#                 'Tefftemp', 'loggtemp',
#                 'GmagCorr', 'e_GmagCorr']
        cols = ['Source', 'Plx', 'Gmag', 'RVDR2', 'Tefftemp']
        r = Vizier(catalog=cat, columns=cols).query_constraints(Source=gaiaid)[0]




        OBvalues = [('Source', 'GaiaID', int),
                    ('2massid', '2MASSID', str),
                    ('Plx', 'Parallax', float),
                    ('RVDR2', 'RadialVelocity', float),
                    ('Gmag', 'Gmag', float),
                    ('Jmag', 'Jmag', float),
                    ('Tefftemp', 'Teff', float),
                    ]

        print("Template_Name: kpf_sci")
        print("Template_Version: 0.6")
        print()
        print("# Target Info")
        for OBvalue in OBvalues:
            OBname = OBvalue[1]
            if OBvalue[0] == '2massid':
                if twomassid is not None:
                    print(f"{OBname}: {twomassid}")
                else:
                    print(f"{OBname}: ?")
            elif OBvalue[0] == 'Jmag':
                if Jmag is not None:
                    print(f"{OBname}: {Jmag}")
                else:
                    print(f"{OBname}: ?")
            elif OBvalue[0] in cols:
                masked = r[OBvalue[0]].mask[0]
                if masked == False:
                    val = OBvalue[2](r[OBvalue[0]])
                    print(f"{OBname}: {val}")
                else:
                    print(f"{OBname}: ?")
            else:
                print(f"{OBname}: ?")

        print("# Guider Setup")
        print("GuiderMode: auto")

        print("# Spectrograph Setup")
        print("TriggerCaHK: True")
        print("TriggerGreen: True")
        print("TriggerRed: True")

        print("# Observations")
        print("SEQ_Observations:")
        print(" - Object: ?")
        print("   nExp: ?")
        print("   Exptime: ?")
        print("   TakeSimulCal: ?")
        print("   ExpMeterMode: ?")
        print("   ExpMeterExpTime: ?")
        print("   CalND1: ?")
        print("   CalND2: ?")



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
