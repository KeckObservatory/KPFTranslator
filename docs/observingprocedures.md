# Quick Reference

- [Beginning of the Night](#beginning-of-the-night)
- [Performing Observations](#performing-observations)
- [Switching Programs on a Split Night](#switching-programs-on-a-split-night)
- [Bad Weather](#bad-weather)

# Beginning of the Night

### Wait for Dome to Open

The Observing Assistant (OA) is not permitted to open the dome until after sunset. Please be patient while the shutter opens and the OA checks the initial telescope pointing. 

### Run Start of Night

KPF needs to be configured properly at the start of the night. There is a procedure which should be run **only after the Observing Assistant (OA) has selected KPF as the instrument** and **after automated afternoon calibrations are complete.**  The selected instrument ("INST") can be seen in the lower left corner of the [FACSUM window](figures/FACSUM.png).

It is important that this not be run while other instruments are observing. To configure KPF for observing, run `KPF Control Menu --> Run Start of Night Script` from the background menu (or `kpfStartOfNight` from the command line on any KPF machine). This will:

- Disable automated calibrations
- Configure the FIU to the observing mode
- Open the science and sky source select shutters
- Configure the AO Bench. Including positioning the PCU stage and opening the AO hatch.
- Configure DCS for KPF by setting dcs.ROTDEST=0 and dcs.ROTMODE=stationary
- Configure the tip tilt loop gain to its default setting
- Set data output directory
- Set observers from telescope schedule


### Slew to the Vicinity of Your First Target

When ready to move the telescope, the OA will ask you for your first target and load the coordinates from your starlist file. They will select a bright star near your target and will attempt to acquire that in the guider, then will double-check the accuracy of pointing by acquiring one or two additional stars from the SAO or GSC catalogs.

To monitor the guider images, run `Telescope GUIs --> MAGIQ Guider UI` from the background menu.

### Focus the Telescope

The OA will run the telescope focus procedure (typically Autofoc) near your science field. On some nights, they will opt for the Mira focus procedure which takes slightly longer but is needed to calibrate the secondary mirror tilt.

# Performing Observations

### Highlight Your Target in Magiq

In the Magiq star list (at the bottom of the Magiq User GUI), right click your target and select the option to highlight it for the OA (you can get the same result by middle clicking the target).  This highlighting will show up on the OA's GUI making it easier for them to find the target you want to go to.  Let the OA know to slew to the target when your current exposure is done.

### Execute Your OB

Observers can load previously saved OBs or create them on the fly for KPF observing. To load and execute a saved OB:

- Click Load OB from File
- Select the OB from the file list
- Click Execute This OB (or Execute OB with Slew Cal)

The GUI will first prompt the observers to confirm the OB execution. Once confirmed, an xterm will launch and prompt the observers with addtional information if and when needed, so watch the contents of this xterm.

Executing the OB will not start an exposure immediately. The system will first configure the instrument and will then prompt the observer to confirm once the OA has acquired the target. While configuring the instrument, the OB will provide information on how to set the gain and frames per second on the guider.  Because of this, **it is important to execute the OB during the slew** and before the OA acquires the target, so they have the right exposure parameters to see the target on the guider.

The log lines which show up in the xterm with the running OB contain useful information.  In general, lines with INFO are attempting to explain what the instrument is doing.  Lines with WARNING are indicating that a minor problem has occurred, but the system is handling it -- these lines are purely informational, no action is needed on the part of the observer in response.  Lines with ERROR indicate a serious problems which may require user intervention.

### Slew Cals

KPF has the option of taking a "slew cal" immediately prior to a science observation.  This is a way to make use of the time spent slewing from one target to another.  If an OB is executed with a slew cal (using the "Execute OB with Slew Cal" button in the OB GUI), then the FIU will transition to calibration mode (the FIU hatch will close and calibration light will be directed to the science and sky fibers), and a calibration exposure will be taken.  This will obscure the sky during calibration, so the OA will not be able to see the target until the slew cal is done.  This process takes around 2 minutes and so fits nicely in to long slews.

Because the slew cal happens during the slew to a target, it is optimally performed with a science OB so that the guider can be configured for the science target.  This is another case where executing a science OB before the slew has completed is the most efficient observing strategy.

At the moment, we recommend that slew cals are taken roughly every hour while observing.  This helps track the internal drift of the instrument itself over time scales less than 1 day and can be used by the DRP to further improve RV precision.  The instrument software keeps track of the time since the last relevant calibration and the timer is shown in the upper right of the OB GUI.  The "Time Since Cal" value will color code to orange if it exceeds 1 hour and will become red at 2 hours.  Despite this, **the choice to take slew cals is entirely up to the observer** the timer is only a recommendation.

Slew cals can also be taken independently using the "Execute Slew Cal Only" button.  This is not the intended method for taking slew cals and we recommend using the "Execute OB with Slew Cal" button instead, however the slew cal only option may be useful during periods of bad weather when no observing is happening.

### Stopping Scripts or Exposures

**Important**: If you wish to halt an OB during execution, do **NOT** hit Control-c in the terminal.  Use the "Request Script STOP" button instead. The KPF scripts have checkpoints in them which are places where the script can cleanly exit and perform important cleanup operations.  The "STOP Exposure and Script" button does the same thing, but it will also terminate an exposure in progress.

### Known Issues

There is a known failure mode for KPF called a "start state error".  What happens is some sort of communication failure between the `kpfexpose` control software, the galil hardware which handles the timing and signaling of the detectors and shutters, and the Archon detector controllers.  The result is that one of the green or red detectors does not begin the exposure properly and that detector's data will be useless.  The `kpf.spectrograph.StartExposure` [script](scripts/StartExposure.md) will automatically detect this situation, terminate the bad exposure after a few seconds, and start a new one all without user intervention.  This will generate several WARNING level log messages, but the user does not need to take action as the correction happens automatically.

Another known failure mode which can generate WARNING level log messages is a failure of the FIU to transition in to a new mode (i.e. "Observing" or "Calibration").  The `kpf.fiu.ConfigureFIU` and `kpf.fiu.WaitForConfigureFIU` [scripts](scripts/WaitForConfigureFIU.md) will automatically retry several times before giving up and erroring out.  As with the start state error above, no user action is needed, but you will see WARNING level log messages to let you know what is happening.

# Switching Programs on a Split Night

On a KPF/KPF split night, before starting the second KPF program, run `KPF Control Menu --> Set Program ID and Observers` from the background menu (or `kpfSetObserverFromSchedule` from the command line on any KPF machine). Enter the program ID at the terminal prompt. The script will then set program ID and observers for the second KPF program, based on the telescope schedule.

If you wish to set the observer names and program ID manually (i.e. without querying the telescope schedule), you can use the `kpfSetProgram` and `kpfSetObserver` scripts from the command line.  For example: `kpfSetProgram K123` will set program ID "K123" and `kpfSetObserver "E.E. Barnard, S.W. Burnham"` will set the observer name to "E.E. Barnard, S.W. Burnham".  Note that observer names should be enclosed in quotes to handle spaces in the list of names.

# Bad Weather

If the weather is so bad that no observing is taking place and there doesn't seem to be an immediate likelihood of observing, then we recommend that the observer runs the end of night procedure (`KPF Control Menu --> Run End of Night Script`).  The main advantage of this is that running End of Night will re-enable the automatic scheduled calibrations which happen 4 times per night when KPF is not on sky.  This means that the instrumental drift will be tracked with no action required by the observer (i.e. running slew cals).  If one of these calibration scripts is in progress and observing should resume, use the "Request Script STOP" as described above. After that, run the Start of Night script just as you would at the beginning of the night (among other things it disables the autmatic scheduled calibrations).