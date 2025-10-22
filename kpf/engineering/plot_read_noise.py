#!python3

## Import General Tools
from pathlib import Path
import argparse
import datetime
import re

import numpy as np
from astropy.io import fits
import matplotlib.pylab as plt


##-------------------------------------------------------------------------
## Parse Command Line Arguments
##-------------------------------------------------------------------------
## create a parser object for understanding command-line arguments
p = argparse.ArgumentParser(description='''Plot the read noise over time from
the input FITS files.

This was designed to work on the FITS files produced by archonGUI (see
https://keckobservatory.atlassian.net/wiki/x/AYAnk) and is not tested on files
from the main KPF data taking system (e.g. the KTL keywords). The file names
are assumed to match a particular pattern:
* start with either G or R to indicate whether it is the green or red side
* include a description in the middle offset by underscores (`_`).
* include pixel dimension (e.g. `_4188x4110`, the default from ArchonGUI).
* end in the frame number (again the default from ArchonGUI)
''')
p.add_argument('files', nargs='*',
               help="The files to process")
args = p.parse_args()


##-------------------------------------------------------------------------
## Main Program
##-------------------------------------------------------------------------
def main():
    # Parse files
    fileinfo = {}
    for file in args.files:
        fnmatch = re.match('([GR])[a-zA-Z]*_(.*)_4188x4110_(\d+)\.(\w+)', Path(file).name)
        if fnmatch:
            timestamp = datetime.datetime.fromtimestamp(Path(file).stat().st_mtime)
            fileinfo[file] = {'det': fnmatch.group(1),
                              'label': fnmatch.group(2),
                              'frameno': int(fnmatch.group(3)),
                              'ext': fnmatch.group(4),
                              'timestamp': timestamp,
                              'timestr': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                              }
        else:
            print(f'Failed to parse filename: {Path(file).name}')

    # Iterate over FITS files and calculate read noise
    for file in fileinfo.keys():
        if fileinfo[file]['ext'] == 'fits':
            hdul = fits.open(file)
            gain = 5     # approx 5 to convert to electrons, good enough for this analysis
            image = gain * hdul[0].data/(2**16) #convert to e-
            # measure read noise
            fileinfo[file]['rn_e'] = np.std(image[4:1004,4:1004].flatten())
            fileinfo[file]['rn_oscan'] = np.std(image[:,4:5].flatten())

    sortedfiles = sorted(fileinfo, key=lambda file: fileinfo[file]['timestamp'])
    greenfiles = [file for file in sortedfiles if fileinfo[file]['det'] == 'G' and fileinfo[file]['ext'] == 'fits']
    redfiles = [file for file in sortedfiles if fileinfo[file]['det'] == 'R' and fileinfo[file]['ext'] == 'fits']

    # Plot read noise from FITS files
    plt.figure(figsize=(12,8))

    print('# Green Noise Measurements')
    G_offset = 0.5
    plt.subplot(2,1,1)
    G_RN = [fileinfo[file]['rn_e'] for file in greenfiles]
    G_RNos = [fileinfo[file]['rn_oscan'] for file in greenfiles]
    G_timestamp = [fileinfo[file]['timestamp'] for file in greenfiles]
    G_label = [fileinfo[file]['label'] for file in greenfiles]
    G_frameno = [fileinfo[file]['frameno'] for file in greenfiles]
    plt.plot(G_RN, 'go')
    plt.plot(G_RNos, 'go', alpha=0.5)
    for i,file in enumerate(greenfiles):
        print(f"{fileinfo[file]['timestr']} {file:50s}: {fileinfo[file]['rn_e']:5.2f} {fileinfo[file]['rn_oscan']:5.2f}")
        plt.text(i, max([fileinfo[file]['rn_e'], fileinfo[file]['rn_e']])+G_offset, G_label[i],
                 rotation='vertical')
    plt.ylabel('Read Noise (e-)')
#     plt.ylim(min(G_RN)*0.98, max(G_RN)*1.05)
    plt.ylim(3.5, max(G_RN)+3)
    plt.xticks(range(len(G_frameno)), G_frameno)
    plt.grid()

    print('# Red Noise Measurements')
    R_offset = 0.1
    plt.subplot(2,1,2)
    R_RN = [fileinfo[file]['rn_e'] for file in redfiles]
    R_RNos = [fileinfo[file]['rn_oscan'] for file in redfiles]
    R_timestamp = [fileinfo[file]['timestamp'] for file in redfiles]
    R_label = [fileinfo[file]['label'] for file in redfiles]
    R_frameno = [fileinfo[file]['frameno'] for file in redfiles]
    plt.plot(R_RN, 'ro')
    plt.plot(R_RNos, 'ro', alpha=0.5)
    for i,file in enumerate(redfiles):
        print(f"{fileinfo[file]['timestr']} {file:50s}: {fileinfo[file]['rn_e']:5.2f} {fileinfo[file]['rn_oscan']:5.2f}")
        plt.text(i, fileinfo[file]['rn_e']+R_offset, R_label[i],
                 rotation='vertical')
    plt.ylabel('Read Noise (e-)')
#     plt.ylim(min(R_RN)*0.98, max(R_RN)*1.05)
    plt.ylim(1.5, max(R_RN)+1)
    plt.xlabel('Frame Number')
    plt.xticks(range(len(R_frameno)), R_frameno)
    plt.grid()

    plt.savefig('ReadNoise.png', bbox_inches='tight', pad_inches=0.1)
    plt.show()


if __name__ == '__main__':
    main()
