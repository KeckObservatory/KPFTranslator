# Data Reduction Pipeline

WMKO automatically delivers KPF L0 data products to the Keck Observatory Archive (KOA) for distribution to observers. We plan to distribute L1 and L2 data products as well, but the KPF DRP is still under active development by the KPF science team, so the Keck deployment of the DRP is on hold until there are less frequent changes for us to track.

Observers not affiliated with the KPF build team or with the California Planet Search (CPS) should contact their Staff Astronomer about access to reduced data products.

Advanced users who would like to run the DRP locally can find the [KPF DRP on GitHub](https://github.com/Keck-DataReductionPipelines/KPF-Pipeline) and the documentation can be found on [ReadTheDocs](https://kpf-pipeline.readthedocs.io/en/latest).

## Level Definitions

| Level | Description |
| ----- | ----------- |
| L0 | Raw spectra packaged with other instrument data<br>(see [Data Format](dataflow.md) for details) |
| L1 | 1-d, wavelength calibrated spectra |
| L2 | RVs, multiple activity indicators |