# KPF Computers

`kpf` (aka `vm-kpf`) is a virtual machine at the summit.  It runs the VNC sessions which observers use to interact with the instrument and runs most of the GUIs in those VNCs.

`kpfserver` is the instrument host on which most of the critical dispatchers and keyword services run.

`kpffiuserver` performs a similar function to `kpfserver` for the FIU and Ca H&K spectrometer in the (physically-separated) AO room.  

`kpfbuild` is the build host where files are installed and built. When ready they are deployed using a script to each of the run hosts (`kpfserver`, `kpffiuserver`, and `kpf`).   

`kpfetalon` is a machine in the basement which handles telemetry from the Etalon thermal controllers and sensors.

`tc-su-kpfetalon` is a small windows machine connected to the NKT SuperK light source for the etalon.  It is used when we need to run the NKT software to start up the light source.

# Data Storage

Most KPF data is stored on `/sdata1701` on `kpfserver` which other computers a WMKO cross-mount as `/s/sdata1701`.  Subdirectories within `/sdata1701` are for the assigned account, e.g. `kpfeng` or `kpf1`.  Then there are date-coded directories, which correspond to the date of the start of the night (i.e. `2024jun21` is the night of June 21 Hawaii time, but data taken during the second half will be written there even though it is technically June 22 at the moment the data is taken). The date directories change at 2pm HST.  An example data directory is `/s/sdata1701/kpfeng/2023jul11`.

# Network

KPF is controlled by computers and devices that are behind the WMKO firewall.  Most KPF devices (e.g., vacuum controllers) are on a private network behind kpfserver, which has separate network cards for the WMKO network and the private KPF network.
