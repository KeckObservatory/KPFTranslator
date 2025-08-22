from astropy.io import fits

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class WaitForL0File(KPFFunction):
    '''Wait a short time to see if `kpfassemble` writes a new L0 file.  If it
    does, print a log line with that file name.

    KTL Keywords Used:

    - `kpfassemble.LOUTFILE`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        log.debug('Waiting for new L0 file')
        LOUTFILE = ktl.cache('kpfassemble', 'LOUTFILE')
        initial_LOUTFILE = LOUTFILE.read()
        timeout = 10
        timeout = cfg.getfloat('times', 'L0_file_creation', fallback=10)
        found_new_file = LOUTFILE.waitFor(f'!="{initial_LOUTFILE}"',
                                          timeout=timeout)
        if found_new_file is True:
            new_file = LOUTFILE.read()
            try:
                hdr = fits.getheader(new_file, ext=0)
                green_file = hdr.get('GRFILENA')
                red_file = hdr.get('RDFILENA')
                new_file_name = Path(new_file).name
                log.info(f"L0 file {new_file_name} assembled from {green_file},{red_file}")
            except:
                log.info(f'L0 file {new_file} assembled')
        else:
            log.debug('WaitForL0File did not find new file')


    @classmethod
    def post_condition(cls, args):
        pass
