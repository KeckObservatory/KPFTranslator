import yaml
from datetime import datetime, timedelta
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui

from kpf.ObservingBlocks.Target import Target
from kpf.ObservingBlocks.Calibration import Calibration
from kpf.ObservingBlocks.Observation import Observation
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.schedule.GetScheduledPrograms import GetScheduledPrograms


##-------------------------------------------------------------------------
## Define Model for MVC
##-------------------------------------------------------------------------
class OBListModel(QtCore.QAbstractListModel):
    '''Model to hold the list of OBs that the observer will select from.
    '''
    def __init__(self, *args, OBs=[], **kwargs):
        super(OBListModel, self).__init__(*args, **kwargs)
        self.OBs = OBs
        self.start_times = None

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            if self.start_times is None:
                OB = self.OBs[index.row()]
                output_line = f"{str(OB):s}"
            else:
                OB = self.OBs[index.row()]
                start_time_decimal = self.start_times[index.row()]
                sthr = int(np.floor(start_time_decimal))
                stmin = (start_time_decimal-sthr)*60
                start_time_str = f"{sthr:02d}:{stmin:02.0f} UT"
                output_line = f"{start_time_str}  {str(OB):s}"
            if OB.edited == True:
                output_line += ' [edited]'
            return output_line
        if role == QtCore.Qt.DecorationRole:
            OB  = self.OBs[index.row()]
            if OB.executed == True:
                return QtGui.QColor('black')
            else:
                return QtGui.QColor('green')

    def rowCount(self, index):
        return len(self.OBs)

    def sort(self, sortkey):
        if self.start_times is not None:
            zipped = [z for z in zip(self.start_times, self.OBs)]
            zipped.sort(key=lambda z: z[0])
            self.OBs = [z[1] for z in zipped]
            self.start_times = [z[0] for z in zipped]
        elif sortkey == 'Name':
            self.OBs.sort(key=lambda o: o.Target.TargetName.value, reverse=False)
        elif sortkey == 'RA':
            self.OBs.sort(key=lambda o: o.Target.coord.ra.deg, reverse=False)
        elif sortkey == 'Dec':
            self.OBs.sort(key=lambda o: o.Target.coord.dec.deg, reverse=False)
        elif sortkey == 'Gmag':
            self.OBs.sort(key=lambda o: o.Target.Gmag.value, reverse=False)
        elif sortkey == 'Jmag':
            self.OBs.sort(key=lambda o: o.Target.Jmag.value, reverse=False)


##-------------------------------------------------------------------------
## Confirmation Popup
##-------------------------------------------------------------------------
class ConfirmationPopup(QtWidgets.QMessageBox):
    '''Wrapper for easy use
    '''
    def __init__(self, window_title, msg, info_only=False, warning=False,
                 *args, **kwargs):
        QtWidgets.QMessageBox.__init__(self, *args, **kwargs)
        self.setWindowTitle(window_title)
        if type(msg) == list:
            msg = "\n".join(msg)
        self.setText(msg)
        if info_only == True:
            self.setIcon(QtWidgets.QMessageBox.Information)
            self.setStandardButtons(QtWidgets.QMessageBox.Ok)
        else:
            self.setIcon(QtWidgets.QMessageBox.Question)
            self.setStandardButtons(QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes) 
        if warning is True:
            self.setIcon(QtWidgets.QMessageBox.Warning)

##-------------------------------------------------------------------------
## Input Popup
##-------------------------------------------------------------------------
class InputPopup(QtWidgets.QDialog):
    '''Wrapper for easy use
    '''
    def __init__(self, window_title, msg, *args, **kwargs):
        super().__init__()
        self.setWindowTitle(window_title)
        self.result = ''
        layout = QtWidgets.QVBoxLayout()
        # Render message
        if type(msg) == list:
            msg = "\n".join(msg)
        layout.addWidget(QtWidgets.QLabel(msg))
        # Render input box
        self.input_field = QtWidgets.QLineEdit()
        self.input_field.textChanged.connect(self.edit_input)
        layout.addWidget(self.input_field)
        # Set up buttons
        QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)
        # Wrap up definition of the InputPopup
        self.setLayout(layout)
        self.setStyleSheet("min-width:350 px;")

    def edit_input(self, value):
        self.result = value


##-------------------------------------------------------------------------
## Scrollable QMessageBox
##-------------------------------------------------------------------------
class ScrollMessageBox(QtWidgets.QMessageBox):
    '''Custom message box to show the contents of an OB (as it would appear in
    a .yaml file on disk) in a scrollable window.
    '''
    def __init__(self, OB, *args, **kwargs):
        contents = OB.__repr__()
        QtWidgets.QMessageBox.__init__(self, *args, **kwargs)
        self.setStandardButtons(QtWidgets.QMessageBox.Close | QtWidgets.QMessageBox.Cancel)
        self.button(QtWidgets.QMessageBox.Cancel).setText("Edit OB")
        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        self.content = QtWidgets.QWidget()
        scroll.setWidget(self.content)
        lay = QtWidgets.QVBoxLayout(self.content)
        contents_label = QtWidgets.QLabel(contents, self)
        contents_label.setFont(QtGui.QFont('Courier New', 11))
        lay.addWidget(contents_label)
        self.layout().addWidget(scroll, 0, 0, 1, self.layout().columnCount())
        self.setStyleSheet("QScrollArea{min-width:450 px; min-height: 600px;}")


