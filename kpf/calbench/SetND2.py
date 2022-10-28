

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class SetND2(KPFTranslatorFunction):
    '''Set the filter in the ND2 filter wheel (the one at the output of the 
    octagon) via the `kpfcal.ND2POS` keyword.
    
    {OD 0.1} 2 {OD 0.3} 3 {OD 0.5} 4 {OD 0.8} 5 {OD 1.0} 6 {OD 4.0}
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        target = args.get('CalND2', None)
        if target is None:
            return False
        allowed_values = ["OD 0.1", "OD 0.3", "OD 0.5", "OD 0.8", "OD 1.0",
                          "OD 4.0"]
        return target in allowed_values

    @classmethod
    def perform(cls, args, logger, cfg):
        target = args.get('CalND2')
        kpfcal = ktl.cache('kpfcal')
        kpfcal['ND2POS'].write(target)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        target = args.get('CalND2')
        cfg = cls._load_config(cls, cfg)
        timeout = cfg.get('times', 'nd_move_time', fallback=20)
        expr = f"($kpfcal.ND2POS == {target})"
        success = ktl.waitFor(expr, timeout=timeout)
        return success
