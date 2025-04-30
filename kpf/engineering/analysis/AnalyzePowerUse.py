#!python3

## Import General Tools
import copy
from pathlib import Path
import time
from datetime import datetime, timedelta
from matplotlib import pyplot as plt
import numpy as np

import keygrabber



def get_power_telemetry(date, outlets):

    dt = datetime.strptime(date, '%Y-%m-%d')
    oneday = timedelta(days=1)
    begin  = time.mktime(dt.timetuple())
    end = time.mktime((dt+oneday).timetuple())

    power_history = keygrabber.retrieve({'kpfpower': outlets}, begin=begin, end=end)
    outlets = [o.replace('_DRAW', '_NAME') for o in outlets]
    outlet_name_history = keygrabber.retrieve({'kpfpower': outlets}, begin=begin, end=end)
    outlet_names = {}
    for i,entry in enumerate(outlet_name_history):
        key = entry['keyword'].replace('_NAME', '_DRAW')
        outlet_names[key] = entry['ascvalue']

    return power_history, outlet_names


def analyze_total_power(date, power_history):
    total_power = []
    total_power_times = []
    total_power_components = []
    Wh = 0

    dto = datetime.strptime(date, '%Y-%m-%d')

    for i,entry in enumerate(power_history):
        time = datetime.fromtimestamp(entry['time'])
        # Build total_power time series of total power use
        if len(total_power_components) > 0:
            newtpdict = copy.deepcopy(total_power_components[-1])
        else:
            newtpdict = {}
        newtpdict[entry['keyword']] = float(entry['binvalue'])
        # Dict of current power values
        tptotal = 0
        for key in newtpdict.keys():
            tptotal += newtpdict[key]
        total_power.append(tptotal)
        total_power_times.append(time)
        total_power_components.append(newtpdict)
        # Wh
        if time > dto and i > 0:
            dt = (time - max([dto, total_power_times[i-1]])).total_seconds()/3600
            Wh += tptotal*dt

    title_str = f'KPF Total Power Use (no LFC)'
    title_str += f'\nEnergy Use on {date} = {Wh/1000.:.2f} kWh'
    title_str += f'\nAverage Power on {date} = {np.mean(total_power)/1000.:.2f} kW'
    title_str += f'\nPeak Power on {date} = {max(total_power)/1000.:.2f} kW'
    print(title_str)
    plt.figure(figsize=(12,8))
    plt.plot(total_power_times, total_power, 'k,')
    plt.title(title_str)
    plt.ylabel('Power (Watt)')
    plt.xlabel('Time')
    plt.xlim(dto, dto+timedelta(days=1))
    plt.ylim(0,1.1*max(total_power))
    plt.grid()
    pngfile = Path(f'~/PowerUse_{date}.png').expanduser()
    print(f'Writing: ~/PowerUse_{date}.png')
    if pngfile.exists(): pngfile.unlink()
    plt.savefig(pngfile, bbox_inches='tight', pad_inches=0.1)


def analyze_outlet_use(power_history):
    power_data = {}
    avg_draw = {}
    max_draw = {}

    for i,entry in enumerate(power_history):
        # Build power_data for each outlet
        if entry['keyword'] not in power_data.keys():
            power_data[entry['keyword']] = []
        power_data[entry['keyword']].append(float(entry['binvalue']))

    for outlet in power_data.keys():
        avg_draw[outlet] = np.mean(power_data[outlet])
        max_draw[outlet] = max(power_data[outlet])

    return avg_draw, max_draw


def main(date):
    power_strips = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M']
    outlets = []
    for power_strip in power_strips:
        for i in [1, 2, 3, 4, 5, 6, 7, 8]:
            outlets.append(f'OUTLET_{power_strip}{i}_DRAW')
        if power_strip == 'B':
            for i in [9, 10, 11, 12, 13, 14,  15, 16]:
                outlets.append(f'OUTLET_{power_strip}{i}_DRAW')

    power_history, outlet_names = get_power_telemetry(date, outlets)
    avg_draw, max_draw = analyze_outlet_use(power_history)

    # Which outlets have the highest avg draw?
    threshold = 100
    print(f"Outlets drawing more than {threshold:.0f} W on average:")
    for outlet in avg_draw.keys():
        if avg_draw[outlet] > threshold:
            print(f"  {outlet} ({outlet_names[outlet]}) average draw = {avg_draw[outlet]:.0f} W")
    analyze_total_power(date, power_history)


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
