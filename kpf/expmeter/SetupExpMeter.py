import traceback

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.expmeter.SetExpMeterTerminationParameters import SetExpMeterTerminationParameters


class SetupExpMeter(KPFFunction):
    '''Configure the exposure meter using the given OB arguments.

    Args:
        ExpMeterMode (str): See Science OB definition.
        TriggerExpMeter (bool): See Science OB definition.

    KTL Keywords Used:

    - `kpf_expmeter.USETHRESHOLD`
    - `kpfconfig.EXPMETER_ENABLED`

    Functions Called:

    - `kpf.expmeter.SetExpMeterTerminationParameters`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        USETHRESHOLD = ktl.cache('kpf_expmeter', 'USETHRESHOLD')
        EXPMETER_ENABLED = ktl.cache('kpfconfig', 'EXPMETER_ENABLED')

        ## ----------------------------------------------------------------
        ## Configure exposure meter
        ## ----------------------------------------------------------------
        log.debug('Setting up exposure meter using SetupExpMeter')
        EM_mode = args.get('ExpMeterMode', 'off')
        EM_enabled = EXPMETER_ENABLED.read() == 'Yes'
        if EM_mode == 'monitor' and EM_enabled:
            USETHRESHOLD.write('No')
            args['TriggerExpMeter'] = True
        elif EM_mode == 'control' and EM_enabled:
            args['TriggerExpMeter'] = True
            try:
                SetExpMeterTerminationParameters.execute(args)
            except Exception as e:
                log.error('SetExpMeterTerminationParameters failed')
                log.error(e)
                traceback_text = traceback.format_exc()
                log.error(traceback_text)
                USETHRESHOLD.write('No')
        elif EM_mode in ['off', False]: # pyyaml converts 'off' to False, so handle both
            args['TriggerExpMeter'] = False
        elif EM_enabled == False:
            log.warning('ExpMeter is disabled')
            args['TriggerExpMeter'] = False
        else:
            log.warning(f"ExpMeterMode {EM_mode} is not available")
            USETHRESHOLD.write('No')

        # Must return args as we have edited them
        return args


    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('--nointensemon', dest="nointensemon",
                            default=False, action="store_true",
                            help='Skip the intensity monitor measurement?')
        return super().add_cmdline_args(parser)
