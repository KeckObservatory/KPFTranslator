# Examine Slowdown Factors

The nominal zero points we have determined are effectively simple ETCs for each wavelength as, by definition, the zero point is the magnitude at which you will get a flux of 1 per second of whatever flux units you used to calculate the zero point.  In our case, this is detected photons per pixel for the spectrograph and total ADU in the wavelength bin for the Exposure Meter.

Because these zero points represent nominal conditions, we can use the comparison of the ETC predictions to the actual measured flux to measure the slowdown factor which is of interest to KPF-CC scheduling.


```python
from pathlib import Path
import yaml
import numpy as np
from astropy import stats
from astropy.time import Time
from astropy.table import Table, MaskedColumn
from kpf_etc.etc import kpf_photon_noise_estimate

import matplotlib.pyplot as plt

data_file = 'data/Feb2026_withInstZPs.csv'
t = Table.read(data_file, format='ascii.csv')
```


```python
EMZPfile = Path('data/ExposureMeterZeroPoints.yaml')
with open(EMZPfile, 'r') as f:
    EMZeroPoint = yaml.safe_load(f)
EMZeroPoint
```




    {1: 21.296861833059204,
     2: 21.802875631774594,
     3: 21.73859924329517,
     4: 21.385171098414354,
     'SUM': 23.06521519492087}




```python
ZPfile = Path('data/InstrumentZeroPoints.yaml')
with open(ZPfile, 'r') as f:
    ZeroPoint = yaml.safe_load(f)
ZeroPoint
```




    {'452': 13.664362089856091,
     '548': 14.964690898633878,
     '652': 15.329155098901115,
     '747': 15.466755734095996,
     '852': 15.073233551565435}




```python
EMbinfile = Path('data/ExpMeterBins.yaml')
with open(EMbinfile, 'r') as f:
    best_EMbin = yaml.safe_load(f)
best_EMbin
```




    {'452': 1, '548': 2, '652': 3, '747': 4, '852': 4}




```python
wavs = ZeroPoint.keys()
EMbins = EMZeroPoint.keys()
```

# Use "Nominal" Zero Point Value as an ETC


```python
def ZPETC(Gmag, exptime, wav='652', EMbin=2):
    assert wav in ZeroPoint.keys()
    assert EMbin in EMZeroPoint.keys()
    photons = float(exptime*10**((Gmag - ZeroPoint[wav])/-2.5))
    EM_ADU = float(exptime*10**((Gmag - EMZeroPoint[EMbin])/-2.5))
    return photons, EM_ADU


def EMThreshold(photons, wav='652', EMbin=2):
    assert wav in ZeroPoint.keys()
    assert EMbin in EMZeroPoint.keys()
    ZPdiff = ZeroPoint[wav] - EMZeroPoint[EMbin]
    EM_ADU = photons*10**(-ZPdiff/2.5)
    return EM_ADU
```


```python
# Double Check Consistency
photons, EMADU = ZPETC(10, 60, wav='747', EMbin=2)
EMADU2 = EMThreshold(photons, wav='747', EMbin=2)
EMADU2/EMADU
```




    1.0



## Add Zero Point ETC results to table for both instrument and exposure meter


```python
for wav in wavs:
    t.add_column(MaskedColumn(t['ELAPSED']*10**((t['GAIAMAG'] - ZeroPoint[wav])/-2.5), name=f'ZP-etc-{wav}'))
    t[f'ZP-etc-{wav}'].mask = t[f'ZP-etc-{wav}'].mask | (t[f'ZP-etc-{wav}'] <= 0)
    slowdown = t[f'ZP-etc-{wav}']/t[f'SNRSC{wav}']**2
    t.add_column(MaskedColumn(slowdown, name=f'SD-ZP-etc-{wav}'))
    t[f'SD-ZP-etc-{wav}'].mask = t[f'SD-ZP-etc-{wav}'].mask | t[f'ZP-etc-{wav}'].mask | (t[f'SD-ZP-etc-{wav}'] > 10)
```


