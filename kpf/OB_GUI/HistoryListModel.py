from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

from PyQt5 import QtWidgets, QtCore, QtGui


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
        start_time = self.exposure_start_times[ind.row()]
        start_str = start_time.strftime('%H:%M:%S')
        output_line = f"{exposure.get('target'):15s} {start_str:<12s} {exposure.get('exptime'):.0f} s"
        return output_line

    def icon_output(self, ind):
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
                self.exposures.append({'target': target,
                                       'exptime': exptime})
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
