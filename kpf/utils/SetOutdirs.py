import os
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetOutdirs(KPFFunction):
    '''Set output directories for all detectors based on the current date.
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        log.info(f"SetOutdirs invoked")
        utnow = datetime.utcnow()
        date = utnow-timedelta(days=1)
        date_str = date.strftime('%Y%b%d').lower()
        outdir = Path(f"/s/sdata1701/{os.getlogin()}/{date_str}")
        magiq_outdir = Path(f"/s/sdata1701/kpfguide/{date_str}")
        log.debug(f"base outdir: {outdir}")
        log.debug(f"magiq outdir: {magiq_outdir}")

        if args.get('CRED2', True) is True:
            log.info(f"  Guider OUTDIR = {magiq_outdir}")
            guide_outdir = ktl.cache('kpfguide', 'OUTDIR')
            try:
                guide_outdir.write(f"{magiq_outdir}")
            except Exception as e:
                log.error(f"ERROR setting guider outdir")
                log.error(e)

            log.info(f"  Guider TRIGOUTDIR = {outdir / 'CRED2'}")
            trig_outdir = ktl.cache('kpfguide', 'TRIGOUTDIR')
            try:
                trig_outdir.write(f"{outdir / 'CRED2'}")
            except Exception as e:
                log.error(f"ERROR setting guider TRIGOUTDIR")
                log.error(e)

        kpffvc = ktl.cache('kpffvc')
        if args.get('FVC1', False) is True:
            log.info(f"  FVC1 OUTDIR = {outdir / 'FVC1'}")
            try:
                kpffvc['SCIOUTDIR'].write(f"{outdir / 'FVC1'}")
            except Exception as e:
                log.error(f"ERROR setting SCI FVC outdir")
                log.error(e)

        if args.get('FVC2', False) is True:
            log.info(f"  FVC2 OUTDIR = {outdir / 'FVC2'}")
            try:
                kpffvc['CAHKOUTDIR'].write(f"{outdir / 'FVC2'}")
            except Exception as e:
                log.error(f"ERROR setting CAHK FVC outdir")
                log.error(e)

        if args.get('FVC3', False) is True:
            log.info(f"  FVC3 OUTDIR = {outdir / 'FVC3'}")
            try:
                kpffvc['CALOUTDIR'].write(f"{outdir / 'FVC3'}")
            except Exception as e:
                log.error(f"ERROR setting CAL FVC outdir")
                log.error(e)

        if args.get('FVC4', False) is True:
            log.info(f"  FVC4 OUTDIR = {outdir / 'FVC4'}")
            try:
                kpffvc['EXTOUTDIR'].write(f"{outdir / 'FVC4'}")
            except Exception as e:
                log.error(f"ERROR setting EXT FVC outdir")
                log.error(e)

        if args.get('ExpMeter', True) is True:
            expmeter_outdir = outdir / 'ExpMeter'
            log.info(f"  ExpMeter DATADIR = {expmeter_outdir}")
            kpf_expmeter_outdir = ktl.cache('kpf_expmeter', 'DATADIR')
            try:
                kpf_expmeter_outdir.write(f"{expmeter_outdir}")
            except Exception as e:
                log.error(f"ERROR setting ExpMeter outdir")
                log.error(e)

        if args.get('CaHK', True) is True:
            cahk_outdir = outdir / 'CaHK'
            log.info(f"  CaHK RECORDDIR = {cahk_outdir}")
            kpf_hk_outdir = ktl.cache('kpf_hk', 'RECORDDIR')
            try:
                kpf_hk_outdir.write(f"{cahk_outdir}")
            except Exception as e:
                log.error(f"ERROR setting CaHK outdir")
                log.error(e)

        if args.get('Green', True) is True:
            green_outdir = outdir / 'Green'
            log.info(f"  Green FITSDIR = {green_outdir}")
            kpfgreen_outdir = ktl.cache('kpfgreen', 'FITSDIR')
            try:
                kpfgreen_outdir.write(f"{green_outdir}")
            except Exception as e:
                log.error(f"ERROR setting Green outdir")
                log.error(e)

        if args.get('Red', True) is True:
            red_outdir = outdir / 'Red'
            log.info(f"  Red FITSDIR = {red_outdir}")
            kpfred_outdir = ktl.cache('kpfred', 'FITSDIR')
            try:
                kpfred_outdir.write(f"{red_outdir}")
            except Exception as e:
                log.error(f"ERROR setting Red outdir")
                log.error(e)

        if args.get('L0', True) is True:
            L0_outdir = outdir / 'L0'
            log.info(f"  kpfasemble OUTDIR = {L0_outdir}")
            kpfassemble_outdir = ktl.cache('kpfassemble', 'OUTDIR')
            try:
                kpfassemble_outdir.write(f"{L0_outdir}")
            except Exception as e:
                log.error(f"ERROR setting kpfasemble outdir")
                log.error(e)

    @classmethod
    def post_condition(cls, args):
        utnow = datetime.utcnow()
        date = utnow-timedelta(days=1)
        date_str = date.strftime('%Y%b%d').lower()
        outdir = Path(f"/s/sdata1701/{os.getlogin()}/{date_str}")
        tests = []
        if args.get('CRED2', True) is True:
            expr = f"$kpfguide.OUTDIR == '/s/sdata1701/kpfguide'"
            success = ktl.waitFor(expr, timeout=5)
            tests.append(success)
        if args.get('CRED2', True) is True:
            expr = f"$kpfguide.TRIGOUTDIR == '{outdir}/CRED2'"
            success = ktl.waitFor(expr, timeout=5)
            tests.append(success)
        if args.get('FVC1', False) is True:
            expr = f"$kpffvc.SCIOUTDIR == '{outdir}/FVC1'"
            success = ktl.waitFor(expr, timeout=5)
            tests.append(success)
        if args.get('FVC2', False) is True:
            expr = f"$kpffvc.CAHKOUTDIR == '{outdir}/FVC2'"
            success = ktl.waitFor(expr, timeout=5)
            tests.append(success)
        if args.get('FVC3', False) is True:
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
        if args.get('CaHK', True) is True:
            expr = f"$kpf_hk.RECORDDIR == '{outdir}/CaHK'"
            success = ktl.waitFor(expr, timeout=5)
            tests.append(success)
        if args.get('Green', True) is True:
            expr = f"$kpfgreen.FITSDIR == '{outdir}/Green'"
            success = ktl.waitFor(expr, timeout=5)
            tests.append(success)
        if args.get('Red', True) is True:
            expr = f"$kpfred.FITSDIR == '{outdir}/Red'"
            success = ktl.waitFor(expr, timeout=5)
            tests.append(success)
        if args.get('L0', True) is True:
            expr = f"$kpfassemble.OUTDIR == '{outdir}/L0'"
            success = ktl.waitFor(expr, timeout=5)
            tests.append(success)

        return np.all(np.array(tests))
