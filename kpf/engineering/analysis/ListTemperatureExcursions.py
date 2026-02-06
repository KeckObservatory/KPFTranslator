#!python3

## Import General Tools
import sys
import copy
import time
from datetime import datetime, timedelta
from matplotlib import pyplot as plt
import numpy as np
from scipy.signal import find_peaks

import keygrabber


def find_excursions(side, threshold=0.005, min_duration=1*60*60, set_point=-100,
                    start='2025-11-01'):
    excursion_min_duration = timedelta(hours=1)
    set_point = -100

    start_date = datetime.strptime(start, '%Y-%m-%d')
    begin  = time.mktime(start_date.timetuple())
    end = time.mktime(datetime.now().timetuple())

#     start_date = datetime.strptime('2025-11-09 05:00:00', '%Y-%m-%d %H:%M:%S')
#     begin  = time.mktime(start_date.timetuple())
#     end_date = datetime.strptime('2025-11-10 08:00:00', '%Y-%m-%d %H:%M:%S')
#     end  = time.mktime(end_date.timetuple())

    det_temp_history = keygrabber.retrieve({f'kpf{side.lower()}': ['STA_CCDVAL']},
                                           begin=begin, end=end)
    det_temp = np.array([abs(float(x['binvalue'])-set_point)
                         for x in det_temp_history])
    det_time = np.array([datetime.fromtimestamp(x['time'])
                         for x in det_temp_history])

    # Find local maxima (peaks)
    peaks_indices, _ = find_peaks(det_temp, height=threshold,
                                  distance=1, width=5)

    # Get the actual values of the peaks
    peak_values = det_temp[peaks_indices]
    peak_times = det_time[peaks_indices]


    # Print the indices and values of the peaks
    remove_inds = []
    for i,peak in enumerate(peak_values):
        pt = peak_times[i]
        print(f"{peak_times[i]}: {peak:.3f} K")
        delta_ts = abs(pt-peak_times)
        in_window = delta_ts < excursion_min_duration
        in_window_inds = np.where(in_window)[0]
        windowed_peak_values = copy.deepcopy(peak_values)
        windowed_peak_values[~in_window] = 0
        max_ind = np.argmax(windowed_peak_values)
        not_peak = (in_window_inds != max_ind)
        remove_inds.extend(in_window_inds[not_peak])


    print(f'{side} Final list')
    final_times = []
    final_values = []
    for i,peak in enumerate(peak_values):
        if i not in remove_inds:
            final_times.append(peak_times[i])
            final_values.append(peak_values[i])
            print(f"{peak_times[i]}: {peak*1000:4.0f} mK")

    return det_time, det_temp, final_times, final_values


if __name__ == '__main__':
    Gdet_time, Gdet_temp, Gfinal_times, Gfinal_values = find_excursions('Green')
    Rdet_time, Rdet_temp, Rfinal_times, Rfinal_values = find_excursions('Red')

    # Plot the results to visualize
    plt.figure(figsize=(12, 5))

    plt.subplot(2,1,1)
    plt.title('Detector Temperature Excursions')
    plt.fill_between([min(Gdet_time), max(Gdet_time)], y1=0.0001, y2=0.005, color='g', alpha=0.3)
    plt.plot(Gdet_time, Gdet_temp, 'k-', alpha=0.3, label='Green Temperature')
    plt.scatter(Gfinal_times, Gfinal_values, color='red', marker='x', label='Green Excursions')
    plt.ylim(0.0005, max([0.010, max(Gdet_temp)*2]))
    plt.xlim(min(Gdet_time), max(Gdet_time))
    plt.legend()
    plt.gca().set_yscale('log')
    plt.ylabel('Temperature Delta (K)')

    plt.subplot(2,1,2)
    plt.fill_between([min(Rdet_time), max(Rdet_time)], y1=0.0001, y2=0.005, color='g', alpha=0.3)
    plt.plot(Rdet_time, Rdet_temp, 'k-', alpha=0.3, label='Red Temperature')
    plt.scatter(Rfinal_times, Rfinal_values, color='red', marker='x', label='Red Excursions')
    plt.xlim(min(Rdet_time), max(Rdet_time))
    plt.ylim(0.0005, max([0.010, max(Rdet_temp)*2]))
    plt.legend()
    plt.gca().set_yscale('log')

    plt.xlabel('Time')
    plt.ylabel('Temperature Delta (K)')
    plt.show()
