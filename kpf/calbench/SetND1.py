

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class SetND1(KPFTranslatorFunction):
    '''Set the filter in the ND1 filter wheel (the one at the output of the 
    octagon) via the `kpfcal.ND1POS` keyword.
    
    {OD 0.1} 2 {OD 1.0} 3 {OD 1.3} 4 {OD 2.0} 5 {OD 3.0} 6 {OD 4.0}
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        target = args.get('CalND1', None)
        if target is None:
            return False
        allowed_values = ["OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0", "OD 3.0",
                          "OD 4.0"]
        return target in allowed_values

    @classmethod
    def perform(cls, args, logger, cfg):
        target = args.get('CalND1')
        kpfcal = ktl.cache('kpfcal')
        kpfcal['ND1POS'].write(target)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        target = args.get('CalND1')
        cfg = cls._load_config(cls, cfg)
        timeout = cfg.get('times', 'nd_move_time', fallback=20)
        expr = f"($kpfcal.ND1POS == {target})"
        success = ktl.waitFor(expr, timeout=timeout)
        return success
