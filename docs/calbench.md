# Calibration Bench

The cal bench contains several calibration light sources and can inject light in to the simultaneous calibration fiber (one of the components of the pseudo slit) or to inject light to the FIU and thus illuminate the science and sky fibers with the chosen calibration lamp.

Most of the calibration sources are located in the "octagon".  A rotating fold mirror can direct light from one of 8 ports to the calibration fibers. The octagon light sources are:

- `EtalonFiber`: Light from a "SuperK" continuum source which has passed through the Etalon.
- `BrdbandFiber`: A broadband lamp.
- `U_gold`: A UNe arc lamp
- `U_daily`: A UNe arc lamp
- `Th_daily`: A ThAr arc lamp
- `Th_gold`: A ThAr arc lamp
- `SoCal-CalFib`: Light from the [Solar Calibrator](socal.md)
- `LFCFiber`: Light from the Laser Frequency Comb (LFC)


## Etalon

The KPF etalon is a thermally stable (~1 mK RMS) resonant cavity fed by an NKT SuperK EVO light source.  The resulting line forest covers all of the KPF science passband.  The Etalon spectrum evolves slowly with time, so it is not used for obsolte calibration, but it can be used to track the short time scale evolution of the instrument.  Effectively "filling in" between absolute wavelength calibrators such as the LFC or the arc lamps.

## Broadband Lamp

KPF takes relatively standard spectral flats using a broadband lamp.  Because of the extreme requirements for PRV measurements, the flats must be extraordinarily high signal to noise and be taken daily to track any changes.

## Arc Lamps

The arc lamps (ThAr and UNe) can be used for absolute wavelength calibration. Unlike the LFC, they do not have a regular spacing of lines, but they do provide lines in the bluest orders (see below).  Two of each lamp are available in the octagon at any time.

## Laser Frequency Comb

The LFC is the best calibrator due to the density of lines which allows a very precise measurement of the wavelength solution, but it is currently (early 2024) limited due to a lack of flux in the bluest orders.  For those, the traditional Thorium and Uranium lamps provide absolute calibration.
