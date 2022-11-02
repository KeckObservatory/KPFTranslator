from time import sleep
import subprocess
import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from ..fiu.InitializeTipTilt import InitializeTipTilt
from ..guider.SetGuiderExpTime import SetGuiderExpTime

class TipTiltPerformanceCheck(KPFTranslatorFunction):
    '''Take data to measure tip tilt performance.
    
    fps
    exptime
    
    - Turn CONTINUOUS on
    - Turn TIPTILT on
    - Take image sequence at [fps] for [exptime] with open loop tracking
        - Store cube of images
        - Record OBJECTnRAW values
    - Turn TIPTILT_CONTROL on
    - For a set of gain values:
        - Set TIPTILT_GAIN
        - Take image sequence at [fps] for [exptime]
            - Store cube of images
            - Record OBJECTnRAW values
            - Record DISP2REQ commands
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        InitializeTipTilt.execute({})

        kpfguide = ktl.cache('kpfguide')
        kpfguide['CONTINUOUS'].write('Active')

        SetGuiderExpTime.execute({'exptime': 2})

        # Record OBJECTnRAW values
        SetTipTiltCalculations.execute({'calculations': 'Active'})
        kpfguide['LASTFILE'].wait()
        cmd = ['gshow', '-s', 'kpfguide', 'OBJECT%RAW', '-c', '-timestamp',
               '-binary', '>', '~/test.txt']
        process = subprocess.Popen(cmd)
        kpfguide['LASTFILE'].wait()
        process.kill()



    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
