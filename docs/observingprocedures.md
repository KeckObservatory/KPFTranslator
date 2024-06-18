# Quick Reference

- [Wait for Dome to Open](#wait-for-dome-to-open)
- [Run Start of Night](#run-start-of-night)
- [Slew to the Vicinity of Your First Target](#slew-to-the-vicinity-of-your-first-target)
- [Focus the Telescope](#focus-the-telescope)
- [Execute OBs](#execute-obs)
- [Switching Programs on a Split Night](#switching-programs-on-a-split-night)

# Wait for Dome to Open

The Observing Assistant (OA) is not permitted to open the dome until after sunset. Please be patient while the shutter opens and the OA checks the initial telescope pointing. 

# Run Start of Night

To configure KPF for observing, run `KPF Control Menu --> Run Start of Night Script` from the background menu (or `kpfStartOfNight` from the command line on any KPF machine). This will

- Disable automated calibrations
- Configure the FIU to the observing mode
- Open the science and sky source select shutters
- Configure the AO Bench. Including positioning the PCU stage and opening the AO hatch.
- Configure DCS for KPF by setting dcs.ROTDEST=0 and dcs.ROTMODE=stationary
- Confgure the tip tilt loop gain to its default setting
- Set data output directory
- Set observers from telescope schedule

# Slew to the Vicinity of Your First Target

When ready to move the telescope, the OA will ask you for your first target and load the coordinates from your starlist file. They will select a bright star near your target and will attempt to acquire that in the guider, then will double-check the accuracy of pointing by acquiring one or two additional stars from the SAO or GSC catalogs.

To monitor the guider images, run `Telescope GUIs --> MAGIQ Guider UI` from the background menu.

# Focus the Telescope

The OA will run the telescope focus procedure (Autofoc) near your science field. On some nights, they will opt for the Mira focus procedure which takes slightly longer but is needed to calibrate the secondary mirror tilt.

# Execute OBs

Observers can load previously saved OBs or create them on the fly for KPF observing. To load and execute a saved OB:

- Click Load OB from File
- Select a desired OB from the file list
- Click Execute This OB or Execute OB with Slew Cal

The GUI will first prompt the observers to conform the OB execution. Once confirmed, an xterm will launch and prompt the observers with addtional information if needed.

Executing the OB will not start an exposure immediately. The system will first configure the instrument and will then prompt the observer to confirm once the OA has acquired the target. While configuring the instrument, the OB will set the gain and frames per second on the guider based on the target information (J magnitude).  Because of this, **it is important to execute the OB during the slew** and before the OA acquires the target, so that the guider exposure parameters are not changed while the OA is working to acquire the target.

The log lines which show up in the xterm with the running OB contain useful information.  In general, lines with INFO are attempting to explain what the instrument is doing.  Lines with WARNING are indicating that a minor problem has occurred, but the system is handling it.  The WARNING lines are purely informational, no action is needed on the part of the observer in response.  Lines with ERROR indicate a serious problems which may require user intervention.

## Stopping Scripts or Exposures

**Important**: If you wish to halt an OB durin execution, do **NOT** hit Control-c in the terminal.  Use the "Request Script STOP" button instead. The KPF scripts have checkpoints in them which are places where the script can cleanly exit and perform important cleanup operations.  The "STOP Exposure and Script" button does the same thing, but it will also terminate an exposure in progress.

# Switching Programs on a Split Night

On a KPF/KPF split night, before starting the second KPF program, run `KPF Control Menu --> Set Program ID and Observers` from the background menu (or `kpfSetObserverFromSchedule` from the command line on any KPF machine). Enter the program ID at the terminal prompt. The script will then set program ID and observers for the second KPF program, based on the telescope schedule.

