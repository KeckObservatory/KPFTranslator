from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

from PyQt5 import QtWidgets, QtCore, QtGui

import ktl

from kpf import cfg
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.observatoryAPIs.GetTelescopeRelease import GetTelescopeRelease
from kpf.observatoryAPIs.GetObservingBlocks import GetObservingBlocks
from kpf.magiq.RemoveTarget import RemoveTarget, RemoveAllTargets
from kpf.magiq.AddTarget import AddTarget
from kpf.magiq.SetTargetList import SetTargetList


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
    def __init__(self, *args, log=None, **kwargs):
        super(OBListModel, self).__init__(*args, **kwargs)
        self.OBs = []
        self.start_times = None
        self.update_observed_status()
        self.currentOB = -1
        self.nextOB = -1
        self.sort_key = None
        self.log = log
        self.magiq_enabled = True
        self.icon_path = Path(__file__).parent / 'icons'
        dcsint = cfg.getint('telescope', 'telnr', fallback=1)
        self.INSTRUME = ktl.cache(f'dcs{dcsint}', 'INSTRUME')
        self.INSTRUME.monitor()

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
            if np.isclose(start_time_decimal, 0) or np.isclose(start_time_decimal, 24):
                start_time_str = f"--:-- UT"
            else:
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
            return QtGui.QImage(f'{self.icon_path}/arrow.png')
        elif ind.row() == self.nextOB:
            return QtGui.QImage(f'{self.icon_path}/arrow-curve-000-left.png')
        # Check observed state
        if self.observed[ind.row()] is False:
            # Not observed yet tonight
            return QtGui.QImage(f'{self.icon_path}/status-offline.png')
        elif self.observed[ind.row()] is True:
            # All observations of this OB scheduled are complete
            return QtGui.QImage(f'{self.icon_path}/tick.png')
        elif self.observed[ind.row()] is None:
            # There is no history, so there is no observed status
            return QtGui.QImage(f'{self.icon_path}/question-small-white.png')
        elif self.observed[ind.row()] < 0:
            # This is a calibration OB
            return QtGui.QImage(f'{self.icon_path}/light-bulb-off.png')
        else:
            OB = self.OBs[ind.row()]
            all_visits = [i for i,v in enumerate(self.OBs) if v.OBID == OB.OBID]
            if all_visits.index(ind.row()) < self.observed[ind.row()]:
                return QtGui.QImage(f'{self.icon_path}/tick.png')
            else:
                return QtGui.QImage(f'{self.icon_path}/status-away.png')

    def refresh_history(self, history):
        self.log.debug(f'refresh_history')
        OBIDs = [OB.OBID for OB in self.OBs]
        refreshed = 0
        # Clear History in OBs and replace with refreshed values
        for i,OB in enumerate(self.OBs):
            self.OBs[i].History = []
        for i,h in enumerate(history):
            if h.get('id') in OBIDs:
                matched_index = OBIDs.index(h.get('id'))
                self.OBs[matched_index].History.append(h)
                refreshed += 1
        self.log.debug(f'  Refreshed {refreshed} out of {len(self.OBs)}')
        self.update_observed_status()
        self.log.debug(f'  Updated observed status')

    def update_observed_status(self):
        self.observed = [False]*len(self.OBs)
        for i,OB in enumerate(self.OBs):
            if len(OB.Observations) == 0 and len(OB.Calibrations) > 0:
                # This is a calibration OB
                self.observed[i] = -1
            elif OB.OBID in ['', 'None', None]:
                # There is no history, so there is no observed status
                self.observed[i] = None
            else:
                scheduled_visits = [i for i,v in enumerate(self.OBs) if v.OBID == OB.OBID]
                N_scheduled_visits = len(scheduled_visits)
                visits_tonight = [h for h in OB.History if len(h.get('exposure_start_times', [])) > 0]
                N_visits_tonight = len(visits_tonight)
                if N_visits_tonight == 0:
                    self.observed[i] = False
                elif N_visits_tonight < N_scheduled_visits:
                    self.observed[i] = N_visits_tonight
                else:
                    self.observed[i] = True
        self.update_current_next()

    def update_current_next(self):
        if self.start_times is None:
            self.currentOB = -1
            self.nextOB = -1
        else:
            now = datetime.utcnow()
            decimal_now = now.hour + now.minute/60 + now.second/3600
            masked_start_times = np.ma.MaskedArray(self.start_times)
            unscheduled_mask = (masked_start_times < 0.01) | (masked_start_times > 23.99)
            past = np.ma.masked_greater(np.array(masked_start_times) - decimal_now, 0)
            past.mask = past.mask | np.array([o is True for o in self.observed]) | unscheduled_mask
            if np.all(past.mask):
                self.currentOB = -1 # If nothing is in the past, there is no current
            else:
                self.currentOB = past.argmax() # Current is nearest start time in past
            future = np.ma.masked_less_equal(np.array(masked_start_times) - decimal_now, 0)
            future.mask = future.mask | np.array([o is True for o in self.observed]) | unscheduled_mask
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
        self.update_observed_status()

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
            if self.telescope_interactions_allowed() and self.magiq_enabled:
                self.log.info(f"Adding {targetname} to Magiq star list")
                AddTarget.execute(OB.Target.to_dict())

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
            if self.telescope_interactions_allowed() and self.magiq_enabled:
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
        checks = [self.INSTRUME.ascii in ['KPF', 'KPF-CC'],
                  GetTelescopeRelease.execute({}),
                  ]
        ok = np.all(checks)
        self.log.debug(f'telescope_interactions_allowed = {ok}')
        return ok

    def update_star_list(self):
        if self.telescope_interactions_allowed() and self.magiq_enabled:
            self.log.debug('update_star_list')
            star_list = [OB.Target.to_star_list() for OB in self.OBs
                         if OB.Target is not None]
            for line in star_list:
                self.log.debug(line)
            RemoveAllTargets.execute({})
            SetTargetList.execute({'StarList': '\n'.join(star_list)})