```python
for EMbin in EMbins:
    t.add_column(MaskedColumn(t['ELAPSED']*10**((t['GAIAMAG'] - EMZeroPoint[EMbin])/-2.5), name=f'ZP-etc-EM{EMbin}'))
    t[f'ZP-etc-EM{EMbin}'].mask = t[f'ZP-etc-EM{EMbin}'].mask | (t[f'ZP-etc-EM{EMbin}'] <= 0)
    slowdown = t[f'ZP-etc-EM{EMbin}']/t[f'TOTCORR_{EMbin}']
    t.add_column(MaskedColumn(slowdown, name=f'SD-ZP-etc-EM{EMbin}'))
    t[f'SD-ZP-etc-EM{EMbin}'].mask = t[f'SD-ZP-etc-EM{EMbin}'].mask | t[f'ZP-etc-EM{EMbin}'].mask | (t[f'SD-ZP-etc-EM{EMbin}'] > 10)
```

## Add in results of formal KPF-etc


```python
def read_GminusV_table():
    '''Table of data from:
    https://www.pas.rochester.edu/~emamajek/EEM_dwarf_UBVIJHK_colors_Teff.txt
    '''
    table_file = Path('data/EEM_dwarf_UBVIJHK_colors_Teff.txt')
    if table_file.exists() is False:
        return 0
    t = Table.read(table_file, format='ascii')
    filtered = t[t['G-V'] != '...']
    return filtered

filtered = read_GminusV_table()

def get_GminusV(Teff):
    Teff_diff = abs(filtered['Teff'] - Teff)
    ind = np.argmin(Teff_diff)
    GminusV = float(filtered[ind]['G-V'])
    return GminusV

def Vmag(Gmag, Teff):
    return Gmag - get_GminusV(Teff)
```


```python
# Add Vmag as column
vmag_data = [Vmag(row['GAIAMAG'], row['TARGTEFF']) for row in t]
t.add_column(MaskedColumn(vmag_data, name=f'VMAG'))
```


```python
# Add ETC results as columns
order = {'452': 2,
         '548': 25,
         '652': 43,
         '747': 55,
         '852': 65}
ETCflux = {'452': [],
           '548': [],
           '652': [],
           '747': [],
           '852': []}
ETC_SD = {'452': [],
          '548': [],
          '652': [],
          '747': [],
          '852': []}

ETCvalid = (t['TARGTEFF'] >= 2700) & (t['TARGTEFF'] <= 6600) & (t['ELAPSED'] > 10) & (t['ELAPSED'] <= 3600)
for i,row in enumerate(t):
    # KPF-etc
    if ETCvalid[i] == True:
        try:
            a, b, snr_ord, c = kpf_photon_noise_estimate(row['TARGTEFF'], row['VMAG'], row['ELAPSED'], quiet=True)
            for wav in wavs:
                predicted_flux = float(snr_ord[order[wav]]**2)
                ETCflux[wav].append(predicted_flux)
                slowdown = predicted_flux/float(row[f'SNRSC{wav}']**2)
                ETC_SD[wav].append(slowdown)
        except Exception as e:
            print(e, row['TARGTEFF'], row['VMAG'], row['ELAPSED'])
            for wav in wavs:
                ETCflux[wav].append(0)
                ETC_SD[wav].append(0)
    else:
        for wav in wavs:
            ETCflux[wav].append(0)
            ETC_SD[wav].append(0)

for wav in wavs:
    t.add_column(MaskedColumn(ETCflux[wav], name=f'KPF-etc-{wav}'))
    t[f'KPF-etc-{wav}'].mask = (t[f'KPF-etc-{wav}'] <= 0)
    t.add_column(MaskedColumn(ETC_SD[wav], name=f'SD-KPF-etc-{wav}'))
    t[f'SD-KPF-etc-{wav}'].mask = (t[f'SD-KPF-etc-{wav}'] <= 0) | (t[f'SD-KPF-etc-{wav}'] > 10)

```

    /var/folders/3m/rvt2qsdx3nv0cv6m5rvbbgzc0000gp/T/ipykernel_69776/848789479.py:27: UserWarning: Warning: converting a masked element to nan.
      slowdown = predicted_flux/float(row[f'SNRSC{wav}']**2)


# Slowdown Factor

How well does the nominal flux estimate from our Zero Point based ETC predict the actual/measured flux in the data set?  To examine this, we look at the slowdown factor which is the ratio of the flux expected versus the flux measured.  The slowdown can be calculated for the instrument flux and for the Exposure Meter flux, so we want to see how well the Exposure Meter slowdown predicts the spectrograph slowdown.

