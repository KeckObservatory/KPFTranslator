#!python3

## Import General Tools
import sys
import copy
import time
from datetime import datetime, timedelta
from matplotlib import pyplot as plt
import numpy as np
from scipy.signal import find_peaks
from astropy.table import Table

import keygrabber


def retrieve_basement_temperatures(start='2026-01-01', end='2026-02-01'):

    start_date = datetime.strptime(start, '%Y-%m-%d')
    begin  = time.mktime(start_date.timetuple())
    end_date = datetime.strptime(end, '%Y-%m-%d')
    end = time.mktime(end_date.timetuple())

#     start_date = datetime.strptime('2025-11-09 05:00:00', '%Y-%m-%d %H:%M:%S')
#     begin  = time.mktime(start_date.timetuple())
#     end_date = datetime.strptime('2025-11-10 08:00:00', '%Y-%m-%d %H:%M:%S')
#     end  = time.mktime(end_date.timetuple())

    keywords = {f'kpfmet': ['TEMP', 'ETALON_AMBIENT', 'CAL_BENCH_BOT',
                            'ENCLOSURE_FRONT', 'ENCLOSURE_TOP']}
    temp_history = keygrabber.retrieve(keywords, begin=begin, end=end)

    data = {}
    for kw in keywords['kpfmet']:
        data[f'{kw} value'] = []
        data[f'{kw} times'] = []
    for entry in temp_history:
        kw = entry['keyword']
        value = float(entry['binvalue'])
        timestamp = datetime.fromtimestamp(entry['time'])
        if value > -10 and value < 50:
            data[f'{kw} value'].append(value)
            data[f'{kw} times'].append(timestamp)

    return data, keywords['kpfmet']


def plot_basement_temperatures(data, kws, start=None, end=None):
    if start and end:
        start_date = datetime.strptime(start, '%Y-%m-%d')
        end_date = datetime.strptime(end, '%Y-%m-%d')

    # Plot the results to visualize
    plt.figure(figsize=(14, 8))

    plt.subplot(2,1,1)
    plt.title('Basement Temperatures')
    for kw in kws:
        plt.plot(data[f'{kw} times'], data[f'{kw} value'], marker=',', label=kw)
    plt.ylabel('Temperature (C)')
    plt.grid()
    plt.legend(loc='best')
    plt.ylim(17.5,27.5)
    if start and end:
        plt.xlim(start_date, end_date)

    plt.subplot(2,1,2)
    minmax = [0, 0]
    for kw in kws:
        mint = min(data[f'{kw} value']-np.median(data[f'{kw} value']))
        maxt = max(data[f'{kw} value']-np.median(data[f'{kw} value']))
        plt.plot(data[f'{kw} times'], data[f'{kw} value']-np.median(data[f'{kw} value']),
                 marker=',', label=kw, alpha=0.3)
        if mint < minmax[0]: minmax[0] = np.floor(mint*4)/4
        if maxt > minmax[1]: minmax[1] = np.ceil(maxt*4)/4
    plt.ylabel('Temperature Changes (C)')
    plt.grid()
    plt.legend(loc='best')
    plt.ylim(*minmax)
    if start and end:
        plt.xlim(start_date, end_date)

    plt.xlabel('Time')
    plt.show()


if __name__ == '__main__':
    start = '2025-11-01'
    end = '2026-03-01'
    data, kws = retrieve_basement_temperatures(start=start, end=end)
    plot_basement_temperatures(data, kws, start=start, end=end)
