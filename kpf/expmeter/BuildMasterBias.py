from pathlib import Path
import re
from datetime import datetime, timedelta
import numpy as np
from astropy.nddata import CCDData
import ccdproc

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)

# Suppress warnings about DATE-BEG and DATE-END, for example:
# WARNING: FITSFixedWarning: 'datfix' made the change 'Set MJD-BEG to 60199.135879 from DATE-BEG.
# Set MJD-END to 60199.135882 from DATE-END'. [astropy.wcs.wcs]
import warnings
from astropy.wcs import FITSFixedWarning
warnings.filterwarnings('ignore', category=FITSFixedWarning, append=True)


class BuildMasterBias(KPFTranslatorFunction):
    '''
    Args:
    =====
    :files: A list of files to combine.
    :output: The output combined filename to write.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'files', allowed_types=[list])

    @classmethod
    def perform(cls, args, logger, cfg):
        biasfiles = [Path(biasfile) for biasfile in args.get('files')]
        biases = [CCDData.read(file, unit="adu") for file in biasfiles]

        combiner = ccdproc.Combiner(biases)
        combiner.sigma_clipping(low_thresh=5, high_thresh=5)
        combined_average = combiner.average_combine()

        if args.get('output', None) not in [None, '']:
            outputfile = Path(args.get('output')).expanduser()
        else:
            match_fn = re.match('([\w\d_]+)(\d{6})\.(\d{3})\.fits', biasfiles[0].name)
            if match_fn is not None:
                frameno = match_fn.group(2)
                outputfile = Path(f'/s/sdata1701/ExpMeterMasterFiles/MasterBias_{frameno}.fits')
            else:
                utnow = datetime.utcnow()
                now_str = utnow.strftime('%Y%m%dat%H%M%S')
                outputfile = Path(f'/s/sdata1701/ExpMeterMasterFiles/MasterBias_{now_str}.fits')

        log.info(f"Writing {outputfile}")
        combined_average.write(outputfile, overwrite=True)
        if args.get('update', False) is True:
            bias_file = ktl.cache('kpf_expmeter', 'BIAS_FILE')
            bias_file.write(f"{outputfile}")

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
                            default='',
                            help="The output combined bias file.")
        parser.add_argument("--update", dest="update",
                            default=False, action="store_true",
                            help="Update the bias file in use with the newly generated file?")
        return super().add_cmdline_args(parser, cfg)
