from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

import keygrabber

from PyQt5 import QtWidgets, QtCore, QtGui

from kpf import cfg


##-------------------------------------------------------------------------
## Define Model for History List
##-------------------------------------------------------------------------
class HistoryListModel(QtCore.QAbstractListModel):
    '''
    '''
    def __init__(self, *args, log=None, mock_date=False, **kwargs):
        super(HistoryListModel, self).__init__(*args, **kwargs)
        self.log = log
        self.mock_date = mock_date
        self.icon_path = Path(__file__).parent / 'icons'
        self.exposures = []
        self.exposure_start_times = []

    def data(self, ind, role):
        if role == QtCore.Qt.DisplayRole:
            return self.string_output(ind)
        elif role == QtCore.Qt.DecorationRole:
            return self.icon_output(ind)

    def string_output(self, ind):
        exposure = self.exposures[ind.row()]
        output_line = f"{exposure.get('start_time', '')[11:]:<11s}   "
        output_line += f"{exposure.get('target'):15s} "
        output_line += f"{exposure.get('exptime'):5.0f} s   "
        output_line += f"{exposure.get('L0_file', '')} "
        return output_line

    def icon_output(self, ind):
        exposure = self.exposures[ind.row()]
        if exposure.get('junk') == True:
            return QtGui.QImage(f'{self.icon_path}/cross-script.png')
        else:
            return QtGui.QImage(f'{self.icon_path}/tick.png')

    def refresh_history(self, history):
        self.log.debug(f'refresh_history')
        self.exposures = []
        self.exposure_start_times = []
        for i,h in enumerate(history):
            target = h.get('target')
            for j,st_str in enumerate(h.get('exposure_start_times')):
                st = datetime.strptime(f"{st_str}0000", '%Y-%m-%dT%H:%M:%S.%f')
                exptime = h.get('exposure_times')[j]
                junk = h.get('junk', [False]*len(h.get('exposure_times')))[j]
                exposure_data = {'target': target,
                                 'start_time': st_str,
                                 'exptime': exptime,
                                 'junk': junk,
                                 'id': h.get('id')}
                # Try to determine L0 file name
                try:
                    fastreadtime = cfg.getfloat('time_estimates', f'readout_red_fast')
                    normalreadtime = cfg.getfloat('time_estimates', f'readout_red')
                    assemblytime = cfg.getfloat('time_estimates', f'assembly')
                    stHST = st-timedelta(hours=10)
                    begin = stHST+timedelta(seconds=exptime+fastreadtime)
                    end = stHST+timedelta(seconds=exptime+normalreadtime+assemblytime+10)
                    L0_hist = keygrabber.retrieve({'kpfassemble': ['LOUTFILE']},
                                         begin=begin.timestamp(),
                                         end=end.timestamp())
                    for entry in L0_hist:
                        L0_time = datetime.fromtimestamp(entry.get('time'))
                        assembly_delay = L0_time-(stHST+timedelta(seconds=exptime))
                        if assembly_delay.total_seconds() > 0:
                            exposure_data['L0_file'] = Path(entry.get('ascvalue')).name
                except Exception as e:
                    print('Failed to get keyword history')
                    print(e)
                self.exposures.append(exposure_data)
                self.exposure_start_times.append(st)
        self.sort()

    def rowCount(self, ind):
        return len(self.exposures)

    def sort(self, key=None):
        self.log.debug(f'HistoryListModel.sort')
        zipped = [z for z in zip(self.exposure_start_times, self.exposures)]
        zipped.sort(key=lambda z: z[0])
        self.exposures = [z[1] for z in zipped]
        self.exposure_start_times = [z[0] for z in zipped]
        self.layoutChanged.emit()
