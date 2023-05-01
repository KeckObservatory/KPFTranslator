import time
from pathlib import Path
import numpy as np
from astropy.io import fits
from astropy import stats

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class BuildMasterBias(KPFTranslatorFunction):
    '''
    Args:
    =====
    :: 
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'files', allowed_types=[list])

    @classmethod
    def perform(cls, args, logger, cfg):
        biasfiles = args.get('files')
        biasfiles = [Path(biasfile) for biasfile in biasfiles]
        bias_hduls = [fits.open(f"{file}") for file in biasfiles]
        biases = [hdul[0].data[:, 1:1069] for hdul in bias_hduls]
        log.info(f"Combining {len(biasfiles)} ExpMeter bias frames")
        for i,bias in enumerate(biases):
            mean, med, std = stats.sigma_clipped_stats(bias, sigma=2, maxiters=5)
            log.info(f"  {biasfiles[i].name}: mean, med, std = {mean:.1f}, {med:.1f}, {std:.1f}")
        median = np.median(biases, axis=0)
        mean, med, std = stats.sigma_clipped_stats(median, sigma=2, maxiters=5)
        log.info(f"ExpMeter combined bias mean, med, std = {mean:.1f}, {med:.1f}, {std:.1f}")
        
        if args.get('output', None) is None:
            outputfile = Path('~/combined_bias.fits').expanduser()
        else:
            outputfile = Path(args.get('output')).expanduser()
        log.info(f"Writing {outputfile}")
        fits.writeto(outputfile, median, overwrite=True)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('files', nargs='*',
                            help="The files to combine")
        parser.add_argument("--output", dest="output", type=str,
                            default='~/bias.fits',
                            help="The output combined bias file.")
        return super().add_cmdline_args(parser, cfg)
