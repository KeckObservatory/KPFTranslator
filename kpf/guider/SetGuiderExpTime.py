from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class SetGuiderExpTime(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        exptimekw = ktl.cache('kpfguide', 'EXPTIME')
        exptime = args.get('exptime', None)
        if exptime is not None:
            exptimekw.write(exptime)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        exptimekw = ktl.cache('kpfguide', 'EXPTIME')
        exptime = args.get('exptime', None)

        exptol = 0.01
        timeshim = 0.25
        if exptime is not None:
            exptime_check = exptimekw.read(binary=True)
            # First try sleeping briefly
            if abs(exptime_check - exptime) > exptol:
                sleep(timeshim)
            # Now check again
            exptime_check = exptimekw.read(binary=True)
            if abs(exptime_check - exptime) > exptol:
                print(f"Failed to set exposure time.")
                print(f"Requested {exptime:.3f} s, found {exptime_check:.3f} s")
                return False

        return True
