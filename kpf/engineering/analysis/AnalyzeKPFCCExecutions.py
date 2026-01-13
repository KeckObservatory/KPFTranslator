import sys
from pathlib import Path
from datetime import datetime, timedelta
import re

from astropy.table import Table, Column
import numpy as np

from matplotlib import pyplot as plt
from matplotlib import ticker


semester = '2025B'
logdir = Path(f'/s/sdata1701/KPFTranslator_logs/')
execution_history_file = logdir / f'KPFCC_executions_{semester}.csv'
executions = Table.read(execution_history_file, format='ascii.csv')

remove_rows = []
timestamps = []
line_deltas = []
time_deltas = []
UTnight_strings = []
CNdelta = []
for r,ex in enumerate(executions):

    # Remove Calibration or filler rows
    if re.search('Calibration', ex['OB summary']) is not None:
        remove_rows.append(r)
#     elif int(ex['scheduleUT']) in [0, 24]:
#         print(f"Removing {ex['OB summary']} because scheduled time is {ex['scheduleUT']}")
#         remove_rows.append(r)
    else:
        # Add timestamps
        timestamps.append(datetime.strptime(ex['timestamp'], '%Y-%m-%d %H:%M:%S UT'))
        # Add line delta
        line_deltas.append(ex['executed_line'] - ex['schedule_current_line'] - 0.5)
        # Add time deltas
        time_deltas.append(ex['decimalUT']-ex['scheduleUT'])
        # Add night string
        UTnight_strings.append(ex['timestamp'].split()[0])
        # Check current, next lines are 1 apart
        CNdelta.append(ex['schedule_next_line'] - ex['schedule_current_line'])

print(f"Removing {len(remove_rows)} entries")
executions.remove_rows(remove_rows)
executions.add_column(Column(timestamps, name='datetime'))
executions.add_column(Column(line_deltas, name='line_delta'))
executions.add_column(Column(time_deltas, name='time_delta'))
executions.add_column(Column(UTnight_strings, name='UTnight'))
executions.add_column(Column(CNdelta, name='CNdelta'))

# print(executions.keys())
# print(executions['executed_line', 'schedule_current_line', 'schedule_next_line', 'on_schedule'][:9])
# print(executions['decimalUT', 'scheduleUT', 'scheduleUT_current', 'scheduleUT_next', 'on_schedule'][:9])
# print(executions['datetime', 'line_delta', 'time_delta', 'UTnight', 'on_schedule'][:9])

on_schedule_groups = executions.group_by('on_schedule')
off_schedule = on_schedule_groups.groups[0]
off_schedule = off_schedule[off_schedule['scheduleUT'] < 23.99]
on_schedule = on_schedule_groups.groups[1]
unscheduled = executions[executions['scheduleUT'] > 23.99]
PctOffSched = len(off_schedule)/len(executions)
PctOnSched = len(on_schedule)/len(executions)
PctUnSched = len(unscheduled)/len(executions)
print(f"In {semester}, {len(executions)} KPF-CC science OBs have been successfully executed.")
print(f"  {len(on_schedule):4d} scheduled OBs were executed according to the schedule ({PctOnSched:.1%})")
print(f"  {len(off_schedule):4d} scheduled OBs were executed off the prescribed schedule ({PctOffSched:.1%})")
print(f"  {len(unscheduled):4d} unscheduled OBs were executed ({PctUnSched:.1%})")


oddities = executions[(executions['CNdelta'] != 1) & (executions['schedule_next_line'] > -1)]
# print(oddities['UTnight', 'decimalUT', 'schedule_current_line', 'schedule_next_line'])
# print(np.median(oddities['CNdelta']), np.min(oddities['CNdelta']), np.max(oddities['CNdelta']))

# Time Delta Plot
plt.figure(figsize=(10,6))
plt.title('Distribution of Time Offsets from Schedule')
plt.subplot(2,1,1)
timebins_on = np.arange(-3,+3,0.10)
plt.hist(on_schedule['time_delta'], bins=timebins_on,
         color='g', alpha=0.4, label='On Schedule')
plt.axvline(0, color='k')
plt.legend(loc='best')
plt.ylabel('N Executions')

plt.subplot(2,1,2)
timebins_off = np.arange(-3,+3,0.10)
plt.hist(off_schedule['time_delta'], bins=timebins_off,
         color='r', alpha=0.4, label='Off Schedule')
plt.axvline(0, color='k')
plt.legend(loc='best')
plt.ylabel('N Executions')

plt.xlabel('Time Delta (hours) [actual-scheduled]')
plt.savefig('KPF-CC_TimeOffsetDistribution.png', bbox_inches='tight', pad_inches=0.1)


# Line Delta Plot
# plt.figure(figsize=(10,6))
# plt.title('Distribution of Schedule Line Offsets')
# plt.subplot(2,1,1)
# timebins_on = np.arange(-15.5,+14.5,1)
# plt.hist(on_schedule['line_delta'], bins=timebins_on, color='g', alpha=0.4)
# plt.axvline(0, color='k')
# plt.ylabel('N Executions')
# 
# plt.subplot(2,1,2)
# timebins_off = np.arange(-15.5,+14.5,1)
# plt.hist(off_schedule['line_delta'], bins=timebins_off, color='r', alpha=0.4)
# plt.axvline(0, color='k')
# plt.ylabel('N Executions')
# 
# plt.xlabel('Schedule Delta (lines) [actual-scheduled]')
# plt.savefig('KPF-CC_LineOffsetDistribution.png', bbox_inches='tight', pad_inches=0.1)
# plt.show()


# On Schedule Rate Over Semester
frac_on = []
frac_off = []
frac_un = []
Ntot = []
UTnights = []
UTnight_groups = executions.group_by('UTnight')
for key, UTnight_group in zip(UTnight_groups.groups.keys, UTnight_groups.groups):
    UTnights.append(key['UTnight'])
    Ntot.append(len(UTnight_group))

    N_on_schedule = len(UTnight_group[UTnight_group['on_schedule'] == 'True'])
    N_off_schedule = len(UTnight_group[UTnight_group['on_schedule'] == 'False'])
    N_unscheduled = len(UTnight_group[UTnight_group['scheduleUT'] > 23.99])
    N_off_schedule -= N_unscheduled

    frac_off.append(N_off_schedule/len(UTnight_group))
    frac_on.append(N_on_schedule/len(UTnight_group))
    frac_un.append(N_unscheduled/len(UTnight_group))

plt.figure(figsize=(10,6))
plt.title('Fraction of On Schedule (green), Off Schedule (red), and Unscheduled (Magenta) OBs')
plt.bar(range(1,len(UTnights)+1,1), frac_on, color='g')
plt.bar(range(1,len(UTnights)+1,1), frac_off, color='r', bottom=frac_on)
plt.bar(range(1,len(UTnights)+1,1), frac_un, color='m',
        bottom=np.array(frac_on)+np.array(frac_off))

for i,N in enumerate(Ntot):
    plt.text(i+0.60, 1.03, f"N={N}", rotation=90)

plt.ylim(0,1.15)
plt.xlim(0,len(UTnights)+1)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(1.0))
tick_labels = ['', ''] + [UTN[5:] for UTN in UTnights]
plt.gca().set_xticklabels(tick_labels, rotation=90)
plt.savefig('KPF-CC_OnScheduleRate.png', bbox_inches='tight', pad_inches=0.1)
# plt.show()