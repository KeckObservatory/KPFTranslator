# Tip Tilt Correction System

The KPF tip tilt system takes fast (e.g. 100 FPS) subframe images from the KPF [CRED2 guide camera](guider.md) in order to control the fast tip tilt mirror which directs light in to the KPF FIU.  This fast tip tilt system maintains the stellar position on the science fiber.  This is critical not for reasons of maximizing flux in to the spectrograph (though that is a side benefit), but to optimize the radial velocity measurement by keeping the illumination pattern on the fiber tip stable.

Even after fiber scrambling and agitation, if the star’s position on the fiber entrance fiber shifts, that can manifest as a small shift of the spectrum on the detector which would be interpreted as a radial velocity change.  Thus we need to position the star on the fiber, and then hold it in a consistent place during observations and make that position consistent from observation to observation.

The tip tilt mirror is a fold mirror which sits on the PCU stage on the Keck I AO bench.  The mirror folds the light in to the KPF FIU and is controlled in tip and tilt by a piezo stage built by nPoint.  The nominal spec for tip tilt performance is to position of the star within 50mas of the target position and then maintain that position at an RMS fo 50mas or better.

The software which controls the tip tilt stage is built in to the `kpffiu` and `kpfguide` KTL keyword services.
