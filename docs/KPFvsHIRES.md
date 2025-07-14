# Comparing KPF to HIRES

This page attempts to compare KPF and HIRES for users who may be wondering which instrument they should propose for.

Fundamentally HIRES is a more flexible instrument with selectable grating angles to control the wavelength coverage and selectable slits which allow the user to trade off throughput against spectral resolution while KPF is a fixed format spectrograph with a fixed input fiber.

HIRES also has a wider spectral coverage than KPF and even includes the option to change the internal optics to optimize either blue or red sensitivity. Though KPF has the Calcium H&K spectrograph, a dedicated arm to examine the 382-402 nm wavelength range around the Ca H&K lines.

KPF, on the other hand, has higher spectral resolution even though it has a larger entrance aperture on sky and so it may be more sensitive for use cases which need that combination.  Of course, KPF is also highly stabilized and is optimized for precision radial velocity measurements.


## Summary Table

| Comparison | KPF | HIRES |
| ---------- | --- | ----- |
| Optical Input | 1.14 arcsec octagonal fibers for<br>science and sky (fixed format) | Selectable deckers and slits for<br>different sky projections<br>(e.g., B5 = 0.87 x 3.5 arcsec) |
| Wavelength<br>Coverage | Fixed format:<br>445-870 nm (high-res)<br>382-402 nm (med-res) | ~300-1000 nm in an adjustable format<br>(moving the spectral format across detector) |
| Resolving Power | R=98k (445-870 nm) | depends on slit<br>e.g. R=49k for 0.86 arcsec-wide slit<br>R=80k for 0.40 arcsec-wide slit |
| Throughput<br>(sky to CCD) | ~8-10% peak-of-blaze (measured) | 5-6% peak-of-blaze<br>for B5-B1 deckers (measured) |
| Doppler<br>Precision | 0.5 m/s noise floor (req.)<br>0.3 m/s (goal) | ~2 m/s systematic noise floor |
| Doppler Speed | ~8-10x faster than HIRES | Limited by need for high SNR<br>to model iodine spectrum |

## Instrument Efficiency Comparison

Prior to delivery of KPF, the KPF Team made a series of HIRES observations of a spectrophotometric standard using deckers that spanned the full range of slit widths (but not all slit lengths, which only affects spatial information).  In the plot below, each blue line plots the peak-of-blaze efficiency from the top of the atmosphere to detected photoelectrons.  The red line is the predicted KPF efficiency curve based on Steve Gibson’s detailed optical model, efficiency curves for each optic (measured, if available), and a model of seeing and the atmosphere that match the airmass and seeing values for the actual HIRES observations.  We saw later that the KPF model is pretty good — it’s ~10% low for wavelengths > 500 nm and is too high for bluer wavelengths (>>10% off for the bluest wavelength).

![Comparison of the measured efficiency for HIRES to the KPF modeled efficiency (later validated, but see discussion above).](figures/KPFvsHIRES.png)
> Comparison of the measured efficiency for HIRES to the KPF modeled efficiency (later validated, but see discussion above).

The huge range of HIRES efficiency depending on decker is the biggest factor.  For science at lower resolution, KPF and HIRES have comparable efficiency. For high-resolution, KPF is much more efficient.

## Common Observations

WMKO obtained observations designed to compare KPF and HIRES directly on a variety of science targets during 2025A.  We will be posting links to the data here soon.
