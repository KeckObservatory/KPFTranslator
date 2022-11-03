def standardize_lamp_name(input_name):
    '''Take input string of a lamp name selected from the names from
    kpfcal.OCTAGON plus "WideFlat", "ExpMeterLED", "CaHKLED", "SciLED", and
    "SkyLED" and return a name which can be used in the kpflamps service.

    kpflamps keywords:
      EXPMLED = Exp Meter Back Illum LED
      FLATFIELD = Flatfield fiber
      HKLED = HK Back-Illumination LED
      OCTFLAT = Octagon flatfield
      SCILED = Science Back-Illumination LED
      SKYLED = Sky Back-Illumination LED
      TH_DAILY = ThAr Daily
      TH_GOLD = ThAr Gold
      U_DAILY = UNe Daily
      U_GOLD = UNe Gold

    octagon_names = ['BrdbandFiber', 'U_gold', 'U_daily', 'Th_daily',
                     'Th_gold', 'WideFlat']
    '''
    if input_name in [None, '']:
        return None
    lamp_name = {'BrdbandFiber': 'OCTFLAT',
                 'U_gold': 'U_GOLD',
                 'U_daily': 'U_DAILY',
                 'Th_daily': 'TH_DAILY',
                 'Th_gold': 'TH_GOLD',
                 'WideFlat': 'FLATFIELD',
                 'ExpMeterLED': 'EXPMLED',
                 'CaHKLED': 'HKLED',
                 'SciLED': 'SCILED',
                 'SkyLED': 'SKYLED',
                 }
    if input_name not in lamp_name.keys():
        return None
    lamp = lamp_name.get(input_name)
    allowed_lamps = ['EXPMLED', 'FLATFIELD', 'HKLED', 'OCTFLAT', 'SCILED',
                     'SKYLED', 'TH_DAILY', 'TH_GOLD', 'U_DAILY', 'U_GOLD']
    if lamp not in allowed_lamps:
        return None
    return lamp
