# Guider

The KPF guide camera views the science field, but behind a long pass dichroic which sends light blueward of about 950nm to the science and Ca H&K fibers. As a result, the guide camera was chosen to be a "short wave IR" camera utilizing an InGaS detector.

| Camera Model | First Light CRED2 |
| ------------ | ----------------- |
| Pixel Scale | 0.056 arcsec/pix |
| Field of View | 35 x 28 arcseconds |
| Frame Rate | up to 400 Hz (100 Hz recommended) |
| Passband | 950-1200 nm (0.95-1.2 microns) |
| Gain Settings | high, medium, low |

> Note that while the camera can operate at 400 Hz, the practical limit for operations is around 100-150 Hz due to tip tilt system limitations.

Rather than using traditional telescope guiding, the guide camera takes images at high frame rates and sends corrections to a fast tip tilt mirror situated just outside the FIU. We recommend running the system at 100 Hz for optimum performance. The system will offload corrections from the tip tilt mirror to the telescope drive system periodically as needed to keep the tip tilt mirror within its optimum range of travel.

The OAs use a separate GUI for controlling the KPF tip tilt system (not the usual Magiq interface used on other instruments).  The OAs can run Magiq in "centroid only" mode which will provide FWHM and flux feedback to the observer in the normal Magiq display. 
