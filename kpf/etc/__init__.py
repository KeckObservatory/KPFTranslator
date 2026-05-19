from pathlib import Path
import yaml

'''Data files for the zero points were calculated by examining several years of
DRP outputs.  See analysis in this repo:
https://github.com/joshwalawender/KPF-ZPETC/
or on the KPF web page:
https://www2.keck.hawaii.edu/inst/kpf/sensitivity/
under the "Zero Point Analysis" title.
'''

ZPfile = Path(__file__).parent / 'InstrumentZeroPoints.yaml'
with open(ZPfile, 'r') as f:
    ZeroPoint = yaml.safe_load(f)


EMZPfile = Path(__file__).parent / 'ExposureMeterZeroPoints.yaml'
with open(EMZPfile, 'r') as f:
    EMZeroPoint = yaml.safe_load(f)


EMbinfile = Path(__file__).parent / 'ExpMeterBins.yaml'
with open(EMbinfile, 'r') as f:
    best_EMbin = yaml.safe_load(f)
