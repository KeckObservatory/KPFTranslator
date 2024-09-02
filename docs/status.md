# Instrument Status

KPF has been commissioned on sky, and is available for use. Many aspects of the instrument are still being optimized and the long term stability is still under evaluation. Short term stability looks excellent (exceeding the 50 cm/s target spec within a night) and we expect measures of the long term RV precision to become available as the DRP evolves.

A detailed summary of the instrument status was presented at the September 2023 Keck Science Meeting. The slides from that presentation are available in [PDF format](Keck Science Meeting 2023 Breakout Session.pdf).

<font color="red">**Important Notice**</font>: KPF will have a lengthy “servicing mission” during 24B to perform several upgrades.  This will involve warm up of the detectors.  The work is expected to commence around Oct 27 and be complete before Nov 24.


### Subsystem Status

This is an attempt to summarize the status of various sub-systems of the instrument.  Each sub-system name is color coded to indicate the status at a glance: <font color="green">green</font> means functioning normally, <font color="orange">orange</font> means mostly normal, but with some caveats or minor issues, and <font color="red">red</font> means the sub-system is compromised in some way.

- **<font color="orange">Tip Tilt Corrections</font>**: The tip tilt stage X-axis has degraded once again (as of 2024 Aug 22) and we are not making fast tip tilt corrections in X.  Troubleshooting is underway.
- **<font color="green">Ca H&K Detector</font>**: The CA H&K detector is operational.
- **<font color="green">Double Star Observations</font>**: Operational.
- **<font color="green">Etalon</font>**: Operational and providing the expected flux.
- **<font color="green">LFC</font>**: Is operating normally. 
- **<font color="green">Detector Systems</font>**: The red and green detectors suffer from occasional “start state errors” in which the affected detector remains in the start phase and does not produce a useful exposure. The observing scripts now detect this occurrence, abort the current exposure (with read out) and start a fresh exposure on both cameras. No action is necessary on the part of the observer.  This costs about a minute of time for this to happen, but the resulting data should be normal (unless another error occurs).  The occurrence rate for these problems is 0.34% on the green detector and 0.22% on the red, so around one in every 180 exposures is affected by one of the two detectors experiencing this error.
- **<font color="green">Simultaneous Calibration (SimulCal)</font>**: Simultaneous calibrations are supported.  Observers have the option of manually specifying the ND filters to balance the calibration flux or using the `AutoNDFilters` option in the OB to have an algorithm set the filters based on the KPF ETC, the target parameters in the OB, and a reference calibration brightness value.  See the [Nighttime Calibrations](nighttimecals.md) page for more info.
- **<font color="orange">Exposure Meter Terminated Exposures</font>**: The control system supports exposure meter terminated exposures (`ExpMeterMode: control` in the OB), however we are still documenting performance on sky.
- **<font color="orange">Nod to Sky Observations</font>**: For observations which need a sky measurement other than the built in sky fibers, nodding away to a sky position can be accomplished manually by running separate OBs for the target and sky and asking the OA to offset the telescope as appropriate.  We plan to build a separate Nod To Sky observing mode which will accomplish this within a single OB, but that is not yet ready.
- **<font color="red">Off Target Guiding</font>**: Not yet commissioned.  Currently, the tip tilt system must be able to detect the science target in order to position it on the fiber.
