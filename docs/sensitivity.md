# Spectrograph Sensitivity

For sensitivity estimates, please see the KPF exposure time calculator written by the instrument team. More information is available on the [KPF Exposure Time (and RV Precision) Calculator page](https://exoplanets.caltech.edu/kpf-exposure-time-calculator/) or go directly to GitHub to download the [exposure time calculator software](https://github.com/California-Planet-Search/KPF-etc).

# Acquiring Faint Targets

We use J-band magnitude as a rough guide for the guider sensitivity, but it is important to keep in mind that this is not a perfect match to the guider passband (950-1200 nm).  That said, we have acquired a J=17.0 (V=18.05) quasar using the guider with FPS=0.1 (10 second individual frame exposures).  It was not a strong detection: the target was just visible by eye in the images, but the guide system struggled to lock on to it.  Another test acquisition on a J=16.7 (V=17.6) object was correspondingly a bit easier.

We believe this performance can be improved substantially by using sky subtraction.  This is possible currently, but is a slow manual process to configure.  On the second test target above (J=16.7, V=17.6), we got reasonable signal using 0.25 FPS (4 second exposures) while using sky subtraction.  We are planning to script this process to make it easier and to integrate sky subtraction in to the OA's GUI for controlling the tip tilt, but the timeline for that is still TBD.

If you need to acquire very faint targets (J > 16), please reach out to your SA ahead of time to discuss strategies.

# Zero Point Analysis

From a collection of anonymized DRP products from the first few years of observations, we have used the DRP's reported signal to noise as a probe of KPF's sensitivity.  Specifically, we have measured the photometric zero point of the instrument at various wavelengths. The 5 notebooks below explore different aspects of the instrument and operations.

- [Examine Properties of Data Set](ZeroPointAnalysis/1-PrepareDataFile/1-PrepareDataFile.md)
- [Find Zero Point of Exposure Meter](ZeroPointAnalysis/2-ExpMeterZeroPoint/2-ExpMeterZeroPoint.md)
- [Find Zero Point of Instrument](ZeroPointAnalysis/3-InstrumentZeroPoint/3-InstrumentZeroPoint.md)
- [Find the Best Exposure Meter Bin](ZeroPointAnalysis/4-BestExpMeterBin/4-BestExpMeterBin.md)
- [Examine the Distribution of Slowdown Factors](ZeroPointAnalysis/5-ETCs/5-ETCs.md)
