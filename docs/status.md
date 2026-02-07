# Instrument Status

### Current Announcements

* 2026 February: [26A Status Announcement](announcements/2026-02-01_26A-status.md)

### Status Summary by Subsystem

This is an attempt to summarize the status of various sub-systems of the instrument.  Each sub-system name is color coded to indicate the status at a glance: <font color="green">green</font> means functioning normally, <font color="orange">orange</font> means mostly normal, but with some caveats or minor issues, and <font color="red">red</font> means the sub-system is compromised in some way.

- **<font color="orange">Detector Noise</font>**: Starting in November of 2024, additional non-gaussian noise has been present on the detectors. As of late-October 2025 the read noise on the Green side remains elevated (~10 electrons), while the red side is at our target level (~4.3 electrons).
- **<font color="orange">LFC</font>**: Initial evaluations of the reliability of the LFC after the recent service look promising, though the bluest flux (below ~490 nm) is not consistent.
- **<font color="red">Detector Cooling Systems</font>**: The green side CCR has  very little overhead on maintaining temperature and has quasi-periodic deviations which affect the detector. Red side is performing well, but has shown evidence of a slow degradation of performance.
- **<font color="green">Etalon</font>**: Operational.
- **<font color="green">Detector Errors</font>**: The red and green detectors suffer from occasional “start state errors” in which the affected detector does not produce a useful exposure. The observing scripts detect this, abort the exposure (with read out) and start a fresh exposure on both cameras. **No action is necessary on the part of the observer.**  The occurrence rate is such that around one in every 180 exposures is affected by one of the two detectors experiencing this error.
- **<font color="green">Ca H&K Detector</font>**: The CA H&K detector is operational.
- **<font color="green">Exposure Meter Terminated Exposures</font>**: Operational.
- **<font color="green">Tip Tilt Corrections</font>**: The tip tilt axis are currently correcting as expected.
- **<font color="green">Double Star Observations</font>**: Operational.
- **<font color="green">Simultaneous Calibration (SimulCal)</font>**: Simultaneous calibrations are supported.
- **<font color="red">Off Target Guiding</font>**: Not yet commissioned.  Currently, the tip tilt system must be able to detect the science target in order to position it on the fiber.

Last Updated: 2026-02-01

### KPF Era 4.0 Temperature Stability Summary

KPF Era 4.0 began in late-October 2025 after Servicing Mission 4. We continue to have issues with the cooling systems for the detectors, especially the Green side.  We list below all temperature excursions in which one of the detectors deviated temperature by more than 5 mK from the set point.  Excursions of order 1 K (1000 mK) or more are expected to induce a radial velocity offset which is not calibratable.  We are providing this data as a guide, but users should not assume that past performance is a good indicator of future performance -- we have seen indications that the cooling systems are slowly degrading, so an increasing rate of these temperature excursions is a distinct possibility.

| Side | Date & Time (HST)   | Delta T  |
| ---- | ------------------- | -------- |
| G    | 2025-11-09 21:22:50 |     7 mK |
| G    | 2025-11-10 05:48:42 |   109 mK |
| G    | 2025-11-10 13:15:18 |  2825 mK |
| G    | 2025-11-15 11:50:50 |   250 mK |
| G    | 2025-11-16 16:04:50 |  5779 mK |
| G    | 2025-11-17 09:17:54 |  5564 mK |
| G    | 2025-11-17 10:34:40 |  6147 mK |
| G    | 2025-11-17 11:52:54 |    87 mK |
| G    | 2025-11-18 05:06:38 |  4200 mK |
| G    | 2025-11-19 01:01:22 |  5862 mK |
| G    | 2025-11-19 02:15:06 |    90 mK |
| G    | 2026-01-23 21:28:10 |    95 mK |
| G    | 2026-01-25 16:15:50 |   712 mK |
| G    | 2026-01-30 19:52:12 |   129 mK |

### Past Announcements

* 2025 August: [26A Stability Announcement](KPF Stability Statement - August 15 2025.pdf)
* 2023 September: [Keck Science Meeting presentation](Keck Science Meeting 2023 Breakout Session.pdf)
