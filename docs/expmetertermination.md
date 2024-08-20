# Exposure Meter Termination

KPF contains an [exposure meter](exposuremeter.md) which can measure the flux weighted midpoint of an exposure. This can also be used to terminate a science exposure once a desired signal level is reached. To do this the system will track the flux measured in the exposure meter spectra binned in to 4 passbands, each about 100nm wide, centered on 498.125nm, 604.375nm, 710.625nm, and 816.875nm respectively.

To use exposure meter termination, the observer sets `ExpMeterMode: control` in the OB and then chooses one wavelength band to trigger on (using the `ExpMeterBin` OB value) and then chooses the target flux (in e-/nm via the `ExpMeterThreshold` OB value) in the resulting **science** spectrum that is desired.  The system will convert the target value for the science spectrum in to a total ADU count for the exposure meter in that particular bandpass and when that threshold is surpassed, the exposure will stop.  Regardless of whether that exposure meter threshold is passed, the exposure will stop when the nominal exposure time is reached.  Thus when using exposure meter termination, the `ExpTime` parameter should be thought of as the maximum allowed exposure time.

For example, an OB with the following values:
```
  ExpTime: 300
  ExpMeterMode: control
  ExpMeterBin: 604.375
  ExpMeterThreshold: 50000
```
will terminate when the exposure meter flux reaches a value which should result in approximately 50,000 e-/nm signal in the resulting science spectrum at about 604nm **or** when the total exposure time reaches 300 seconds, whichever comes first.