##-------------------------------------------------------------------------
## Observer Comment Dialog Box
##-------------------------------------------------------------------------
class ObserverCommentBox(QtWidgets.QDialog):
    '''Custom dialog box for observers to submit observer comments on an OB.
    '''
    def __init__(self, SOB, observer):
        super().__init__()
        self.SOB = SOB
        self.comment = ''
        self.observer = observer
        self.setWindowTitle(f"Observer Comment Form: {self.SOB.summary()}")
        layout = QtWidgets.QVBoxLayout()

        # Initial message lines
        line1 = QtWidgets.QLabel("Submit an observer comment for:")
        layout.addWidget(line1)
        line2 = QtWidgets.QLabel(f"{self.SOB.summary()}")
        myFont=QtGui.QFont()
        myFont.setBold(True)
        line2.setFont(myFont)
        layout.addWidget(line2)
        line3 = QtWidgets.QLabel(f"ProgramID: {self.SOB.ProgramID}")
        layout.addWidget(line3)
        line4 = QtWidgets.QLabel(f"OB ID: {self.SOB.OBID}\n")
        layout.addWidget(line4)

        # Add observer field
        observer_label = QtWidgets.QLabel('Observer/Commenter:')
        layout.addWidget(observer_label)
        self.observer_field = QtWidgets.QLineEdit()
        self.observer_field.setText(self.observer)
        self.observer_field.textChanged.connect(self.edit_observer)
        layout.addWidget(self.observer_field)

        # Add comment field
        comment_label = QtWidgets.QLabel('Comment:')
        layout.addWidget(comment_label)
        self.comment_field = QtWidgets.QLineEdit()
        self.comment_field.textChanged.connect(self.edit_comment)
        layout.addWidget(self.comment_field)

        # Set up buttons
        QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

        if self.SOB.OBID in ['', None]:
            self.observer_field.setEnabled(False)
            self.comment_field.setEnabled(False)
            self.buttonBox.setEnabled(False)
            line4.setText(f"OB ID is unknown, can not submit comment\n")

        # Wrap up definition of the ObserverCommentBox
        self.setLayout(layout)
        self.setStyleSheet("min-width:300 px;")

    def edit_comment(self, value):
        self.comment = value

    def edit_observer(self, value):
        self.observer = value


