# Afternoon Setup

The afternoon setup process for the instrument itself is minimal. Calibrations are automated, so unless you have very special requirements for your observation (if so please contact the Staff Astronomer supporting your night in advance), then observers will not need to execute any calibrations.

Prior to starting observing, observers should run: `KPF Control Menu --> Start KPF GUIs` from the background menu (or `kpfStartUp` from the command line on any KPF machine). This will:

 * Configure the output directories
 * Set the observer names based on the telescope schedule
 * Start the KPF GUIs

This can be run at any time prior to observing. If automated calibrations are in progress, this may take several minutes as certain operations can only be done while the detectors are not exposing.

Observers should use the afternoon to [prepare Observing Blocks (OBs)](preparingOBs.md) and their star list if they have not done so already. 

# Start of Night

KPF does, however, need to be configured properly at the start of the night. There is a procedure which should be run **only after the Observing Assistant (OA) has selected KPF as the instrument** and **after automated afternoon calibrations are complete.**  It is important that this not be run while other instruments are observing. To configure KPF for observing, run `KPF Control Menu --> Run Start of Night Script` from the background menu (or `kpfStartOfNight` from the command line on any KPF machine). This will:

* Disable automated calibrations
* Configure the FIU to the observing mode
* Open the science and sky source select shutters
* Configure the AO Bench. Including positioning the PCU stage and opening the AO hatch.
* Configure DCS for KPF by setting dcs.ROTDEST=0 and dcs.ROTMODE=stationary
* Confgure the tip tilt loop gain to its default setting
