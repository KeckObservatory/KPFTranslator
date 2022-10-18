from collections import OrderedDict
import os
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class SetOutdirs(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        utnow = datetime.utcnow()
        date = utnow-timedelta(days=1)
        date_str = date.strftime('%Y%b%d').lower()
        outdir = Path(f"/s/sdata1701/{os.getlogin()}/{date_str}")

        if args.get('CRED2', True) is True:
            print(f"Setting guider OUTDIR to {outdir / 'CRED2'}")
            guide_outdir = ktl.cache('kpfguide', 'OUTDIR')
            try:
                guide_outdir.write(f"{outdir / 'CRED2'}")
            except Exception as e:
                print(f"ERROR setting guider outdir")
                print(e)

        kpffvc = ktl.cache('kpffvc')
        if args.get('FVC1', True) is True:
            print(f"Setting FVC1 OUTDIR to {outdir / 'FVC1'}")
            try:
                kpffvc['SCIOUTDIR'].write(f"{outdir / 'FVC1'}")
            except Exception as e:
                print(f"ERROR setting SCI FVC outdir")
                print(e)

        if args.get('FVC2', True) is True:
            print(f"Setting FVC2 OUTDIR to {outdir / 'FVC2'}")
            try:
                kpffvc['CAHKOUTDIR'].write(f"{outdir / 'FVC2'}")
            except Exception as e:
                print(f"ERROR setting CAHK FVC outdir")
                print(e)

        if args.get('FVC3', True) is True:
            print(f"Setting FVC3 OUTDIR to {outdir / 'FVC3'}")
            try:
                kpffvc['CALOUTDIR'].write(f"{outdir / 'FVC3'}")
            except Exception as e:
                print(f"ERROR setting CAL FVC outdir")
                print(e)

        if args.get('FVC4', False) is True:
            print(f"Setting FVC4 OUTDIR to {outdir / 'FVC4'}")
            try:
                kpffvc['EXTOUTDIR'].write(f"{outdir / 'FVC4'}")
            except Exception as e:
                print(f"ERROR setting EXT FVC outdir")
                print(e)

        if args.get('ExpMeter', True) is True:
            expmeter_outdir = outdir / 'ExpMeter'
            print(f"Setting exposure meter DATADIR to {expmeter_outdir}")
            kpf_expmeter = ktl.cache('kpf_expmeter')
            try:
                kpf_expmeter['DATADIR'].write(f"{expmeter_outdir}")
            except Exception as e:
                print(f"ERROR setting ExpMeter outdir")
                print(e)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        utnow = datetime.utcnow()
        date = utnow-timedelta(days=1)
        date_str = date.strftime('%Y%b%d').lower()
        outdir = Path(f"/s/sdata1701/{os.getlogin()}/{date_str}")
        tests = []
        if args.get('CRED2', True) is True:
            expr = f"$kpfguide.OUTDIR == '{outdir}/CRED2'"
            success = ktl.waitFor(expr, timeout=5)
            tests.append(success)
        if args.get('FVC1', True) is True:
            expr = f"$kpffvc.SCIOUTDIR == '{outdir}/FVC1'"
            success = ktl.waitFor(expr, timeout=5)
            tests.append(success)
        if args.get('FVC2', True) is True:
            expr = f"$kpffvc.CAHKOUTDIR == '{outdir}/FVC2'"
            success = ktl.waitFor(expr, timeout=5)
            tests.append(success)
        if args.get('FVC3', True) is True:
            expr = f"$kpffvc.CALOUTDIR == '{outdir}/FVC3'"
            success = ktl.waitFor(expr, timeout=5)
            tests.append(success)
        if args.get('FVC4', False) is True:
            expr = f"$kpffvc.EXTOUTDIR == '{outdir}/FVC4'"
            success = ktl.waitFor(expr, timeout=5)
            tests.append(success)
        if args.get('ExpMeter', True) is True:
            expr = f"$kpf_expmeter.DATADIR == '{outdir}/ExpMeter'"
            success = ktl.waitFor(expr, timeout=5)
            tests.append(success)

        return np.all(np.array(tests))

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        """
        The arguments to add to the command line interface.
        """
        parser = cls._add_bool_arg(parser, 'CRED2',
            'Set CRED2 OUTDIR (kpfguide.OUTDIR)?', default=True)
        parser = cls._add_bool_arg(parser, 'FVC1',
            'Set FVC1 OUTDIR (kpffvc.SCIOUTDIR)?', default=True)
        parser = cls._add_bool_arg(parser, 'FVC2',
            'Set FVC2 OUTDIR (kpffvc.CAHKOUTDIR)?', default=True)
        parser = cls._add_bool_arg(parser, 'FVC3',
            'Set FVC3 OUTDIR (kpffvc.CALOUTDIR)?', default=True)
        parser = cls._add_bool_arg(parser, 'FVC4',
            'Set FVC4 OUTDIR (kpffvc.EXTOUTDIR)?', default=False)
        parser = cls._add_bool_arg(parser, 'ExpMeter',
            'Set ExpMeter OUTDIR (kpf_expmeter.DATADIR)?', default=True)

        return super().add_cmdline_args(parser, cfg)
