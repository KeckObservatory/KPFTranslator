# Instrument Status

### Current Announcements

* 2026 April: [Turbo Pump Failure](announcements/2026-04-06_tubo_failure.md)
* 2026 February: [26A Status Announcement](announcements/2026-02-01_26A-status.md)

<font color="red">KPF is OFFLINE until further notice due to the vacuum pump failure described in the 2026 April announcement above.</font> A Failure Review Board is investigating the root cause of the pump failure and will advise the Observatory on a path forward.  Until that report comes out, the schedule for KPF's return to service is uncertain.


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

| Side  | Duration     | Delta T   | Start (HST)         | End (HST)           |
| ----- | ------------ | --------- | ------------------- | ------------------- |
| Green |   0.05 hours |      7 mK | 2025-11-09 21:22:14 | 2025-11-09 21:25:06 |
| Green |   0.36 hours |    109 mK | 2025-11-10 05:37:12 | 2025-11-10 05:58:50 |
| Green |   2.78 hours |  2,825 mK | 2025-11-10 11:09:06 | 2025-11-10 13:55:54 |
| Green |   0.63 hours |    250 mK | 2025-11-15 11:28:36 | 2025-11-15 12:06:32 |
| Green |   2.54 hours |  5,779 mK | 2025-11-16 14:27:20 | 2025-11-16 16:59:54 |
| Green |   4.04 hours |  6,147 mK | 2025-11-17 07:52:06 | 2025-11-17 11:54:40 |
| Green |   2.31 hours |  4,200 mK | 2025-11-18 03:40:28 | 2025-11-18 05:59:16 |
| Green |   3.14 hours |  5,862 mK | 2025-11-18 23:08:20 | 2025-11-19 02:16:52 |
| Green |   0.56 hours |     95 mK | 2026-01-23 21:12:46 | 2026-01-23 21:46:16 |
| Green |   1.20 hours |    712 mK | 2026-01-25 15:25:34 | 2026-01-25 16:37:48 |
| Green |   0.46 hours |    129 mK | 2026-01-30 19:36:24 | 2026-01-30 20:03:54 |
| Green |  13.82 hours | 53,527 mK | 2026-02-17 21:17:12 | 2026-02-18 11:06:40 |
| Green |   4.48 hours | 11,585 mK | 2026-02-19 02:40:56 | 2026-02-19 07:09:32 |

### Past Announcements

* 2025 August: [26A Stability Announcement](KPF Stability Statement - August 15 2025.pdf)
* 2023 September: [Keck Science Meeting presentation](Keck Science Meeting 2023 Breakout Session.pdf)
