# Observing Blocks (OBs)

The basic unit of KPF nighttime operations is the Observing Block (OB). An OB describes a single visit to a science target and the observations made there. The data in an OB can be divided in to 4 rough categories:

**Target information**: The OB will contain information about the target beyond what is in a typical Keck Star List entry in order to flow that information to the FITS header and the data reduction pipeline (DRP).

**Guide camera configuration**: The OB will also contain information about how to configure the guide camera and tip tilt system for this target.

**Instrument Setup**: The OB will also contain information about how to configure the instrument for this set of observations.

**Observations**: Finally, the OB will contain a list of "observations" to be made of the target. For typical KPF observers, this will only have one entry, but multiple entries are supported. Each entry describes a set of exposures on the target and contains the information on how those exposures should be executed.

The data contained in the OB is a set of keyword-value pairs. Observers can prepare OBs as text files which can be read in by the KPF software and executed or (once logged in to the KPF VNCs) they can use tools there to build the OBs and save them as files. 

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
# Guider Setup
GuideMode: manual               # "manual", "auto", "off", or "telescope"
GuideCamGain: low               # Guide camera gain; values = low | medium | high
GuideFPS: 100                   # Frames per second for guide camera (for tip-tilt)
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

**Template_Name and Template_Version**:<br>These values indicate to the software what sort of observation this is and what script to execute. For a science observation, always use "kpf_sci" as the template name.

**TargetName**:<br>This is a name chosen by the observer.

**GaiaID and 2MASSID**:<br>These values are used by the DRP to identify the star and determine its properties.

**Parallax and RadialVelocity**:<br>These values are used by the DRP.

**Gmag**:<br>This is used by the DRP and by the algorithm which automatically sets the exposure meter exposure time.

**Jmag**:<br>This is used by the algorithm which automatically sets the guider gain and frame rate.

**Teff**:<br>The effective temperature of the star is used by the DRP.

**GuideMode**:<br>The options are "manual", "auto", or "off". If "manual" is selected, the values for the gain and FPS below are used. If "auto" is selected, the camera gain and FPS values in the OB are ignored and the software will choose values based on the Jmag value.

**GuideCamGain and GuideFPS**:<br>The gain (high, medium, or low) and the frame rate (frames per second) at which to operate the guide camera. These are ignored if the GuideMode is set to "auto".

**TriggerCaHK, TriggerGreen, and TriggerRed**:<br>These values indicate whether to trigger the respective camera during the science exposures. All of these cameras will be synced up and will get the same exposure time.

**SEQ_Observations**:<br>This line is required. The following block of lines represent one entry in a list. If more than one set of exposures on a target is desired, this block of text can be repeated to build a second "observation" on the target with different parameters.

**Object**:<br>This value will go in to the FITS header as the OBJECT keyword value. This is can be used as a notes field for the observer to explain how this set of exposures differs from any following observations of this target. This field can be left blank or set to the target name, it is entirely up to the observer.

**nExp and ExpTime**:<br>The number of exposures and exposure time. Note that if the exposure meter is controlling the exposure duration, this exposure time is the maximum value which will be allowed (the exposure meter may cut the exposure short if the desired flux level is reached).

**ExpMeterMode**:<br>For now, only the "monitor" mode is available. In "monitor" the exposure meter will take exposure during the science exposure and record fluxes. This data will be stored in the resulting FITS file can be used to determine the flux weighted exposure midpoint in time for accurate barycentric correction.

**AutoExpMeter**:<br>If this is True, the software will use the Gmag value to estimate a good exposure time for the individual exposure meter exposures and use that instead of the ExpMeterExpTime value below.

**ExpMeterExpTime**:<br>The exposure time for individual exposure meter exposures. This is ignored if AutoExpMeter is True.

**TakeSimulCal**:<br>Should the instrument be configured to illuminate the simultaneous calibration fiber during the science exposure?

**AutoNDFilters**:<br>Should the software automatically set the ND filters based on the target and exposure information? This is not currently implemented and will be ignored!

**CalND1**:<br>Which neutral density filter should be used in the ND1 filter wheel to cut down the brightness of the simultaneous calibration light source? This is only needed if TakeSimulCal is True. Allowed values are "OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0", "OD 3.0", and "OD 4.0"

**CalND2**:<br>Which neutral density filter should be used in the ND2 filter wheel to cut down the brightness of the simultaneous calibration light source? This is only needed if TakeSimulCal is True. Allowed values are "OD 0.1", "OD 0.3", "OD 0.5", "OD 0.8", "OD 1.0", and "OD 4.0" 

# KPF OB GUI

A graphical tool has been built to help observers build their KPF OBs, it is launched automatically as part of the script to start all GUIs.

![A screenshot of the KPF OB GUI](figures/KPF_OB_GUI.png)
>  A screenshot of the KPF OB GUI. This tool is still under development and may change.

The top section of the GUI, "Instrument Status" shows whether an instrument script (e.g. an observation or calibration set) is being run and allows users to request that script stop.

The middle section can be used to load an OB from a file, build an OB from scratch using a Gaia DR3 catalog query, save the OB to a file, or execute the OB.

The lower section is where a user can fill out the OB parameters as described in the "KPF Science OB Contents" section above.