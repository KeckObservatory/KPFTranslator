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