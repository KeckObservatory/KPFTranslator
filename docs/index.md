# Keck Planet Finder (KPF)

## Instrument Status

KPF has been commissioned on sky, and is available for use. Many aspects of the instrument are still being optimized and the long term stability is still under evaluation. Short term stability looks excellent (exceeding the 50 cm/s target spec within a night) and we expect measures of the long term RV precision to become available as the DRP evolves.

See [KPF Status Summary and Blog](https://keckobservatory.atlassian.net/wiki/spaces/KPF/overview) for the latest details on the instrument's operational status broken down by subsystem.

A detailed summary of the instrument status was presented at the September 2023 Keck Science Meeting. The slides from that presentation are available in [PDF format](Keck Science Meeting 2023 Breakout Session.pdf).

## Instrument Description

The Keck Planet Finder (KPF) is a ﬁber-fed, high-resolution, high-stability cross dispersed, spectrometer designed to characterize exoplanets via Doppler spectroscopy with a goal of a single measurement precision of 0.3 m/s or better. KPF covers a wavelength range of 445 nm to 870 nm over green and red channels.

KPF consists of 3 independant spectrographs:

* The primary science spectrograph described above which is designed to be highly stable and has both a green and red arm. The spectrograph optical bench is made from low expansion Zerodur and is kept is a temperature stabilized environment.
* A Calcium H&K spectrograph which gets the light blueward of the main science spectrograph and is used to simultaneously measure stellar activity using the Ca H&K lines.
* The exposure meter spectrograph which gets a portion of the science light and is used to measure the flux level during long exposures of the primary science detectors. The exposure meter both measures the time weighted flux midpoint of each exposure, and can also be used to terminate an exposure at a specified flux level.

All three spectrographs are fed by optical fiber from the Fiber Injection Unit (FIU) which sits on the Keck I AO bench. The light entering the FIU is not AO corrected, but is fed off a fast tip tilt mirror which is used to maintain the target star's position on the science fiber within 50 mas rms of the fiber center. Performance of the tip tilt loop is to be confirmed during commissioning.

During observations, the spectrograph can be fed with light from a simultaneous calibration fiber. This places calibration light alongside science and sky spectra in the pseudo-slit. The calibration light is fed from the calibration bench which contains several calibration sources.

In addition to the simultaneous calibration light, the calibration bench can be configured to feed light up to the FIU and through the science and sky fibers in order to bring cal light in to the science and sky portions of the pseudo-slit.

![The system overview diagram showing the relationships between the different subsystems of the instrument.](figures/system_overview_diagram.png)
> The system overview diagram showing the relationships between the different subsystems of the instrument.

![KPF's Zerodur optical bench during integration at the Space Sciences Lab at UC Berkeley. The echelle grating can be seen at the upper right.](figures/Echelle_installation_Dec_2021.jpeg)
> KPF's Zerodur optical bench during integration at the Space Sciences Lab at UC Berkeley. The echelle grating can be seen at the upper right.

