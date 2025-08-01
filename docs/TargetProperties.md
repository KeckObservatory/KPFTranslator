# Target Properties

**TargetName**: `str`
  Name of the target, chosen by the observer. This will appear in the TARGNAME FITS header field and is the equivalent of the star list target name, but is not the same as the OBJECT field (see the Observation Properties for that).

**GaiaID**: `str`
  Gaia ID of the target (e.g. DR3 123456789012345678)

**2MASSID**: `str`
  2MASS ID of the target (e.g. J12345678-1234567)

**Parallax**: `float`
  [milliarcsec] Parallax of the target

**RadialVelocity**: `float`
  [km/s] Estimated radial velocity of the target

**Gmag**: `float`
  [magnitude] Gaia G magnitude of the target. This is used for the algorithm which automatically sets the exposure meter exposure time and the algorithm which sets the simultaneous calibration filters.

**Jmag**: `float`
  [magnitude] J magnitude of the target. This is used by the algorithm which automatically sets the guider gain and frame rate.

**Teff**: `float`
  [K] Effective temperature of the target (allowed range 2600 - 45000 K). This is used by the algorithm which sets the simultaneous calibration filters. For that to work, this must lie within the range of 2700 - 6600 K.

**RA**: `str`
  [hh:mm:ss.ss] Right Ascension of the target (at Epoch)

**Dec**: `str`
  [dd:mm:ss.ss] Declination of the target (at Epoch)

**Equinox**: `str`
  [str] Equinox of the coordinate system (in Jyear format, e.g. J2000 or decimal year, e.g. 2000.0)

**PMRA**: `float`
  [seconds-of-time/year] Proper motion in RA

**PMDEC**: `float`
  [arcsec/year] Proper motion in Dec

**Epoch**: `str`
  [str] Epoch of the coordinate measurement

**DRA**: `float`
  [arcsec/hr divided by 15] Non sidereal tracking rate in RA

**DDEC**: `float`
  [arcsec/hr] Non sidereal tracking rate in Dec

