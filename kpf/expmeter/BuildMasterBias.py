from pathlib import Path
import re
from datetime import datetime, timedelta
import numpy as np
from astropy.nddata import CCDData
import ccdproc

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript

# Suppress warnings about DATE-BEG and DATE-END, for example:
# WARNING: FITSFixedWarning: 'datfix' made the change 'Set MJD-BEG to 60199.135879 from DATE-BEG.
# Set MJD-END to 60199.135882 from DATE-END'. [astropy.wcs.wcs]
import warnings
from astropy.wcs import FITSFixedWarning
warnings.filterwarnings('ignore', category=FITSFixedWarning, append=True)


class BuildMasterBias(KPFFunction):
    '''Combine a set of bias files to make a master bias.

    Args:
        files (list): A list of files to combine.
        output (str): The output combined filename to write.

    KTL Keywords Used:

    - `kpf_expmeter.BIAS_FILE`
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'files', allowed_types=[list])

    @classmethod
    def perform(cls, args):
        biasfiles = [Path(biasfile) for biasfile in args.get('files')]
        log.debug(f"Combining {len(biasfiles)} bias frames:")

        biases = []
        timestamps = []
        for biasfile in biasfiles:
            log.debug(f"  {biasfile.name}")
            this_bias = CCDData.read(biasfile, unit="adu")
            biases.append(this_bias)
            timestamps.append(this_bias[0].header.get('DATE-BEG'))

        combiner = ccdproc.Combiner(biases)
        combiner.sigma_clipping(low_thresh=5, high_thresh=5)
        combined_average = combiner.average_combine()
        for i,timestamp in enumerate(timestamps):
            combined_average[0].header[f'DATEBEG{i:02d}'] = (timestamp,
                                       'DATE-BEG of file {i:02d}')
        utnow = datetime.utcnow()
        combined_average[0].header['DATEMADE'] = (utnow.isoformat(),
                                   'UT timestamp of file creation')

        if args.get('output', None) not in [None, '']:
            outputfile = Path(args.get('output')).expanduser()
        else:
            match_fn = re.match('([\w\d_]+)(\d{6})\.(\d{3})\.fits', biasfiles[0].name)
            if match_fn is not None:
                frameno = match_fn.group(2)
                outputfile = Path(f'/s/sdata1701/ExpMeterMasterFiles/MasterBias_{frameno}.fits')
            else:
                now_str = utnow.strftime('%Y%m%dat%H%M%S')
                outputfile = Path(f'/s/sdata1701/ExpMeterMasterFiles/MasterBias_{now_str}.fits')

        log.info(f"Writing {outputfile}")
        combined_average.write(outputfile, overwrite=True)
        if args.get('update', False) is True:
            bias_file = ktl.cache('kpf_expmeter', 'BIAS_FILE')
            bias_file.write(f"{outputfile}")

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('files', nargs='*',
                            help="The files to combine")
        parser.add_argument("--output", dest="output", type=str,
                            default='',
                            help="The output combined bias file.")
        parser.add_argument("--update", dest="update",
                            default=False, action="store_true",
                            help="Update the bias file in use with the newly generated file?")
        return super().add_cmdline_args(parser)
