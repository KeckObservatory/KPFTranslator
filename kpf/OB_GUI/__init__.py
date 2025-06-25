##-------------------------------------------------------------------------
## Keck Horizon
##-------------------------------------------------------------------------
def above_horizon(az, el):
    '''From https://www2.keck.hawaii.edu/inst/common/TelLimits.html
    Az 5.3 to 146.2, 33.3
    Az Elsewhere, 18
    '''
    if az >= 5.3 and az <= 146.2:
        horizon = 33.3
    else:
        horizon = 18
    return el > horizon


def near_horizon(az, el, margin=5):
    '''From https://www2.keck.hawaii.edu/inst/common/TelLimits.html
    Az 5.3 to 146.2, 33.3
    Az Elsewhere, 18
    '''
    if az >= 5.3 and az <= 146.2:
        horizon = 33.3 - margin
    else:
        horizon = 18 - margin
    return el > horizon
