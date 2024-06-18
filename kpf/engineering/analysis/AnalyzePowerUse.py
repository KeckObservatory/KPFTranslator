#!python3

## Import General Tools
from pathlib import Path
import time
from datetime import datetime, timedelta

import numpy as np

import keygrabber



def get_power_telemetry(date, outlets):

    dt = datetime.strptime(date, '%Y-%m-%d')
    oneday = timedelta(days=1)
    begin  = time.mktime(dt.timetuple())
    end = time.mktime((dt+oneday).timetuple())

    power_history = keygrabber.retrieve({'kpfpower': outlets}, begin=begin, end=end)

#     for entry in power_history:
#         entry_dt = datetime.fromtimestamp(entry['time'])
#         entry_delta = (entry_dt - dt).total_seconds()
#         if entry_delta > 60*60*24:
#             print(entry_dt)

    return power_history


def analyze_power_use(power_history):
    power_data = {}
    avg_draw = {}
    max_draw = {}
    for entry in power_history:
        if entry['keyword'] not in power_data.keys():
            power_data[entry['keyword']] = []
        power_data[entry['keyword']].append(float(entry['binvalue']))

    total_avg = 0
    total_max = 0
    for outlet in power_data.keys():
        avg_draw[outlet] = np.mean(power_data[outlet])
        max_draw[outlet] = max(power_data[outlet])
        total_avg += avg_draw[outlet]
        total_max += max_draw[outlet]

    # Which outlets have the highest avg draw?
    threshold = 100
    worst_offenders = {}
    for outlet in power_data.keys():
        if avg_draw[outlet] > threshold:
            worst_offenders[outlet] = avg_draw[outlet]

    return total_avg, total_max, worst_offenders


def main(date):
    power_strips = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M']
    outlets = []
    for power_strip in power_strips:
        for i in [1, 2, 3, 4, 5, 6, 7, 8]:
            outlets.append(f'OUTLET_{power_strip}{i}_DRAW')
        if power_strip == 'B':
            for i in [9, 10, 11, 12, 13, 14,  15, 16]:
                outlets.append(f'OUTLET_{power_strip}{i}_DRAW')
    
    power_history = get_power_telemetry(date, outlets)
    total_avg, total_max, worst_offenders = analyze_power_use(power_history)
    print(total_avg, total_max)
    print(worst_offenders)


if __name__ == '__main__':
    ##-------------------------------------------------------------------------
    ## Parse Command Line Arguments
    ##-------------------------------------------------------------------------
    ## create a parser object for understanding command-line arguments
    import argparse
    p = argparse.ArgumentParser(description='''
    ''')
    ## add options
    p.add_argument("--date", dest="date", type=str,
        default='2024-01-01',
        help="The date to analyze (in YYYY-mm-dd format).")
    args = p.parse_args()

    main(args.date)
