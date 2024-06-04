Because KPF contains many detectors, but they are all synchronized in time, the raw data is immediately combined in to a "Level 0" (L0) multi-extension FITS file by the `kpfassemble` dispatcher.  Most users will want to use that L0 data for analysis or inspection.

# Raw Data

Each detector writes data to a separate output directory and `kpfassemble` will collect them from these to generate the L0 file.  This is a relatively quick process, typically the L0 file is written a few seconds after the component raw data are available on disk.

As mentioned on the [detectors](detectors.md) page, the Green and Red detectors have 32 bit ADCs and thus the pixel data do not fall on the usual 0-65535 range you may be used to.

# L0 Data

The L0 data is a multi extension FITS file consisting of the following HDUs:

| HDU # | HDU Name | Notes |
| ---------- | -------- | ----- |
| 0  | PRIMARY | Header only, no image data |
| 1  | GREEN_AMP1 | Green image data |
| 2  | GREEN_AMP2 | Green image data |
| 3  | RED_AMP1 | Red image data |
| 4  | RED_AMP2 | Red image data |
| 5  | CA_HK | Ca H&K image data |
| 6  | EXPMETER_SCI | Table of processed exposure meter spectra |
| 7  | EXPMETER_SKY | Table of processed exposure meter spectra |
| 8  | GUIDER_AVG | The average guider image over the duration<br>of the exposure |
| 9  | GUIDER_CUBE_ORIGINS | Table of telemetry from the tip tilt system |
| 10 | TELEMETRY | Table of instrument telemetry |

This can change depending on the composition of the science observation.  For example, if the Ca H&K detector was not triggered, that extension would not be used.