##-------------------------------------------------------------------------
## Select Program Popup Window
##-------------------------------------------------------------------------
class SelectProgramPopup(QtWidgets.QDialog):
    '''Custom dialog box for observers to select program to load OBs from.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Select Program")
        layout = QtWidgets.QVBoxLayout()
        self.ProgID = ''
        # Add ProgramID selection
        programID_label = QtWidgets.QLabel('Select Program ID:')
        layout.addWidget(programID_label)
        classical, cadence = GetScheduledPrograms.execute({})
        program_strings = [f"{p['ProjCode']} on {p['Date']}" for p in classical]
        programID_selector = QtWidgets.QComboBox()
        programID_selector.addItems([''])
        programID_selector.addItems(program_strings)
        programID_selector.currentTextChanged.connect(self.choose_progID)
        layout.addWidget(programID_selector)
        # Set up buttons
        QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)
        # Wrap up definition
        self.setLayout(layout)
        self.setStyleSheet("min-width:100 px;")

    def choose_progID(self, program_string):
        self.ProgID = program_string.split()[0]


##-------------------------------------------------------------------------
## Editable QMessageBox
##-------------------------------------------------------------------------
class EditableMessageBox(QtWidgets.QMessageBox):
    '''Custom message box to edit the contents of an OB (as it would appear in
    a .yaml file on disk) in a scrollable window.
    '''
    def __init__(self, input_object, *args, **kwargs):
        self.input_type = type(input_object)
        assert self.input_type in [Target, Calibration, Observation, ObservingBlock]
        self.input_object = input_object
        self.original_lines = input_object.__repr__(prune=False)
        self.edited_lines = input_object.__repr__(prune=False)
        self.result = self.input_object
        self.valid = self.input_object.validate()
        #
        QtWidgets.QMessageBox.__init__(self, *args, **kwargs)
        self.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        wdgt = QtWidgets.QWidget()
        scroll.setWidget(wdgt)
        lay = QtWidgets.QVBoxLayout(wdgt)
        # Explanatory text
        if self.input_type is ObservingBlock:
            msg = ['The text area below is an editable version of the OB.',
                   'Note that the edited OB will be executable, but will not be',
                   'uploaded to the database. To make changes permanent, edit',
                   'the OB via the web form.']
        else:
            msg = [f'The text area below is an editable version of the {self.input_type.__name__}.']
        helptext = QtWidgets.QLabel('\n'.join(msg))
        lay.addWidget(helptext)
        # Add Editable YAML text
        self.contents = QtWidgets.QPlainTextEdit(self.edited_lines, self)
        self.contents.setFont(QtGui.QFont('Courier New', 11))
        self.contents.textChanged.connect(self.edit_object)
        lay.addWidget(self.contents)
        # Add validate button
        validate_button = QtWidgets.QPushButton('Validate')
        validate_button.clicked.connect(self.validate_object)
        lay.addWidget(validate_button)
        # Finish layout
        self.layout().addWidget(scroll, 0, 0, 1, self.layout().columnCount())
        self.setStyleSheet("QScrollArea{min-width:450 px; min-height: 650px;}")

    def edit_object(self):
        self.edited_lines = self.contents.document().toPlainText()
        try:
            new_dict = yaml.safe_load(self.edited_lines)
            if type(new_dict) == list:
                self.result = [self.input_type(entry) for entry in new_dict]
                self.valid = np.all([entry.validate() for entry in self.result])
            else:
                self.result = self.input_type(new_dict)
                self.valid = self.result.validate()
            if self.input_type == ObservingBlock:
                self.result.edited = (self.edited_lines != self.original_lines)
                self.result.executed = self.input_object.executed
        except Exception as e:
            print(e)
            if self.input_type == Observation:
                self.result = []
            else:
                self.result = None

    def validate_object(self):
        validationpopup = QtWidgets.QMessageBox()
        valid_str = {True: 'valid', False: 'invalid'}[self.valid]
        valid_icon = {True: QtWidgets.QMessageBox.Information,
                      False: QtWidgets.QMessageBox.Critical}[self.valid]
        validationpopup.setText(f"{self.input_type.__name__} is {valid_str}")
        validationpopup.setIcon(valid_icon)
        validationpopup.setStandardButtons(QtWidgets.QMessageBox.Ok) 
        validationpopup.exec_()


class OBEditableMessageBox(QtWidgets.QMessageBox):
    '''Custom message box to edit the contents of an OB (as it would appear in
    a .yaml file on disk) in a scrollable window.
    '''
    def __init__(self, OB, *args, **kwargs):
        self.OB = OB
        self.OBlines_original = self.OB.__repr__()
        self.OBlines = self.OB.__repr__()
        self.newOB = None
        QtWidgets.QMessageBox.__init__(self, *args, **kwargs)
        self.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        wdgt = QtWidgets.QWidget()
        scroll.setWidget(wdgt)
        lay = QtWidgets.QVBoxLayout(wdgt)
        # Add explanatory text
        msg = ['The text area below is an editable version of the OB.',
               'Note that the edited OB will be executable, but will not be',
               'uploaded to the database. To make changes permanent, edit',
               'the OB via the web form.']
        helptext = QtWidgets.QLabel('\n'.join(msg))
        lay.addWidget(helptext)
        # Add Editable YAML text
        self.contents = QtWidgets.QPlainTextEdit(self.OBlines, self)
        self.contents.setFont(QtGui.QFont('Courier New', 11))
        self.contents.textChanged.connect(self.edit_OB)
        lay.addWidget(self.contents)
        # Add validate button
        validate_button = QtWidgets.QPushButton('Validate')
        validate_button.clicked.connect(self.validate_OB)
        lay.addWidget(validate_button)

        self.layout().addWidget(scroll, 0, 0, 1, self.layout().columnCount())
        self.setStyleSheet("QScrollArea{min-width:450 px; min-height: 650px;}")

    def validate_OB(self):
        self.OBlines = self.contents.document().toPlainText()
        valid = False
        try:
            newOB = ObservingBlock(yaml.safe_load(self.OBlines))
            valid = newOB.validate()
            if valid == False:
                print('OB is invalid)')
        except Exception as e:
            print('Failed to read in OB')
            print(e)
        validationpopup = QtWidgets.QMessageBox()
        valid_str = {True: 'valid', False: 'invalid'}[valid]
        valid_icon = {True: QtWidgets.QMessageBox.Information,
                      False: QtWidgets.QMessageBox.Critical}[valid]
        validationpopup.setText(f"OB is {valid_str}")
        validationpopup.setIcon(valid_icon)
        validationpopup.setStandardButtons(QtWidgets.QMessageBox.Ok) 
        validationpopup.exec_()

    def edit_OB(self):
        self.OBlines = self.contents.document().toPlainText()
        try:
            self.newOB = ObservingBlock(yaml.safe_load(self.OBlines))
            self.newOB.edited = True
            self.newOB.executed = self.OB.executed
        except:
            self.newOB = None


