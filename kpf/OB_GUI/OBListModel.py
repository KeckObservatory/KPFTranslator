from datetime import datetime, timedelta
import numpy as np

from PyQt5 import QtWidgets, QtCore, QtGui

from kpf.schedule.GetTelescopeRelease import GetTelescopeRelease
from kpf.magiq.RemoveTarget import RemoveTarget, RemoveAllTargets
from kpf.magiq.AddTarget import AddTarget
from kpf.magiq.SetTargetList import SetTargetList


##-------------------------------------------------------------------------
## Define observed_tonight function
##-------------------------------------------------------------------------
def observed_tonight(OB):
    now = datetime.utcnow()
    exposures_tonight = []
    for hist in OB.History:
        if len(hist.get('exposure_start_times', [])) > 0:
            for timestring in hist.get('exposure_start_times'):
                tstamp = datetime.strptime(timestring[:19], '%Y-%m-%dT%H:%M:%S')
                if (now-tstamp).days <= 1 and (tstamp.day == now.day):
                    exposures_tonight.append(timestring)
    return len(exposures_tonight)


##-------------------------------------------------------------------------
## Define Model for OB List
##-------------------------------------------------------------------------
class OBListModel(QtCore.QAbstractListModel):
    '''Model to hold the list of OBs that the observer will select from.
    
    Properties to Track
    - KPFCC (start_times is None)
    
    Methods?
    - append to list
    - remove from list
    - clear list
    - replace list
    - edit OB
    '''
    def __init__(self, *args, OBs=[], log=None, INSTRUME=None, **kwargs):
        super(OBListModel, self).__init__(*args, **kwargs)
        self.OBs = OBs
        self.start_times = None
        self.currentOB = -1
        self.nextOB = -1
        self.sort_key = None
        self.log = log
        self.INSTRUME = INSTRUME

    def data(self, ind, role):
        if role == QtCore.Qt.DisplayRole:
            return self.string_output(ind)
        elif role == QtCore.Qt.DecorationRole:
            return self.icon_output(ind)

    def string_output(self, ind):
        OB = self.OBs[ind.row()]
        if self.start_times is None:
            output_line = f"{str(OB):s}"
        else:
            start_time_decimal = self.start_times[ind.row()]
            sthr = int(np.floor(start_time_decimal))
            stmin = (start_time_decimal-sthr)*60
            start_time_str = f"{sthr:02d}:{stmin:02.0f} UT"
            output_line = f"{start_time_str}  {str(OB):s}"
        if OB.edited == True:
            output_line += ' [edited]'
        return output_line

    def icon_output(self, ind):
        if self.start_times is None:
            return
        # Check if this OB is next or current
        self.update_current_next()
        if ind.row() == self.currentOB:
            return QtGui.QImage('icons/arrow.png')
        elif ind.row() == self.nextOB:
            return QtGui.QImage('icons/arrow-curve-000-left.png')
        # Check observed state
        OB = self.OBs[ind.row()]
        all_visits = [i for i,v in enumerate(self.OBs) if v.OBID == OB.OBID]
        n_visits = len(all_visits)
        n_observed = observed_tonight(OB)
        if n_observed == 0:
            return QtGui.QImage('icons/status-offline.png')
        else:
            if all_visits.ind(ind.row()) < n_observed:
                return QtGui.QImage('icons/tick.png')
            else:
                return QtGui.QImage('icons/status-away.png')

    def update_current_next(self):
        if self.start_times is None:
            self.currentOB = -1
            self.nextOB = -1
        else:
            now = datetime.utcnow()
            decimal_now = now.hour + now.minute/60 + now.second/3600
            past = np.ma.masked_greater(np.array(self.start_times) - decimal_now, 0)
            self.currentOB = past.argmax() # Current is nearest start time in past
            future = np.ma.masked_less_equal(np.array(self.start_times) - decimal_now, 0)
            if np.all(future.mask):
                self.nextOB = -1 # If nothing is in the future, there is no next
            else:
                self.nextOB = future.argmin() # Next is nearest start time in future

    def rowCount(self, ind):
        return len(self.OBs)

    def sort(self, key=None):
        self.log.debug(f'OBListModel.sort: {key} {self.sort_key}')
        if key is not None:
            self.sort_key = key
        if self.sort_key == 'time' and self.start_times is not None:
            zipped = [z for z in zip(self.start_times, self.OBs)]
            zipped.sort(key=lambda z: z[0])
            self.OBs = [z[1] for z in zipped]
            self.start_times = [z[0] for z in zipped]
        elif self.sort_key == 'Name':
            self.OBs.sort(key=lambda o: o.Target.TargetName.value, reverse=False)
        elif self.sort_key == 'RA':
            self.OBs.sort(key=lambda o: o.Target.coord.ra.deg, reverse=False)
        elif self.sort_key == 'Dec':
            self.OBs.sort(key=lambda o: o.Target.coord.dec.deg, reverse=False)
        elif self.sort_key == 'Gmag':
            self.OBs.sort(key=lambda o: o.Target.Gmag.value, reverse=False)
        elif self.sort_key == 'Jmag':
            self.OBs.sort(key=lambda o: o.Target.Jmag.value, reverse=False)
        self.layoutChanged.emit()

    def set_list(self, OBs, start_times=None):
        self.log.debug('OBListModel.set_list')
        if start_times is not None:
            assert len(OBs) == len(start_times)
        self.OBs = OBs
        self.start_times = start_times
        if start_times is not None: self.sort_key = 'time'
        self.sort()
        self.update_star_list()

    def appendOB(self, OB, start_time=24):
        self.log.debug('OBListModel.append')
        self.OBs.append(OB)
        if self.start_times is not None:
            self.start_times.append(start_time)
            self.sort_key = 'time'
        self.sort()
        if OB.Target is not None:
            targetname = OB.Target.TargetName
            if self.telescope_interactions_allowed():
                self.log.info(f"Adding {targetname} to Magiq star list")
                AddTarget.execute({'TargetName': targetname})


    def extend(self, OBs, start_times=None):
        self.log.debug('OBListModel.extend')
        self.OBs.extend(OBs)
        if self.start_times is not None:
            if start_times is None:
                self.start_times.extend([24]*len(OBs))
            else:
                self.start_times.extend(start_times)
            self.sort_key = 'time'
        self.sort()
        self.update_star_list()

    def removeOB(self, ind):
        self.log.debug('OBListModel.removeOB')
        removed = self.OBs.pop(ind)
        self.log.info(f"Removing {removed.summary()} from OB List")
        if self.start_times is not None:
            stremoved = self.start_times.pop(ind)
        self.sort()
        if removed.Target is not None:
            targetname = removed.Target.TargetName
            if self.telescope_interactions_allowed():
                self.log.info(f"Removing {targetname} from Magiq star list")
                RemoveTarget.execute({'TargetName': targetname})

    def updateOB(self, ind, newOB):
        self.log.debug('OBListModel.updateOB')
        self.OBs[ind] = newOB
        self.sort()

    def clear_list(self):
        self.log.debug('OBListModel.clear_list')
        self.set_list([])
        self.layoutChanged.emit()
        self.update_star_list()

    ##-------------------------------------------
    ## Telescope Related Functions
    ##-------------------------------------------
    def telescope_interactions_allowed(self):
        checks = [self.INSTRUME.ktl_keyword.ascii in ['KPF', 'KPF-CC'],
                  GetTelescopeRelease.execute({}),
                  ]
        ok = np.all(checks)
        self.log.debug(f'telescope_interactions_allowed = {ok}')
        return ok

    def update_star_list(self):
        if self.telescope_interactions_allowed():
            self.log.debug('update_star_list')
            star_list = [OB.Target.to_star_list() for OB in self.OBs
                         if OB.Target is not None]
            for line in star_list:
                self.log.debug(line)
            RemoveAllTargets.execute({})
            SetTargetList.execute({'StarList': '\n'.join(star_list)})