During night observations, the Exposure Meter slowdown factor could be calculated in real time, but the spectrograph slowdown factor will only be available once the DRP has run and provided the `SNRSC*` keyword values.

We can use either the Zero Point ETC or the formal KPF-etc (when the target is within its input ranges) to calculate a slowdown factor for the spectrograph, so we will examine both.


```python
def plot_one_slowdown(slowdowns, bins=np.arange(0,10+0.05,0.05), color='b', label='Spectrograph'):
    plt.hist(slowdowns, bins=bins, density=True, color=color, label=label)
    n, binedges = np.histogram(slowdowns, bins=[0,1,2,4,1e6])
    d = [float(val/np.sum(n)) for val in n]   
    plt.axvspan(0, 1, color='k', alpha=0.01, label=f'band0 {d[0]:.1%}')
    plt.axvspan(1, 2, color='g', alpha=0.2, label=f'band1 {d[1]:.1%}')
    plt.axvspan(2, 4, color='y', alpha=0.2, label=f'band2 {d[2]:.1%}')
    plt.axvspan(4, 10, color='r', alpha=0.1, label=f'band3 {d[3]:.1%}')
    plt.grid()
    plt.legend(loc='best')
    plt.ylabel(f'Density')
    return d


def plot_slowdowns(t, wav):
    EMbin = best_EMbin[wav]
    bins = np.arange(0,10+0.05,0.05)
    
    plt.figure(figsize=(10,6))
    
    plt.subplot(3,1,1)
    ZPETCslowdowns = t[f'SD-ZP-etc-{wav}'][~t[f'SD-ZP-etc-{wav}'].mask]
    plt.title(f'Instrument Slowdowns Calculated at {wav} nm')
    d = plot_one_slowdown(ZPETCslowdowns, bins=bins, color='b', label='Spectrograph')
    
    plt.subplot(3,1,2)
    EM_ZPETCslowdowns = t[f'SD-ZP-etc-EM{EMbin}'][~t[f'SD-ZP-etc-EM{EMbin}'].mask]
    plot_one_slowdown(EM_ZPETCslowdowns, bins=bins, color='g', label='ExpMeter')
       
    plt.subplot(3,1,3)
    KPFETCslowdowns = t[f'SD-KPF-etc-{wav}'][~t[f'SD-KPF-etc-{wav}'].mask]
    plot_one_slowdown(KPFETCslowdowns, bins=bins, color='c', label='KPF-etc')
    plt.xlabel('Slowdown Factor')
    
    plt.show()
    return d
```


```python
distribution = {}
for wav in wavs:
    distribution[wav] = plot_slowdowns(t, wav)
```


    
![png](output_18_0.png)
    



    
![png](output_18_1.png)
    



    
![png](output_18_2.png)
    



    
![png](output_18_3.png)
    



    
![png](output_18_4.png)
    


### Discussion: Spectrograph and Exposure Meter Slowdowns

We see that the slowdown factors for both the instrument and the exposure meter are typically >1.  This is to be expected as our nominal zero points are the 90th percentile of good data, so the Zero Point ETC assumes very good conditions, thus most data are taken in somewhat worse conditions.  The distribution of slowdowns is what we'd expect given the distribution of Zero Points we measured before.

We have highlighted the weather bands as defined by their slowdown rate and put the percentage of observations in each band in the legend.  The majority of observations take place in band1 as we would expect.  The "band0" designation is for observations with a slowdown of <1 which should probably be considered part of band1, but is nominally out of the definied range.  For the spectrograph and exposure meter, the occurance rate of band0 is ~10% which is reasonable based our use of the 90th percentile to define "nominal" which would correspond to a slowdown factor of 1.0.

Comparing the distribution of exposure meter slowdowns to instrument slow downs, we see that the exposure meter is typically a bit optimistic relative to the instrument by 10-15%, so the actual slowdown is a bit worse than one estimated in real time by the Exposure Meter.

### Discussion: KPF-etc Calculated Slowdowns

For all wavelengths other than 452nm, under good conditions, the formal KPF-etc underestimates the flux relative to what is actually observed leading to a "slowdown" of less than 1, putting most of the observations in "band0".

## How Much Time is Spent in Each Weather Band?

The above distribution of weather bands is a count of exposures, not a total time.  To get that we need to sum up the elapsed exposure time in each band.


