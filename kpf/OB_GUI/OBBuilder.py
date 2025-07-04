from pathlib import Path
import copy
import yaml
import datetime
import numpy as np

from kpf.ObservingBlocks.Target import Target
from kpf.ObservingBlocks.Calibration import Calibration
from kpf.ObservingBlocks.Observation import Observation
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.schedule import get_semester_dates
from kpf.scripts.EstimateOBDuration import EstimateOBDuration


class OBBuilder(object):
    def __init__(self, log=None, OBListModel=None):
        self.log = log
        self.OBListModel = OBListModel
        self.SciObservingBlock = None
        self.CalObservingBlock = None
        self.BuildTarget = Target({})
        self.BuildObservation = [Observation({})]
        self.BuildCalibration = [Calibration({})]
        # Example Calibrations
        self.example_cal_file = Path(__file__).parent.parent / 'ObservingBlocks' / 'exampleOBs' / 'Calibrations.yaml'
        if self.example_cal_file.exists():
            self.example_calOB = ObservingBlock(self.example_cal_file)
        else:
            self.example_calOB = ObservingBlock({})


    ##-------------------------------------------
    ## Methods to interact with OB files on disk
    ##-------------------------------------------
    def save_OB_to_file(self, OB, default=None):
        self.log.debug('save_OB_to_file')
        if default is None: default = self.file_path
        result = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File',
                                             f"{default}",
                                             "OB Files (*yaml);;All Files (*)")
        if result:
            save_file = result[0]
            if save_file != '':
                # save fname as path to use in future
                self.file_path = Path(save_file).parent
                self.log.info(f'Saving OB to file: {save_file}')
                OB.write_to(save_file)
        else:
            self.log.debug('No output file chosen')

    def load_OB_from_file(self):
        self.log.debug('load_SciOB_from_file')
        newOB = None
        file, filefilter = QtWidgets.QFileDialog.getOpenFileName(self, 
                                     "Open File", f"{self.file_path}",
                                     "OB Files (*yaml);;All Files (*)")
        if file:
            file = Path(file)
            if file.exists():
                self.file_path = file.parent
                self.log.debug(f"Opening: {str(file)}")
                newOB = ObservingBlock(file)
        return newOB


    ##--------------------------------------------------------------
    ## Generic Methods to Build an OB Component
    ##--------------------------------------------------------------
    def BuildOBC_set(self, input_object, input_class_name=None):
        if input_class_name is None:
            if type(input_object) == list:
                input_class_name = type(input_object[0]).__name__
            else:
                input_class_name = type(input_object).__name__
        self.log.debug(f"Running BuildOBC_set on a {input_class_name}")
        setattr(self, f'Build{input_class_name}', input_object)
        self.BuildOBC_render_text(input_class_name)

    def BuildOBC_render_text(self, input_class_name):
        self.log.debug(f"Running BuildOBC_render_text for {input_class_name}")
        thing = getattr(self, f'Build{input_class_name}')
        view = getattr(self, f'Build{input_class_name}View')
        edited_lines = view.document().toPlainText()
        # Record cursor position
        cursor = view.textCursor()
        cursor_position = cursor.position()
        if thing in [None, []]:
            lines = ''
        elif type(thing) == list:
            lines = ''
            for i,item in enumerate(thing):
                lines += f'# {input_class_name} {i+1}\n'
                lines += item.__repr__(prune=True, comment=True)
        else:
            lines = thing.__repr__(prune=True, comment=True)
        if edited_lines != lines:
            view.setPlainText(lines)
            # Restore cursor position
            try:
                cursor.setPosition(cursor_position)
                view.setTextCursor(cursor)
            except Exception as e:
                self.log.error(f'Failed to set cursor position in {view}')
                self.log.error(e)
        valid = getattr(self, f'Build{input_class_name}Valid')
        if thing in [None, []]:
            isvalid = False
        elif type(thing) == list:
            isvalid = np.all([item.validate() for item in thing])
        else:
            isvalid = thing.validate()
        color = {True: 'green', False: 'orange'}[isvalid]
        valid.setText(str(isvalid))
        valid.setStyleSheet(f"color:{color}")

    def BuildOBC_edit(self, input_class_name):
        self.log.debug(f"Running BuildOBC_edit for {input_class_name}")
        thing = getattr(self, f'Build{input_class_name}')
        view = getattr(self, f'Build{input_class_name}View')
        edited_lines = view.document().toPlainText()
        if edited_lines == '' and thing is None:
            return
        if type(thing) == list:
            lines = ''
            for i,item in enumerate(thing):
                lines += f'# {input_class_name} {i+1}\n'
                lines += item.__repr__(prune=False, comment=True)
        else:
            lines = thing.__repr__(prune=False, comment=True)
        if edited_lines != lines:
            try:
                new_data = yaml.safe_load(edited_lines)
                class_dict = {"Target": Target, "Observation": Observation, "Calibration": Calibration}
                if input_class_name == 'Target':
                    new_thing = class_dict[input_class_name](new_data)
                elif input_class_name in ['Observation', 'Calibration']:
                    new_thing = [class_dict[input_class_name](item) for item in new_data]
                self.BuildOBC_set(new_thing)
            except Exception as e:
                self.log.error(f'Failed to parse edited {input_class_name} text')
                self.log.error(e)
                self.log.error(f'Not changing contents')


    ##--------------------------------------------------------------
    ## Methods for the Build a Science OB Tab Target Section
    ##--------------------------------------------------------------
    def set_Target(self, target):
        self.BuildOBC_set(target)
        self.form_SciOB()

    def clear_Target(self):
        self.set_Target(Target({}))

    def edit_Target(self):
        self.BuildOBC_edit('Target')
        self.form_SciOB()

    def query_Simbad(self):
        self.log.debug(f"Running query_Simbad")
        target_name = self.QuerySimbadLineEdit.text().strip()
        self.log.debug(f"Querying: {target_name}")
        newtarg = self.BuildTarget.resolve_name(target_name)
        if newtarg is None:
            self.log.warning(f"Query failed for {target_name}")
        self.QuerySimbadLineEdit.setText('')
        self.set_Target(newtarg)


    ##--------------------------------------------------------------
    ## Methods for the Build a Science OB Tab Observations Section
    ##--------------------------------------------------------------
    def set_Observations(self, observations):
        self.BuildOBC_set(observations)
        self.form_SciOB()

    def clear_Observations(self):
        self.log.debug(f"Running clear_Observations")
        self.set_Observations([Observation({})])

    def edit_Observations(self):
        self.BuildOBC_edit('Observation')
        self.form_SciOB()


    ##--------------------------------------------------------------
    ## Methods for the Build a Science OB Tab Observing Block
    ##--------------------------------------------------------------
    def form_SciOB(self):
        self.log.debug(f"Running form_SciOB")
        semester, start, end = get_semester_dates(datetime.datetime.now())
        if self.SciOBProgramID.text() != '':
            OBdict = {'ProgramID': self.SciOBProgramID.text(),
                      'semester': semester,
                      'semid': f'{semester}_{self.SciOBProgramID.text()}'}
        else:
            OBdict = {}
        newOB = ObservingBlock(OBdict)
        newOB.Target = self.BuildTarget
        newOB.Observations = self.BuildObservation
        if newOB.__repr__() == self.SciObservingBlock.__repr__():
            self.log.debug('newOB and existing OB match')
            return
        self.SciObservingBlock = ObservingBlock(OBdict)
        self.SciObservingBlock.Target = self.BuildTarget
        self.SciObservingBlock.Observations = self.BuildObservation
        # Validate
        OBValid = self.SciObservingBlock.validate()
        color = {True: 'green', False: 'orange'}[OBValid]
        self.SciOBValid.setText(str(OBValid))
        self.SciOBValid.setStyleSheet(f"color:{color}")
        if OBValid:
            self.SciOBString.setText(self.SciObservingBlock.summary())
            duration = EstimateOBDuration.execute({}, OB=self.SciObservingBlock)
            self.SciOBEstimatedDuration.setText(f"{duration/60:.0f} min")
        else:
            self.SciOBString.setText('')
            self.SciOBEstimatedDuration.setText('')

    def send_SciOB_to_list(self):
        if self.SciObservingBlock.validate() != True:
            self.log.warning('OB is invalid, not sending to OB list')
            return
        targetname = self.SciObservingBlock.Target.TargetName
        self.log.info(f"Adding {targetname} to OB list")
        self.OBListModel.appendOB(self.SciObservingBlock)

    def save_SciOB_to_file(self):
        self.log.debug('save_SciOB_to_file')
        targname = self.SciObservingBlock.Target.get('TargetName')
        self.save_OB_to_file(self.SciObservingBlock,
                             default=f"{self.file_path}/{targname}.yaml")

    def load_SciOB_from_file(self):
        self.log.debug('load_SciOB_from_file')
        newOB = self.load_OB_from_file()
        if newOB.validate() == True:
            if newOB.ProgramID is not None:
                self.SciOBProgramID.setText(newOB.ProgramID)
            self.set_Target(newOB.Target)
            self.set_Observations(newOB.Observations)


    ##-------------------------------------------
    ## Methods for the Build a Calibration OB Tab
    ##-------------------------------------------
    def set_Calibrations(self, calibrations):
        self.BuildOBC_set(calibrations)
        self.form_CalOB()

    def clear_Calibrations(self):
        self.log.debug(f"Running clear_Calibrations")
        self.BuildOBC_set([], input_class_name='Calibration')

    def edit_Calibrations(self):
        self.BuildOBC_edit('Calibration')
        self.form_CalOB()

    def add_example_calibration(self, value):
        self.log.debug(f'add_example_calibration: {value}')
        for cal in self.example_calOB.Calibrations:
            if value == cal.get('Object'):
                self.log.debug(f'Adding {value} from example Cal OB')
                calibrations = copy.deepcopy(self.BuildCalibration)
                calibrations.append(cal)
                self.set_Calibrations(calibrations)

    def form_CalOB(self):
        self.log.debug(f"Running form_CalOB")
        semester, start, end = get_semester_dates(datetime.datetime.now())
        OBdict = {'ProgramID': 'ENG',
                  'semester': semester,
                  'semid': f'{semester}_ENG'}
        newOB = ObservingBlock(OBdict)
        newOB.Calibrations = self.BuildCalibration if self.BuildCalibration is not None else []
        if newOB.__repr__() == self.CalObservingBlock.__repr__():
            return
        self.CalObservingBlock = copy.deepcopy(newOB)
        OBValid = self.CalObservingBlock.validate()
        color = {True: 'green', False: 'orange'}[OBValid]
        self.CalOBValid.setText(str(OBValid))
        self.CalOBValid.setStyleSheet(f"color:{color}")
        if OBValid:
            self.CalOBString.setText(self.CalObservingBlock.summary())
            duration = EstimateOBDuration.execute({}, OB=self.CalObservingBlock)
            self.CalEstimatedDuration.setText(f"{duration/60:.0f} min")
        else:
            self.CalOBString.setText('')
            self.CalEstimatedDuration.setText('')

    def send_CalOB_to_list(self):
        if self.CalObservingBlock.validate() != True:
            self.log.warning('OB is invalid, not sending to OB list')
        else:
            self.OBListModel.appendOB(self.CalObservingBlock)

    def save_CalOB_to_file(self):
        self.log.debug('save_CalOB_to_file')
        self.save_OB_to_file(self.CalObservingBlock,
                             default=f"{self.file_path}/newcalibration.yaml")

    def save_SciOB_to_file(self):
        self.log.debug('save_SciOB_to_file')
        targname = self.SciObservingBlock.Target.get('TargetName')
        self.save_OB_to_file(self.SciObservingBlock,
                             default=f"{self.file_path}/{targname}.yaml")

    def load_CalOB_from_file(self):
        self.log.debug('load_CalOB_from_file')
        newOB = self.load_OB_from_file()
        if newOB.validate() == True:
            self.set_Calibrations(newOB.Calibrations)
