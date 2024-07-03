# Overview and Exposure Timing

KPF utilizes 5 detectors during normal science operations. Two science detectors (green and red) sit on the main spectrograph bench in the facility basement and record the science spectrum which is used to calculate radial velocities. The Ca H&K Spectrograph is an independant optical system fed by a short fiber which runs from the FIU to a nearby echelle spectrograph which contains the third science detector. The exposure meter is another independent spectrograph which sits in the basement and contains the forth science detector. The fifth detector used during science operations is the CRED2 in the FIU and obtains fast frame rate images used to run the tip tilt system.

Because precision radial velocity measurements require exquisite timing, the red and green detectors must have their exposures synced up. To do this, KPF uses a timed shutter on their common light path (before the dichroic splits the light). This is the "Scrambler Timed Shutter". As a result, the red and green cameras are not triggered independently. Instead the KPF software takes a single set of exposure parameters and triggers each camera to begin an exposure, then opens and closes timed shutters to ensure simultaneity where needed.

In addition, the Scrambler Timed Shutter, also gates the light going to the exposure meter to ensure that its sensitivity to light is simultaneous to the red and green detectors.

The Ca H&K spectrograph has its own, separate timed shutter as it is on a completely independent light path to the other detectors. 

# Science Detector Specifications

| Parameter | Green CCD | Red CCD | Ca H&K CCD |
| --------- | --------- | ------- | ---------- |
| Readout Time | 47 s | 47 s | 1 s |
| Read Noise | AMP1: 4.0 e-<br>AMP2: 4.9 e- | AMP1: 4.1 e-<br>AMP2: 4.2 e- |  |
| Format | 4080x4080 | 4080x4080 | windowed to<br>1024x255 |
| Gain | ~5 e-/ADU | ~5 e-/ADU | 5.26 e-/ADU |
| Data Format | 32 bit | 32 bit | 16 bit |
| Saturation | ~2.1 x 10^9 ADU<br>(~150 ke-) | ~2.1 x 10^9 ADU<br>(~150 ke-) | 65,536 ADU<br>(344 ke-) |

Note that the Green and Red science detectors have 32 bit readouts instead of the more common 16 bit (which the Ca H&K detector uses).  This means that the values of the raw image pixels are not in the usual 0-65535 range for CCDs, but are instead much larger.  To convert to the more usual range we are used to, divide by 2^16 (65536) to get ADU values in that range.

# Fast Read Mode

## Summary

The Green and Red science detectors can operate in a fast readout mode.  This reduces the readout time to 16 seconds (and significantly increases the read noise), however changing the readout modes induces a temperature change at the detectors which can impact PRV measurements.  As a result, fast read mode observations should be limited to those instances where it is critical to the science (e.g. seismology or other high cadence observations of a single target) and which are scheduled such that the mode change will not have overly negative impact on other science that night. Fast read mode is not appropriate for long term cadenced RV measurements as the two read modes have different systematic offsets and so RV measurements of the same target taken in different modes can not be easily combined.

## Details

The KPF main spectrometer CCDs can be operated in two read modes: normal and fast.  The main difference is the time to read the CCDs, which is 47 sec in normal-read mode and 16 sec in fast-read mode.  In general, KPF observations should be taken in normal-read mode unless there is a highly compelling reason to operate in fast-read mode.

The fast-read mode is only offered for KPF observations where the speed will aid in resolving fast astrophysical phenomena (e.g., seismology) or for cases where short exposure times are required to avoid saturation and the efficiency is significantly improved by also reading the CCDs quickly (e.g., observing a very bright star during a planetary transit).  This applies to sequences of exposures ranging from 1 hour to 1 night in duration.  The fast-read mode should not be used to improve the efficiency of individual exposure or short sequences of exposures, which comprise the vast majority of KPF observations.

The motivation for this strategy is that **changing between the two modes imparts a ~10 mK temperature transient** to the CCDs, which shift and stretch at the nanometer level in response.  These perturbations violate the operating requirements of maintaining 1 mK rms temperature stability of the CCDs and lead to systematic errors in Doppler measurements on short timescales (< 20-30 min).  On longer timescales, the CCDs appear to relax back to their original state, but this has not been measured at the sub-30 cm/s level.  Out of conservatism, KPF is toggled between read modes as infrequently as possible.

Automated daily calibration sequences are taken in the normal-read mode and are used in the KPF Data Reduction Pipeline (DRP) to process spectra taken with both read modes.  **Radial velocities measured from KPF spectra in the two modes are offset; users cannot combine RVs from the two modes in a time series.**  On the other hand, RVs measured from spectra taken in the fast-read mode during a single night (which are processed with a common set of calibrations) have high Doppler stability over that night-long timescale; this is the main use case for the fast-read mode.

Some additional tradeoffs to consider are the increased read noise and the charge transfer inefficiency (CTI) in fast-read mode. As listed in the table below, the read noise (measured in rms noise per CCD pixel) is 1.5-2X higher in fast-read mode. This limits the utility of this mode for faint sources, which have higher Poisson noise per CCD pixel in the source spectrum.  In fast-read mode, the CCDs are read out using four amplifiers at a higher clock speed (instead of two amplifiers at a slower speed).  This strategy brings one amplifier on the Green CCD into play that has ~100x higher CTI than the others.  CTI smears the spectrum along the direction of the CCD rows (leaving a trail of charge along pixels as they are clocked).  As a result, stellar lines in the affected quadrant are smeared in the dispersion direction.  The intensity of the effect depends on the number of electrons in each pixel (i.e., the SNR of the spectrum), making this effect very difficult to calibrate for precise RV measurements.  When computing RVs for fast-read mode spectra, the KPF DRP ignores portions of the spectrum in the affected quadrant.  This increases the RV uncertainties in the fast-read mode and adds an additional RV zero-point offset between measurements in the two modes.  Fast spectroscopy to measure changes in line intensity (not line shape or center) can still be accomplished using spectra from the affected quadrant.

| Parameter | Normal Read Mode | Fast Read Mode |
| --------- | ------ | ---- |
| Readout Time | 47 s | 16 s |
| Read Noise | Green: 4.0, 4.9 e-<br>Red: 4.1, 4.2 e- | Green: 8.2, 9.7, 8.6, 6.9 e-<br>Red: 6.0, 5.8, 8.2, 6.6 e- |
| Charge Transfer |  | One green amp has ~100x higher CTI |
| Use Cases | Most KPF observations,<br>including cadence RPV measurements<br>and general spectroscopy | Sequences of short exposures whose<br>duration is 1 hour to 1 night. |

If you have questions about utilizing fast read mode, please contact [kpf_info](mailto:kpf_info@keck.hawaii.edu) well ahead of your run.
