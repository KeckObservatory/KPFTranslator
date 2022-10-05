import ktl

def fiu_hatch_is_open():
    '''Verifies that FIU hatch is open
    '''
    kpffiu = ktl.cache('kpffiu')
    return kpffiu['HATCH'].read() == 'Open'


def fiu_hatch_is_closed():
    '''Verifies that FIU hatch is closed
    '''
    kpffiu = ktl.cache('kpffiu')
    return kpffiu['HATCH'].read() == 'Closed'
