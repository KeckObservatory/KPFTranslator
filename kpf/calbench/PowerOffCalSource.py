import numpy as np

import ktl
from ddoitranslatormodule.BaseInstrument import InstrumentBase
from ddoitranslatormodule.DDOIExceptions import *

from ..utils import *


class PowerOffCalSource(InstrumentBase):
    '''Powers off one of the cal lamps via the `kpfpower` keyword service.
    
    The mapping between lamp name and power outlet is hard coded for now.
    The only check on this is that the log message will include the name
    of the power outlet which has been powered on as read from the _NAME
    keyword for that outlet.  No automatic checking of the name is currently
    performed, the only check is if a human reads the log line.
    
    The current mapping only handles the following lamps:
    - U_gold
    - U_daily
    - Th_daily
    - Th_gold
    - BrdbandFiber
    '''
    def __init__(self):
        super().__init__()
        self.ports = {'EtalonFiber': None,
                      'BrdbandFiber': 'OUTLET_CAL2_2',
                      'U_gold': 'OUTLET_CAL2_7',
                      'U_daily': 'OUTLET_CAL2_8',
                      'Th_daily': 'OUTLET_CAL2_6',
                      'Th_gold': 'OUTLET_CAL2_5',
                      'SoCal-CalFib': None,
                      'LFCFiber': None,
                      }

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfpower = ktl.cache('kpfpower')
        cal_source = args.get('cal_source', None)
        port = self.ports.get(cal_source, None)
        if port is not None:
            port_name = kpfpower[f"{port}_NAME"].read()
            print(f"  Powering off {cal_source}")
            print(f"    Unlocking {port}: {port_name}")
            kpfpower[f"{port}_LOCK"].write('Unlocked')
            print(f"    Turning on {port}: {port_name}")
            kpfpower[port].write('Off')
            print(f"    Locking {port}: {port_name}")
            kpfpower[f"{port}_LOCK"].write('Locked')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        '''Verifies that the relevant power port is actually off.
        '''
        kpfpower = ktl.cache('kpfpower')
        cal_source = args.get('cal_source', None)
        port = self.ports.get(cal_source, None)
        if port is not None:
            port_name = kpfpower[f"{port}_NAME"].read()
            print(f"    Reading {port}: {port_name}")
            state = kpfpower[port].read()
            if state != 'Off':
                msg = f"Final power state mismatch: {state} != Off"
                print(msg)
                return False
        print('    Done')
        return True