```python
def time_in_each_band(wav='652', etc='ZP-etc-'):
    band0 = t[(t[f'SD-{etc}{wav}'] < 1)]
    band1 = t[(t[f'SD-{etc}{wav}'] >= 1) & (t[f'SD-{etc}{wav}'] < 2)]
    band2 = t[(t[f'SD-{etc}{wav}'] >= 2) & (t[f'SD-{etc}{wav}'] < 4)]
    band3 = t[(t[f'SD-{etc}{wav}'] >= 4)]
    elapsed0 = float(np.sum(band0[~band0[f'SD-{etc}{wav}'].mask]['ELAPSED']))
    elapsed1 = float(np.sum(band1[~band1[f'SD-{etc}{wav}'].mask]['ELAPSED']))
    elapsed2 = float(np.sum(band2[~band2[f'SD-{etc}{wav}'].mask]['ELAPSED']))
    elapsed3 = float(np.sum(band3[~band3[f'SD-{etc}{wav}'].mask]['ELAPSED']))
    total_elapsed = elapsed0+elapsed1+elapsed2+elapsed3
    # print(f"Time in Each Band at {wav}")
    # print(f"  band0: {elapsed0/total_elapsed:.1%}")
    # print(f"  band1: {elapsed1/total_elapsed:.1%}")
    # print(f"  band2: {elapsed2/total_elapsed:.1%}")
    # print(f"  band3: {elapsed3/total_elapsed:.1%}")
    return [elapsed0/total_elapsed, elapsed1/total_elapsed, elapsed2/total_elapsed, elapsed3/total_elapsed]
```


```python
duration = {}
for wav in wavs:
    duration[wav] = time_in_each_band(wav=wav)
```


```python
plt.figure(figsize=(8,6))

plt.subplot(2,1,1)
for i,wav in enumerate(wavs):
    c = ['b', 'c', 'g', 'r', 'k'][i]
    plt.bar(np.array([0, 1, 2, 3])+0.15*(i-2), distribution[wav], color=c, alpha=0.3, width=0.15, label=f"{wav}nm")
plt.gca().set_xticks([0, 1, 2, 3])
plt.gca().set_xticklabels(['band0', 'band1', 'band2', 'band3'])
plt.grid()
plt.legend(loc='best')
plt.ylabel('Fraction of Exposures')

plt.subplot(2,1,2)
for i,wav in enumerate(wavs):
    c = ['b', 'c', 'g', 'r', 'k'][i]
    plt.bar(np.array([0, 1, 2, 3])+0.15*(i-2), duration[wav], color=c, alpha=0.3, width=0.15, label=f"{wav}nm")
plt.gca().set_xticks([0, 1, 2, 3])
plt.gca().set_xticklabels(['band0', 'band1', 'band2', 'band3'])
plt.grid()
plt.legend(loc='best')
plt.ylabel('Fraction of Time')


plt.show()
```


    
![png](output_23_0.png)
    


# Look at Ratio of Actual Slowdown (from Spectrograph ZPETC) versus Exposure Meter


```python
plt.figure(figsize=(10,8))
for i,wav in enumerate(wavs):
    plt.subplot(5,1,i+1)
    EMbin = best_EMbin[wav]
    if i==0: plt.title(f"Ratio of actual slowdown to exposure meter slowdown")
    ratio = t[f'SD-ZP-etc-{wav}']/t[f'SD-ZP-etc-EM{EMbin}']
    mask = t[f'SD-ZP-etc-{wav}'].mask | t[f'SD-ZP-etc-EM{EMbin}'].mask
    bins=np.arange(0,max(ratio[~mask]),0.02)
    plt.hist(ratio[~mask], bins=bins, density=True, label=f'{wav}nm')
    plt.axvline(1.0, color='k')
    plt.legend(loc='best')
    plt.xlim(0.5,2.5)
    plt.ylabel('Density')
    plt.grid()
plt.xlabel('Slowdown Ratio: ETC Slowdown / ExpMeter Slowdown')
plt.show()
```


    
![png](output_25_0.png)
    


### Discussion: Exposure Meter Slowdowns

Comparing exposure meter slowdown measures with the spectrograph, we can see a bias of ~5-15% toward the exposure meter underestimating the slowdown.  The real slowdown is larger than what you would get from the exposure meter at the end of the exposure.

# Save Results to Disk


```python
t.write('data/Feb2026_withETCs.csv', overwrite=True)
```
