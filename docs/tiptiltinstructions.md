# Tip Tilt Instructions for OAs

## TL:DR Procedure

1. Set the gain and FPS values for the guide camera.
1. Acquire the star to the KPF PO using magiq.
1. In the KPF Tip Tilt GUI, turn on the tip tilt loops.
1. Verify normal operation of the loops (this should just require a momentary glance at the various indicators):
    - Make sure the science target has been indentified.  It should have a circle around it and a label in the image display part of the GUI.
    - Check that an object has been selected in "Object Choice".
    - Check that the Peak Flux is sufficient (the value will be color coded to help you). If needed, adjust the gain and FPS.
    - Check that the Tip Tilt Error is decreasing over time in the plot. This indicates that the star is being moved to the target pixel.
    - Check the "Tip Tilt RMS" value is around 50 mas or better. If the target is faint or there are heavy clouds or bad seeing, it may not be able to reach this, but under normal conditions we should at least be in the ballpark.
    - If there are multiple stars in the field of view, ensure that the corect target is selected and that the stars are not blended (each detected star will have its own OBJECTn label in the image display, make sure this is centered on the star).
1. Inform the observer that the tip tilt loops are engaged and they can being exposing.

### Troubleshooting the TL:DR Procedure

- If the system is not seeing the target star, adjust the "Detect SNR" and/or "Detect Area" values under the Object Detection tab in the GUI (see [Star Detection Algorithm](#star-detection-algorithm) section below for details).
- If the system seems to be having trouble identifying stars, toggle the loops on and off (this is primarily for the Calculation loop). Doing this will cause the algorithm to re-identify the stars and may resolve ID confusion caused when stars are moving rapidly in the field.
- Check that there are no red indicators in the status bar at the bottom of the Tip Tilt GUI.  These indicate that something substantial is wrong.  Which indicator it is will tell you which keyword or dispatcher is in a bad state.

## Tip Tilt System Overview

## Tip Tilt GUI

## Star Detection Algorithm

## Multiple Stars

