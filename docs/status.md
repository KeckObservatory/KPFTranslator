# Instrument Status

### Current and Past Announcements

* 2025 August: [26A Stability Announcement](KPF Stability Statement - August 15 2025.pdf)
* 2023 September: [Keck Science Meeting presentation](Keck Science Meeting 2023 Breakout Session.pdf)

### Status Summary by Subsystem

This is an attempt to summarize the status of various sub-systems of the instrument.  Each sub-system name is color coded to indicate the status at a glance: <font color="green">green</font> means functioning normally, <font color="orange">orange</font> means mostly normal, but with some caveats or minor issues, and <font color="red">red</font> means the sub-system is compromised in some way.

Last Status Update: 2025-10-22

- **<font color="orange">Detector Noise</font>**: Starting in November of 2024, additional pattern noise has been present on the detectors.  We have been working on eliminating the spurious nose, but we have been unable to completely remove it.  As of late-October 2025 the read noise on the Green side remains elevated (~10 electrons), while the red side is near our nominal target (~4.3 electrons).
- **<font color="orange">LFC</font>**: We are evaluating the reliability of the LFC after recent service. Initial indications look prominsing on reliability, though the bluest flux (below ~490 nm) is not consistent.
- **<font color="green">Etalon</font>**: Operational.
- **<font color="red">Detector Cooling Systems</font>**: Both detectors are now cooled with closed cycle refrigerators (CCRs). The green side CCR has  problems and has very little overhead on maintaining temperature and has quasi-periodic deviations which affect the detector.  Red side is performing well.
- **<font color="green">Detector Errors</font>**: The red and green detectors suffer from occasional “start state errors” in which the affected detector remains in the start phase and does not produce a useful exposure. The observing scripts detect this, abort the current exposure (with read out) and start a fresh exposure on both cameras. **No action is necessary on the part of the observer.**  The occurrence rate is such that around one in every 180 exposures is affected by one of the two detectors experiencing this error.
- **<font color="green">Ca H&K Detector</font>**: The CA H&K detector is operational.
- **<font color="green">Exposure Meter Terminated Exposures</font>**: Operational.
- **<font color="green">Tip Tilt Corrections</font>**: The tip tilt axis are currently correcting as expected.
- **<font color="green">Double Star Observations</font>**: Operational.
- **<font color="green">Simultaneous Calibration (SimulCal)</font>**: Simultaneous calibrations are supported.
- **<font color="orange">Nod to Sky Observations</font>**: For observations which need a sky measurement other than the built in sky fibers, nodding away to a sky position can be accomplished manually by running separate OBs for the target and sky and asking the OA to offset the telescope as appropriate.  We plan to build a separate Nod To Sky observing mode which will accomplish this within a single OB, but that is not yet available.
- **<font color="red">Off Target Guiding</font>**: Not yet commissioned.  Currently, the tip tilt system must be able to detect the science target in order to position it on the fiber.
