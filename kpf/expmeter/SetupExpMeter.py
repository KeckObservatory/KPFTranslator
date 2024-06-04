import traceback

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.expmeter.SetExpMeterTerminationParameters import SetExpMeterTerminationParameters


class SetupExpMeter(KPFTranslatorFunction):
    '''# Description
    Configure the exposure meter using the given OB arguments.

    ## KTL Keywords Used

    - `kpf_expmeter.USETHRESHOLD`
    - `kpfconfig.EXPMETER_ENABLED`

    ## Scripts Called

    - `kpf.expmeter.SetExpMeterTerminationParameters`

    ## Parameters

    **ExpMeterMode** (`str`)
    > See Science OB definition

    **TriggerExpMeter** (`bool`)
    > See Science OB definition
    '''
    abortable = False

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'Template_Name', allowed_values=['kpf_lamp', 'kpf_sci'])
        check_input(args, 'Template_Version', version_check=True, value_min='0.5')

    @classmethod
    def perform(cls, args, logger, cfg):
        kpf_expmeter = ktl.cache('kpf_expmeter')
        kpfconfig = ktl.cache('kpfconfig')

        ## ----------------------------------------------------------------
        ## Configure exposure meter
        ## ----------------------------------------------------------------
        log.debug('Setting up exposure meter using SetupExpMeter')
        EM_mode = args.get('ExpMeterMode', 'off')
        EM_enabled = kpfconfig['EXPMETER_ENABLED'].read() == 'Yes'
        if EM_mode == 'monitor' and EM_enabled:
            kpf_expmeter['USETHRESHOLD'].write('No')
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
                kpf_expmeter['USETHRESHOLD'].write('No')
        elif EM_mode in ['off', False]: # pyyaml converts 'off' to False, so handle both
            args['TriggerExpMeter'] = False
        elif EM_enabled == False:
            log.warning('ExpMeter is disabled')
        else:
            log.warning(f"ExpMeterMode {EM_mode} is not available")
            kpf_expmeter['USETHRESHOLD'].write('No')

        # Must return args as we have edited them
        return args


    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('--nointensemon', dest="nointensemon",
                            default=False, action="store_true",
                            help='Skip the intensity monitor measurement?')
        return super().add_cmdline_args(parser, cfg)
