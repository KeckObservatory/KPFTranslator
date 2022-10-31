import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class SetSourceSelectShutters(KPFTranslatorFunction):
    '''Opens and closes the source select shutters via the 
    `kpfexpose.SRC_SHUTTERS` keyword.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        shutter_list = []
        if args.get('SSS_Science', False) is True:
            shutter_list.append('SciSelect')
        if args.get('SSS_Sky', False) is True:
            shutter_list.append('SkySelect')
        if args.get('SSS_SoCalSci', False) is True:
            shutter_list.append('SoCalSci')
        if args.get('SSS_SoCalCal', False) is True:
            shutter_list.append('SoCalCal')
        if args.get('SSS_CalSciSky', False) is True:
            shutter_list.append('Cal_SciSky')
        shutters_string = ','.join(shutter_list)
        print(f"  Setting source select shutters to '{shutters_string}'")
        kpfexpose = ktl.cache('kpfexpose')
        kpfexpose['SRC_SHUTTERS'].write(shutters_string)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        shutters = kpfexpose['SRC_SHUTTERS'].read()
        shutter_list = shutters.split(',')

        sci_shutter_status = 'SciSelect' in shutter_list
        sci_shutter_target = args.get('SSS_Science', False)
        if sci_shutter_target != sci_shutter_status:
            msg = (f"Final Science select shutter mismatch: "
                   f"{sci_shutter_status} != {sci_shutter_target}")
            print(msg)
            return False

        sky_shutter_status = 'SkySelect' in shutter_list
        sky_shutter_target = args.get('SSS_Sky', False)
        if sky_shutter_target != sky_shutter_status:
            msg = (f"Final Sky select shutter mismatch: "
                   f"{sky_shutter_status} != {sky_shutter_target}")
            print(msg)
            return False

        socalsci_shutter_status = 'SoCalSci' in shutter_list
        socalsci_shutter_target = args.get('SSS_SoCalSci', False)
        if socalsci_shutter_target != socalsci_shutter_status:
            msg = (f"Final SoCalSci select shutter mismatch: "
                   f"{socalsci_shutter_status} != {socalsci_shutter_target}")
            print(msg)
            return False

        socalcal_shutter_status = 'SoCalCal' in shutter_list
        socalcal_shutter_target = args.get('SSS_SoCalCal', False)
        if socalcal_shutter_target != socalcal_shutter_status:
            msg = (f"Final SoCalCal select shutter mismatch: "
                   f"{socalcal_shutter_status} != {socalcal_shutter_target}")
            print(msg)
            return False

        calscisky_shutter_status = 'Cal_SciSky' in shutter_list
        calscisky_shutter_target = args.get('SSS_CalSciSky', False)
        if calscisky_shutter_target != calscisky_shutter_status:
            msg = (f"Final Cal_SciSky select shutter mismatch: "
                   f"{calscisky_shutter_status} != {calscisky_shutter_target}")
            print(msg)
            return False

        print(f"    Done")
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg):
        parser = cls._add_bool_arg(parser, 'SciSelect',
                                   'Open the SciSelect shutter?',
                                   default=True)
        parser = cls._add_bool_arg(parser, 'SkySelect',
                                   'Open the SkySelect shutter?',
                                   default=True)
        parser = cls._add_bool_arg(parser, 'Cal_SciSky',
                                   'Open the Cal_SciSky shutter?',
                                   default=True)
        parser = cls._add_bool_arg(parser, 'SoCalSci',
                                   'Open the SoCalSci shutter?',
                                   default=False)
        parser = cls._add_bool_arg(parser, 'SoCalCal',
                                   'Open the SoCalCal shutter?',
                                   default=False)

        return super().add_cmdline_args(parser, cfg)
