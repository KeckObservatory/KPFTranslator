import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class ConfirmGuiding(KPFFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        ALL_LOOPS = ktl.cache('kpfguide', 'ALL_LOOPS')
        guide_here = args.get('GuideHere', True)
        guide_here_txt = {True: 'Active', False: 'Inactive'}[guide_here]
        timeout = args.get('guide_wait_timeout', 5)
        log.info(f"Waiting for kpfguide.ALL_LOOPS = {guide_here_txt}")
        success = ALL_LOOPS.waitfor(f"=='{guide_here_txt}'", timeout=timeout)

        if success == False:
            # Check with user
            SCRIPTMSG = ktl.cache('kpfconfig', 'SCRIPTMSG')
            msg = 'Waiting for user confirmation on tip tilt status'
            log.info(msg)
            SCRIPTMSG.write(msg)
            print()
            print("#####################################################")
            print(f"Timed out waiting for ALL_LOOPS == {guide_here_txt}")
            print("Double check that the OA is configuring the tip tilt system")
            print()
            print("Do you wish to abort the OB? (type: a or abort)")
            print("Do you wish to continute to wait? (type: w or wait)")
            print("or do you wish to proceed to the observation regardless of the tip tilt status? (type: o or observe)")
            print("(a/w/o) [w]:")
            print("#####################################################")
            print()
            user_input = input()
            log.debug(f'response: "{user_input}"')
            SCRIPTMSG.write('')
            if user_input.lower().strip() in ['n', 'no', 'a', 'abort', 'q', 'quit']:
                raise KPFException("User chose to halt execution")
            elif user_input.lower().strip() in ['o', 'p', 'observe', 'proceed']:
                return
            else:
                ConfirmGuiding.execute(args)

    @classmethod
    def post_condition(cls, args):
        pass
