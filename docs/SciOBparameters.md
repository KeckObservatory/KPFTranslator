# Science OB Contents

Here is an example science OB formatted as a text file (this is the YAML data format). The comments (preceded by a # symbol) are not needed, but are present to help the reader. 

```
Template_Name: kpf_sci
Template_Version: 1.0

# Target Info
TargetName: 10700               # Name 
GaiaID: DR3 2452378776434276992 # Gaia ID 
2MASSID: 01440402-1556141       # 2MASS ID 
Parallax: 273.81                # Parallax in arcsec
RadialVelocity: -16.597         # Radial Velocity in km/s
Gmag: 3.3                       # G band magnitude (eventualy used by exposure meter)
Jmag: 2.14                      # J band magnitude (eventualy used by guider)
Teff: 5266                      # Effective temperature
# Spectrograph Setup
TriggerCaHK: False              # Include CaHK in exposure (True/False)
TriggerGreen: True              # Include Green CCD in exposure (True/False)
TriggerRed: True                # Include Red CCD in exposure (True/False)
BlockSky: False                 # Close the sky fiber shutter during observations (True/False)
# Observations
SEQ_Observations:               # 
- Object: 10700                 # User settable comment
  nExp: 4                       # Number of exoposures in the OB
  ExpTime: 30                   # Exposure time of the main spectrometer and CaH&K. See Exposure Meter section below.
  ExpMeterMode: control         # "monitor" or "control" (to terminate exposure based on flux)
  AutoExpMeter: False           # Set the exposure meter exposure time automatically
  ExpMeterExpTime: 0.5          # Exposure time of the Exposure Meter subframes
  ExpMeterBin: 3                # Exposure meter wavelength bin to use for stopping exposure
  ExpMeterThreshold: 1e5        # Target science flux in e-/nm
  TakeSimulCal: True            # Take simultaneous calibrations? (True/False)
  AutoNDFilters: False          # Automatically set ND filters -- Not available at this time!
  CalND1: OD 4.0                # OD=Optical Density. Throughput = 10^-OD
  CalND2: OD 0.1                # 
```

Each value in the OB is described in more detail below.

**Template_Name and Template_Version** (`str`)
> These values indicate to the software what sort of observation this is and what script to execute. For a science observation, always use "kpf_sci" as the template name.

**TargetName**: (`str`)
> This is a name chosen by the observer.

**GaiaID and 2MASSID**: (`str`)
> These values are used by the DRP to identify the star and determine its properties.

**Parallax**: (`float`)
> Parallax in arcseconds.

**RadialVelocity**: (`float`)
> Radial Velocity in km/s.

**Gmag**: (`float`)
> This is used by the DRP and by the algorithm which automatically sets the exposure meter exposure time.

**Jmag**: (`float`)
> This is used by the algorithm which automatically sets the guider gain and frame rate.

**Teff**: (`float`)
> The effective temperature of the star.
<br>Allowed Range: 2600 - 45000

**TriggerCaHK, TriggerGreen, and TriggerRed**: (`bool`)
> These values indicate whether to trigger the respective camera during the science exposures. All of these cameras will be synced up and will get the same exposure time.

## SEQ_Observations

The `SEQ_Observations:` line is required. The following block of lines represent one entry in a list. If more than one set of exposures on a target is desired, this block of text can be repeated to build a second "observation" on the target with different parameters.

**Object**: (`str`)
> This value will go in to the FITS header as the OBJECT keyword value. This is can be used as a notes field for the observer to explain how this set of exposures differs from any following observations of this target. This field can be left blank or set to the target name, it is entirely up to the observer.

**nExp**: (`int`)
>The number of exposures to take.

**ExpTime**: (`float`)
> The exposure time in seconds. Note that if the exposure meter is controlling the exposure duration, this exposure time is the maximum value which will be allowed (the exposure meter may cut the exposure short if the desired flux level is reached).

**ExpMeterMode**: (`str`)
> For now, only the "monitor" mode is available. In "monitor" the exposure meter will take exposure during the science exposure and record fluxes. This data will be stored in the resulting FITS file can be used to determine the flux weighted exposure midpoint in time for accurate barycentric correction.
<br>Allowed Values: "monitor", "control", or "off"

**AutoExpMeter**: (`bool`)
> If this is True, the software will use the Gmag value to estimate a good exposure time for the individual exposure meter exposures and use that instead of the ExpMeterExpTime value below.

**ExpMeterExpTime**: (`float`)
> The exposure time in seconds for individual exposure meter exposures. This is ignored if AutoExpMeter is True.

**TakeSimulCal**: (`bool`)
> Should the instrument be configured to illuminate the simultaneous calibration fiber during the science exposure?

**AutoNDFilters**: (`bool`)
> Should the software automatically set the ND filters based on the target and exposure information? This is currently (June 2024) in a testing mode and is not recommended for normal use.

**CalND1** (`str`)
> The neutral density filter to put in the first filter
wheel. This affects both the simultaneous calibration light and light
which can be routed through the FIU to the science and sky fibers.
<br>Allowed Values: `OD 0.1`, `OD 1.0`, `OD 1.3`, `OD 2.0`, `OD 3.0`, `OD 4.0`

**CalND2** (`str`)
> The neutral density filter to put in the second filter
wheel. This affects only the light injected in to the simultaneous
calibration fiber.
<br>Allowed Values: `OD 0.1`, `OD 0.3`, `OD 0.5`, `OD 0.8`, `OD 1.0`, `OD 4.0`
