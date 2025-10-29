# Overview and Exposure Timing

KPF utilizes 5 detectors during normal science operations. Two science detectors (green and red) sit on the main spectrograph bench in the facility basement and record the science spectrum which is used to calculate radial velocities. The Ca H&K Spectrograph is an independant optical system fed by a short fiber which runs from the FIU to a nearby echelle spectrograph which contains the third science detector. The exposure meter is another independent spectrograph which sits in the basement and contains the forth science detector. The fifth detector used during science operations is the CRED2 in the FIU and obtains fast frame rate images used to run the tip tilt system.

Because precision radial velocity measurements require exquisite timing, the red and green detectors must have their exposures synced up. To do this, KPF uses a timed shutter on their common light path (before the dichroic splits the light). This is the "Scrambler Timed Shutter". As a result, the red and green cameras are not triggered independently. Instead the KPF software takes a single set of exposure parameters and triggers each camera to begin an exposure, then opens and closes timed shutters to ensure simultaneity where needed.

In addition, the Scrambler Timed Shutter, also gates the light going to the exposure meter to ensure that its sensitivity to light is simultaneous to the red and green detectors.

The Ca H&K spectrograph has its own, separate timed shutter as it is on a completely independent light path to the other detectors. 

# Science Detector Specifications

| Parameter | Green CCD | Red CCD | Ca H&K CCD |
| --------- | --------- | ------- | ---------- |
| Readout Time | 47 s | 47 s | 1 s |
| Read Noise | see [status page](status.md) | AMP1: 4.3 e-<br>AMP2: 4.3 e- |  |
| Format | 4080x4080 | 4080x4080 | windowed to<br>1024x255 |
| Gain | ~5 e-/ADU | ~5 e-/ADU | 5.26 e-/ADU |
| Data Format | 32 bit | 32 bit | 16 bit |
| Saturation | ~2.1 x 10^9 ADU<br>(~150 ke-) | ~2.1 x 10^9 ADU<br>(~150 ke-) | 65,536 ADU<br>(344 ke-) |

Note that the Green and Red science detectors have 32 bit readouts instead of the more common 16 bit (which the Ca H&K detector uses).  This means that the values of the raw image pixels are not in the usual 0-65535 range for CCDs, but are instead much larger.  To convert to the more usual range we are used to, divide by 2^16 (65536) to get ADU values in that range.
