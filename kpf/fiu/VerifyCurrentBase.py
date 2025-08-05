import numpy as np

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class VerifyCurrentBase(KPFFunction):
    '''Check whether the tip tilt system's target pixel (kpffiu.CURRENT_BASE)
    is consistent with the selected pointing origin (dcs.PONAME)

    KTL Keywords Used:

    - `dcs1.PONAME`
    - `kpfguide.CURRENT_BASE`
    - `kpfguide.SCIENCE_BASE`
    - `kpfguide.SKY_BASE`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        ponamekw = ktl.cache('dcs1', 'PONAME')
        poname = ponamekw.read().upper()

        kpfguide = ktl.cache('kpfguide')
        current_base = kpfguide['CURRENT_BASE'].read(binary=True)
        science_base = kpfguide['SCIENCE_BASE'].read(binary=True)
        sky_base = kpfguide['SKY_BASE'].read(binary=True)

        science_match = np.all(np.isclose(current_base, science_base, atol=0.01))
        sky_match = np.all(np.isclose(current_base, sky_base, atol=0.01))
        msg = f"CURRENT_BASE="
        if science_match:
            log.debug(f"CURRENT_BASE is science fiber, PO = {poname}")
            msg += 'SCIENCE_BASE'
        elif sky_match:
            log.debug(f"CURRENT_BASE is sky fiber, PO = {poname}")
            msg += 'SKY_BASE'
        else:
            log.debug(f"CURRENT_BASE is {current_base}, PO = {poname}")
            msg += 'custom'

        poname_match = (science_match and poname == 'KPF')\
                       or (sky_match and poname == 'SKY')
        if poname_match:
            msg += f" which is consistent with PONAME={poname}"
            log.debug(msg)
        else:
            msg += f" which is NOT consistent with PONAME={poname}"
            log.error(msg)
        print(msg)

        if args.get('query_user', False) == True and poname_match == False:
            # Check with user
            SCRIPTMSG = ktl.cache('kpfconfig', 'SCRIPTMSG')
            msg = 'Waiting for user confirmation on PO mismatch'
            log.info(msg)
            SCRIPTMSG.write(msg)
            print()
            print("#####################################################")
            print("The dcs.PONAME value is incosistent with CURRENT_BASE")
            print("Please double check that the target object is where you")
            print("want it to be before proceeding.")
            print()
            print("Do you wish to continue executing this OB?")
            print("(y/n) [y]:")
            print("#####################################################")
            print()
            user_input = input()
            log.debug(f'response: "{user_input}"')
            SCRIPTMSG.write('')
            if user_input.lower().strip() in ['n', 'no', 'a', 'abort', 'q', 'quit']:
                raise KPFException("User chose to halt execution")

        return poname_match

    @classmethod
    def post_condition(cls, args):
        pass