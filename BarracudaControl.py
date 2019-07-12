# Standard library modules
import sys
import os
import pickle
import threading
import logging
import time

# GUI Framework
import BarracudaQt

# if r"C:\Program Files\Micro-Manager-2.0gamma" not in sys.path:
#     sys.path.append(r"C:\Program Files\Micro-Manager-2.0gamma")
# prev_dir = os.getcwd()
# os.chdir(r"C:\Program Files\Micro-Manager-2.0gamma")

# Custom modules
import DAQControl
import ImageControl
import OutletControl
import XYControl
import ZStageControl
import ObjectiveControl
import LaserControl
import PressureControl

# Installed modules
from PyQt5 import QtCore, QtGui, QtWidgets

# os.chdir(prev_dir)

HOME = False


# Possible Model Classes
class BaseSystem:
    def __init__(self):
        self.z_stage_control = None
        self.outlet_control = None
        self.objective_control = None
        self.image_control = None
        self.xy_stage_control = None
        self.daq_board_control = None
        self.laser_control = None
        self.pressure_control = None

    def start_system(self):
        pass

    def close_system(self):
        pass


class BarracudaSystem(BaseSystem):
    _z_stage_com = "COM4"
    _outlet_com = "COM7"
    _objective_com = "COM8"
    _laser_com = "COM6"
    _pressure_com = "COM7"
    _daq_dev = "/Dev1/"
    _z_stage_lock = threading.Lock()
    _outlet_lock = threading.Lock()
    _objective_lock = threading.Lock()
    _xy_stage_lock = threading.Lock()
    _pressure_lock = threading.Lock()

    xy_stage_size = [112792, 64340]  # Rough size in mm
    xy_stage_upper_left = [112598, -214]  # Reading on stage controller when all the way to left and up (towards wall)

    def __init__(self):
        super(BarracudaSystem, self).__init__()

    def start_system(self, live_feed=True):
        self.z_stage_control = ZStageControl.ZStageControl(com=self._z_stage_com, lock=self._z_stage_lock, home=HOME)
        self.outlet_control = OutletControl.OutletControl(com=self._outlet_com, lock=self._outlet_lock, home=HOME)
        self.objective_control = ObjectiveControl.ObjectiveControl(com=self._objective_com, lock=self._objective_lock, home=HOME)
        # self.image_control = ImageControl.ImageControl(home=HOME)
        self.xy_stage_control = XYControl.XYControl(lock=self._xy_stage_lock, home=HOME)
        # self.daq_board_control = DAQControl.DAQBoard(dev=self._daq_dev)
        # self.laser_control = LaserControl.Laser(com=self._laser_com, home=HOME)
        self.pressure_control = PressureControl.PressureControl(com=self._pressure_com, lock=self._pressure_lock, arduino=self.outlet_control.arduino, home=HOME)

        self.start_daq()

        if live_feed:
            self.start_image()

    def start_daq(self):
        pass

    def start_image(self):
        pass


class FinchSystem(BaseSystem):
    def __init__(self):
        super(FinchSystem, self).__init__()


class OstrichSystem(BaseSystem):
    def __init__(self):
        super(OstrichSystem, self).__init__()


class CERepository:
    def __init__(self):
        self.methods = None
        self.inserts = None
        self.sequences = None


class Well:
    def __init__(self, location, label=None, contents=None, shape=None, bounding_box=None):
        self.location = location
        self.label = label
        self.contents = contents
        self.shape = shape
        self.bound_box = bounding_box

    def __str__(self):
        return '{} at {} - SHAPE {} - BBOX {}'.format(self.label, self.location, self.shape, self.bound_box)


class Insert:
    def __init__(self, wells=None, label=None):
        self.wells = wells
        self.label = label


class Method:
    def __init__(self, label=None, steps=None, ID=None):
        self.ID = ID
        self.steps = steps
        self.label = label


class Sequence:
    def __init__(self, steps=None):
        self.steps = steps


# Control Classes
class ProgramController:
    def __init__(self):
        # Initialize system model, system hardware and the GUI
        self.repository = CERepository()
        self.hardware = BarracudaSystem()
        self.hardware.start_system()

        app = QtWidgets.QApplication(sys.argv)
        self.program_window = BarracudaQt.MainWindow()

        # Connect the views to the controllers.
        self.gs_screen = self.program_window.getting_started_screen
        self.gs_control = GettingStartedScreenController(self.gs_screen, self.hardware, self.repository)

        self.i_screen = self.program_window.insert_screen
        self.i_control = InsertScreenController(self.i_screen, self.hardware, self.repository)

        self.m_screen = self.program_window.method_screen
        self.m_control = MethodScreenController(self.m_screen, self.hardware, self.repository)

        self.s_screen = self.program_window.sequence_screen
        self.s_control = SequenceScreenController(self.s_screen, self.hardware, self.repository)

        self.r_screen = self.program_window.run_screen
        self.r_control = RunScreenController(self.r_screen, self.hardware, self.repository)

        self.d_screen = self.program_window.data_screen
        self.d_control = DataScreenController(self.d_screen, self.hardware, self.repository)

        self.program_window.show()
        sys.exit(app.exec_())


class GettingStartedScreenController:
    def __init__(self, screen, hardware, repository):
        self.screen = screen
        self.hardware = hardware
        self.repository = repository

        self.set_callbacks()

    def set_callbacks(self):
        pass

    def load_data(self):
        pass

    def load_insert(self):
        pass

    def load_method(self):
        pass

    def load_sequence(self):
        pass

    def load_system(self):
        pass

    def new_insert(self):
        pass

    def new_method(self):
        pass

    def new_sequence(self):
        pass


class InsertScreenController:
    def __init__(self, screen, hardware, repository):
        self.screen = screen
        self.hardware = hardware
        self.repository = repository

        self._um2pix = 1 / 200
        self._mm2pix = 2
        self._initial = True

        self.screen.image_view.setSceneRect(0, 0, self.hardware.xy_stage_size[0]*self._um2pix,
                                            self.hardware.xy_stage_size[1]*self._um2pix)
        self.screen.image_frame.controller = self
        self.insert = None
        self._set_callbacks()

    def _set_callbacks(self):
        """ Sets the callbacks for the InsertScreen. """
        self.screen.draw_circle_action.triggered.connect(lambda: self.draw_circle())
        self.screen.draw_rectangle_action.triggered.connect(lambda: self.draw_rectangle())
        self.screen.draw_array_action.triggered.connect(lambda: self.draw_array())
        self.screen.clear_object_action.triggered.connect(lambda: self.clear_object())
        self.screen.load_insert_action.triggered.connect(lambda: self.load_insert())
        self.screen.clear_area_action.triggered.connect(lambda: self.clear_area())
        self.screen.joystick_action.triggered.connect(lambda: self.joystick())
        self.screen.insert_table.currentCellChanged.connect(lambda: self.highlight_well())
        self.screen.select_file.released.connect(lambda: self.select_file())
        self.screen.save_file.released.connect(lambda: self.save_insert())

    def highlight_well(self):
        """ Prompts the view to highlight the well whose cell in the table is selected. """
        location = self.screen.insert_table.item(self.screen.insert_table.currentRow(), 1)
        if location:  # This check is necessary in case the last well is deleted.
            # Convert from the '({}, {})' format to [f, f]
            try:
                location = [float(x)*self._um2pix for x in location.text().rsplit('(')[1].rsplit(')')[0].rsplit(',')]
            except ValueError:  # The user changed the table contents to an invalid coordinate
                BarracudaQt.ErrorMessageUI(error_message='Well location is invalid.')
            else:
                self.screen.image_frame.highlight_item(location)

    def joystick(self):
        """ Prompts shapes to be created in the view via the joystick method. """
        # The event we are sending holds the current coordinates of the stage and converts them to pixel
        event = self.hardware.xy_stage_control.readXY()
        event[0] *= self._um2pix
        event[1] *= self._um2pix

        # If the user is trying to create and array or circle but hasn't specified radius, simply throw error.
        if not self.screen.circle_radius_input.text() and self.screen.image_frame.draw_shape != 'RECT':
            BarracudaQt.ErrorMessageUI(error_message='Radius not specified.')
            return

        if self.screen.image_frame.draw_shape == 'CIRCLE':  # Only need to know radius of well.
            event.append(float(self.screen.circle_radius_input.text())*self._mm2pix)

        elif self.screen.image_frame.draw_shape == 'ARRAY':  # Need to know dimensions of array and radius of wells.
            event.append(float(self.screen.circle_radius_input.text()) * self._mm2pix)
            event.append(float(self.screen.num_circles_horizontal_input.text()))
            event.append(float(self.screen.num_circles_vertical_input.text()))

        self.screen.image_frame.joystick = True  # So the image frame in the view handles the events appropriately.

        # Note: Every shape requires at least a press and release event ('move' as well in case of array and rect).
        if self._initial:
            self.screen.image_frame.mousePressEvent(event=event)

            if self.screen.image_frame.draw_shape == 'CIRCLE':  # Only one point necessary for a circle.
                self.screen.image_frame.mouseReleaseEvent(event=event)
        else:
            self.screen.image_frame.mouseMoveEvent(event=event)  # For arrays and rects, need to wait for second point.
            self.screen.image_frame.mouseReleaseEvent(event=event)

        if self.screen.image_frame.draw_shape != 'CIRCLE':  # Then the second point is a move and release event.
            self._initial = not self._initial

        self.screen.image_frame.joystick = False  # Returns image frame to mouse functionality.

    def add_row(self, well_location, label_saved=None):
        """ Adds a row to the table with the well label and location. """
        row_count = self.screen.insert_table.rowCount()
        self.screen.insert_table.insertRow(row_count)

        label = QtWidgets.QTableWidgetItem()
        location = QtWidgets.QTableWidgetItem()

        if not label_saved:
            label.setText('Well_{}'.format(row_count))  # Default well label is 'Well_[row_number]'
        else:
            label.setText(label_saved)
        location.setText('({:.0f}, {:.0f})'.format(well_location[0]/self._um2pix, well_location[1]/self._um2pix))

        self.screen.insert_table.setItem(row_count, 0, label)
        self.screen.insert_table.setItem(row_count, 1, location)

    def remove_item(self, location):
        """ Removes row from table based on well location. """
        location[0] /= self._um2pix
        location[1] /= self._um2pix
        location = '({:.0f}, {:.0f})'.format(location[0], location[1])

        for row_index in range(self.screen.insert_table.rowCount()):
            item = self.screen.insert_table.item(row_index, 1)
            item_location = item.text()
            if item_location == location:
                self.screen.insert_table.removeRow(row_index)
                break

    def draw_circle(self):
        self.screen.image_frame.draw_shape = 'CIRCLE'
        self.screen.circle_radius_input.setEnabled(True)
        self.screen.num_circles_horizontal_input.setEnabled(False)
        self.screen.num_circles_vertical_input.setEnabled(False)

    def draw_rectangle(self):
        self.screen.image_frame.draw_shape = 'RECT'
        self.screen.circle_radius_input.setEnabled(False)
        self.screen.num_circles_horizontal_input.setEnabled(False)
        self.screen.num_circles_vertical_input.setEnabled(False)

    def draw_array(self):
        self.screen.image_frame.draw_shape = 'ARRAY'
        self.screen.circle_radius_input.setEnabled(True)
        self.screen.num_circles_horizontal_input.setEnabled(True)
        self.screen.num_circles_vertical_input.setEnabled(True)

    def clear_object(self):
        self.screen.image_frame.draw_shape = 'REMOVE'
        self.screen.circle_radius_input.setEnabled(False)
        self.screen.num_circles_horizontal_input.setEnabled(False)
        self.screen.num_circles_vertical_input.setEnabled(False)

    def clear_area(self):
        self.screen.image_frame.draw_shape = 'RAREA'
        self.screen.circle_radius_input.setEnabled(False)
        self.screen.num_circles_horizontal_input.setEnabled(False)
        self.screen.num_circles_vertical_input.setEnabled(False)

    def select_file(self):
        file_path = QtWidgets.QFileDialog.getSaveFileName(self.screen, 'Select a file', os.getcwd(),
                                                          'INSERT(*.ins)')
        if file_path[0]:
            file_path = file_path[0]
        else:
            return

        if os.path.splitext(file_path)[1] != '.ins':
            BarracudaQt.ErrorMessageUI(error_message='Invalid File Extension')
            return

        self.screen.file_name.setText(file_path)

    def load_insert(self):
        open_file_path = QtWidgets.QFileDialog.getOpenFileNames(self.screen, 'Choose previous session',
                                                                os.getcwd(), 'INSERT(*.ins)')
        if open_file_path[0]:
            open_file_path = open_file_path[0][0]
        else:
            return

        if os.path.splitext(open_file_path)[1] != '.ins':
            BarracudaQt.ErrorMessageUI(error_message='Invalid file chosen')
            return

        with open(open_file_path, 'rb') as open_file:
            try:
                self.insert = pickle.load(open_file)
            except pickle.UnpicklingError:
                message = 'Could not read in data from {}'.format(open_file_path)
                BarracudaQt.ErrorMessageUI(message)
            else:
                self.screen.image_frame.clear()
                self.screen.insert_table.clearContents()
                for row in range(self.screen.insert_table.rowCount()):
                    self.screen.insert_table.removeRow(self.screen.insert_table.rowCount()-1)
                self.screen.file_name.setText(open_file_path)

                for well in self.insert.wells:
                    self.screen.image_frame.add_shape(well.shape, well.bound_box)
                    self.add_row(well.location, well.label)

    def save_insert(self):
        if not self.screen.file_name.text():
            saved_file_path = QtWidgets.QFileDialog.getSaveFileName(self.screen, 'Specify file',
                                                                    os.getcwd(), 'METHOD(*.met)')[0]
            if not saved_file_path:
                return
        else:
            saved_file_path = self.screen.file_name.text()

        self.create_insert()

        with open(saved_file_path, 'wb') as saved_file:
            try:
                pickle.dump(self.insert, saved_file)
            except TypeError:
                return

    def create_insert(self):
        row_count = self.screen.insert_table.rowCount()
        wells = []

        for row_index in range(row_count):
            location = self.screen.insert_table.item(row_index, 1)

            location = [float(x) * self._um2pix for x in location.text().rsplit('(')[1].rsplit(')')[0].rsplit(',')]
            label = self.screen.insert_table.item(row_index, 0).text()
            bounding_box = self.screen.image_frame.get_bounding_rect(location)
            shape = self.screen.image_frame.get_shape(location)

            new_well = Well(label=label, location=location, bounding_box=bounding_box, shape=shape)
            wells.append(new_well)

        self.insert = Insert(wells=wells)


class MethodScreenController:
    def __init__(self, screen, hardware, repository):
        self.screen = screen
        self.hardware = hardware
        self.repository = repository

        self._um2pix = 1 / 200
        self._mm2pix = 2
        self._selecting = False
        self._step_well = None
        self._form_data = []
        self._populating_table = False
        self._well_labels = ['None']

        self.screen.image_view.setSceneRect(0, 0, self.hardware.xy_stage_size[0] * self._um2pix,
                                            self.hardware.xy_stage_size[1] * self._um2pix)
        self.screen.image_frame.controller = self

        self.dialogs = {'Separate': BarracudaQt.SeparateDialog,
                        'Rinse': BarracudaQt.RinseDialog,
                        'Inject': BarracudaQt.InjectDialog}

        self.method = None
        self.insert = None

        self.add_step(self._well_labels, self._well_labels)
        self.set_callbacks()

    def set_callbacks(self):
        self.screen.select_file.released.connect(lambda: self.load_insert())
        self.screen.image_frame.selectionChanged.connect(lambda: self.selecting())
        self.screen.reload_button.released.connect(lambda: self.reload_insert())
        self.screen.save_file.released.connect(lambda: self.save_method())
        self.screen.select_file_save.released.connect(lambda: self.select_file())
        self.screen.load_file_method.released.connect(lambda: self.load_method())

    def selecting(self):
        if self.screen.image_frame.selectedItems():
            item = self.screen.image_frame.selectedItems()[0]
            if type(item) != QtWidgets.QGraphicsPixmapItem:
                location = tuple(item.boundingRect().getRect())
                for well in self.insert.wells:
                    if well.bound_box == location:
                        if self._selecting:
                            self._step_well.setCurrentText(well.label)
                            self._selecting = False
                        self.screen.well_label.setText(well.label)
                        self.screen.well_location.setText(str([x/self._um2pix for x in well.location]))
                        break

    def step_well_change(self, combobox):
        if combobox.currentText() == 'Select' and not self._populating_table:
            self._selecting = True
            self._step_well = combobox

    def add_step(self, inlets, outlets, action_input=None, inlet_input=None, outlet_input=None,
                 time_input=None, value_input=None, duration_input=None, summary_input=None):
        if not self._populating_table:
            self._form_data.extend([{}])
        actions = ['Select', 'Separate', 'Rinse', 'Inject']

        row_count = self.screen.insert_table.rowCount()
        self.screen.insert_table.insertRow(row_count)

        blank_time = QtWidgets.QTableWidgetItem()
        if time_input:
            blank_time.setText(time_input)
        self.screen.insert_table.setItem(row_count, 1, blank_time)

        blank_value = QtWidgets.QTableWidgetItem()
        if value_input:
            blank_value.setText(value_input)
        self.screen.insert_table.setItem(row_count, 3, blank_value)

        blank_duration = QtWidgets.QTableWidgetItem()
        if duration_input:
            blank_duration.setText(duration_input)
        self.screen.insert_table.setItem(row_count, 4, blank_duration)

        blank_summary = QtWidgets.QTableWidgetItem()
        if summary_input:
            blank_summary.setText(summary_input)
        self.screen.insert_table.setItem(row_count, 7, blank_summary)

        add_button = QtWidgets.QPushButton('+')
        add_button.setFixedWidth(38)
        add_button.released.connect(lambda: self.add_step(inlets, outlets))
        self.screen.insert_table.setCellWidget(row_count, 0, add_button)

        action_choices = QtWidgets.QComboBox()
        action_choices.addItems(actions)
        if action_input:
            action_choices.setCurrentText(action_input)
        action_choices.activated.connect(lambda: self.load_dialog(action_choices.currentText()))
        self.screen.insert_table.setCellWidget(row_count, 2, action_choices)

        inlet_choices = QtWidgets.QComboBox()
        inlet_choices.addItems(self._well_labels)
        if inlet_input:
            if inlet_input not in self._well_labels:
                inlet_choices.addItem(inlet_input)
            inlet_choices.setCurrentText(inlet_input)
        inlet_choices.activated.connect(lambda: self.step_well_change(inlet_choices))
        self.screen.insert_table.setCellWidget(row_count, 5, inlet_choices)

        outlet_choices = QtWidgets.QComboBox()
        outlet_choices.setEnabled(False)
        outlet_choices.addItems(self._well_labels)
        if outlet_input:
            if outlet_input not in self._well_labels:
                inlet_choices.addItem(outlet_input)
            outlet_choices.setCurrentText(outlet_input)
        outlet_choices.activated.connect(lambda: self.step_well_change(outlet_choices))
        self.screen.insert_table.setCellWidget(row_count, 6, outlet_choices)

        if row_count > 0:
            remove_button = QtWidgets.QPushButton('-')
            remove_button.setFixedWidth(38)
            remove_button.released.connect(lambda: self.remove_step())
            self.screen.insert_table.setCellWidget(row_count-1, 0, remove_button)

    def remove_step(self):
        current_row = self.screen.insert_table.currentRow()
        self._form_data.remove(self._form_data[current_row])
        self.screen.insert_table.removeRow(current_row)

    def set_step_conditions(self, dialog, dialog_data):
        """ Sets table values based on form data from dialog. """
        current_row = self.screen.insert_table.currentRow()

        data = {'Type': dialog}
        data.update({key: dialog_data[key]() for key in dialog_data.keys()})

        try:
            self._form_data[current_row] = data
        except IndexError:
            print('here?')
            self._form_data.extend([{}])
            self._form_data[current_row] = data

        summary = []
        value = ""

        if dialog == 'Separate':
            # Determine separation type and value.
            if data['SeparationTypeVoltageRadio']:
                summary += ['Voltage']
                value = '{} kV'.format(data['ValuesVoltageEdit'])

            elif data['SeparationTypeCurrentRadio']:
                summary += ['Current']
                value = '{} kV'.format(data['ValuesVoltageEdit'])

            elif data['SeparationTypePowerRadio']:
                summary += ['Power']
                value = '{} kV'.format(data['ValuesVoltageEdit'])

            elif data['SeparationTypePressureRadio']:
                summary += ['Pressure']
                value = '{} psi'.format(data['ValuesPressureEdit'])

            elif data['SeparationTypeVacuumRadio']:
                summary += ['Vacuum']
                value = '{} psi'.format(data['ValuesPressureEdit'])

            # Determine whether it is with pressure or vacuum.
            if data['SeparationTypeWithPressureCheck']:
                summary += ['With Pressure']

            elif data['SeparationTypeWithVacuumCheck']:
                summary += ['With Vacuum']

            # Determine whether the polarity is normal or reversed.
            if data['PolarityNormalRadio']:
                summary += ['Normal Polarity']

            elif data['PolarityReverseRadio']:
                summary += ['Reverse Polarity']

            # Get duration and ramp time.
            duration = '{} min'.format(data['ValuesDurationEdit'])
            summary += ['{} min Ramp'.format(data['ValuesRampTimeEdit'])]

        elif dialog == 'Rinse':
            # Get pressure type and value
            if data['PressureTypePressureRadio']:
                summary += ['Pressure']

            elif data['PressureTypeVacuumRadio']:
                summary += ['Vacuum']

            if data['PressureDirectionForwardRadio']:
                summary += ['Forward']

            elif data['PressureDirectionReverseRadio']:
                summary += ['Reverse']

            value = '{} psi'.format(data['ValuesPressureEdit'])
            duration = '{} min'.format(data['ValuesDurationEdit'])

        else:
            # Get injection type and value
            if data['InjectionTypeVoltageRadio']:
                summary += ['Voltage']

            elif data['InjectionTypePressureRadio']:
                summary += ['Pressure']

            elif data['InjectionTypeVacuumRadio']:
                summary += ['Vacuum']

            if data['PolarityNormalRadio']:
                summary += ['Normal']

            elif data['PolarityReverseRadio']:
                summary += ['Reverse']

            if data['PressureDirectionForwardRadio']:
                summary += ['Forward Pressure']

            elif data['PressureDirectionReverseRadio']:
                summary += ['Reverse Pressure']

            if data['SequenceTableAllowOverrideCheck']:
                summary += ['Override']

            value = '{} psi'.format(data['ValuesPressureEdit'])
            duration = '{} min'.format(data['ValuesDurationEdit'])

        s = ', '
        summary = s.join(summary)

        value_item = QtWidgets.QTableWidgetItem()
        duration_item = QtWidgets.QTableWidgetItem()
        summary_item = QtWidgets.QTableWidgetItem()
        value_item.setText(value)
        duration_item.setText(duration)
        summary_item.setText(summary)

        self.screen.insert_table.setItem(current_row, 3, value_item)
        self.screen.insert_table.setItem(current_row, 4, duration_item)
        self.screen.insert_table.setItem(current_row, 7, summary_item)

    def load_dialog(self, dialog_type):
        """ Loads the appropriate dialog based on user input in table. """
        if not self._populating_table:
            current_row = self.screen.insert_table.currentRow()
            inlet = self.screen.insert_table.cellWidget(current_row, 5).currentText()
            outlet = self.screen.insert_table.cellWidget(current_row, 6).currentText()
            if dialog_type != 'Select':  # Rinse, Inject or Separate (Select is default)
                self.dialogs[dialog_type](self.set_step_conditions, inlet, outlet)

    def load_insert(self):
        """ Prompts user for and loads an in insert file. """
        open_file_path = QtWidgets.QFileDialog.getOpenFileNames(self.screen, 'Choose previous session',
                                                                os.getcwd(), 'INSERT(*.ins)')
        if open_file_path[0]:  # Checks if user selected a file or exited.
            open_file_path = open_file_path[0][0]
        else:
            return

        if os.path.splitext(open_file_path)[1] != '.ins':  # Checks for appropriate extension
            BarracudaQt.ErrorMessageUI(error_message='Invalid file chosen')
            return

        with open(open_file_path, 'rb') as open_file:
            try:
                self.insert = pickle.load(open_file)
            except pickle.UnpicklingError:  # Errors due to file corruption or wrong files with right ext.
                message = 'Could not read in data from {}'.format(open_file_path)
                BarracudaQt.ErrorMessageUI(message)
            else:
                self.screen.image_frame.clear()  # Clear image frame for new insert.
                self.screen.file_name.setText(open_file_path)

                # for row in range(self.screen.insert_table.rowCount()):  # Clears the table
                #     self.screen.insert_table.removeRow(self.screen.insert_table.rowCount()-1)

                for well in self.insert.wells:  # Loads the new shapes onto the frame
                    self.screen.image_frame.add_shape(well.shape, well.bound_box)

                well_labels = ['None', 'Select']
                well_labels.extend([well.label for well in self.insert.wells])

                for row_index in range(self.screen.insert_table.rowCount()):
                    current_choice_inlet = self.screen.insert_table.cellWidget(row_index, 5).currentText()
                    current_choice_outlet = self.screen.insert_table.cellWidget(row_index, 6).currentText()

                    if current_choice_inlet not in well_labels:
                        well_labels.extend(current_choice_inlet)
                    if current_choice_outlet not in well_labels:
                        well_labels.extend(current_choice_outlet)

                    self.screen.insert_table.cellWidget(row_index, 5).clear()
                    self.screen.insert_table.cellWidget(row_index, 6).clear()
                    self.screen.insert_table.cellWidget(row_index, 5).addItems(well_labels)
                    self.screen.insert_table.cellWidget(row_index, 6).addItems(well_labels)
                    self.screen.insert_table.cellWidget(row_index, 5).setCurrentText(current_choice_inlet)
                    self.screen.insert_table.cellWidget(row_index, 6).setCurrentText(current_choice_outlet)

                self._well_labels = well_labels

    def reload_insert(self):
        """ Reloads the current insert file. """
        open_file_path = self.screen.file_name.text()
        if not open_file_path:  # If there is no current file then return.
            return

        if os.path.splitext(open_file_path)[1] != '.ins':  # Checks current file for correct extension.
            BarracudaQt.ErrorMessageUI(error_message='Invalid file chosen')
            return

        with open(open_file_path, 'rb') as open_file:
            try:
                self.insert = pickle.load(open_file)
            except pickle.UnpicklingError:  # Errors due to file corruption or wrong files with right ext.
                message = 'Could not read in data from {}'.format(open_file_path)
                BarracudaQt.ErrorMessageUI(message)
            else:
                self.screen.image_frame.clear()

                for well in self.insert.wells:
                    self.screen.image_frame.add_shape(well.shape, well.bound_box)

                # Keep old steps but add new well labels to inlet and outlet choices.
                well_labels = ['None', 'Select']
                well_labels.extend([well.label for well in self.insert.wells])

                for row_index in range(self.screen.insert_table.rowCount()):
                    current_choice_inlet = self.screen.insert_table.cellWidget(row_index, 5).currentText()
                    current_choice_outlet = self.screen.insert_table.cellWidget(row_index, 6).currentText()

                    if current_choice_inlet not in well_labels:
                        well_labels.extend(current_choice_inlet)
                    if current_choice_outlet not in well_labels:
                        well_labels.extend(current_choice_outlet)

                    self.screen.insert_table.cellWidget(row_index, 5).clear()
                    self.screen.insert_table.cellWidget(row_index, 6).clear()
                    self.screen.insert_table.cellWidget(row_index, 5).addItems(well_labels)
                    self.screen.insert_table.cellWidget(row_index, 6).addItems(well_labels)
                    self.screen.insert_table.cellWidget(row_index, 5).setCurrentText(current_choice_inlet)
                    self.screen.insert_table.cellWidget(row_index, 6).setCurrentText(current_choice_outlet)

                self._well_labels = well_labels

    def load_method(self):
        """ Prompts the user for and loads a method file. """
        open_file_path = QtWidgets.QFileDialog.getOpenFileNames(self.screen, 'Choose previous session',
                                                                os.getcwd(), 'METHOD(*.met)')
        if open_file_path[0]:
            open_file_path = open_file_path[0][0]
        else:
            return

        if os.path.splitext(open_file_path)[1] != '.met':
            message = 'Invalid file chosen.'
            BarracudaQt.ErrorMessageUI(message)
            return

        self.screen.file_name_save.setText(open_file_path)

        with open(open_file_path, 'rb') as open_file:
            try:
                data = pickle.load(open_file)
            except pickle.UnpicklingError:
                message = 'Could not read in data from {}.'.format(open_file_path)
                BarracudaQt.ErrorMessageUI(message)
            else:
                self.method = data
                self.populate_table(data)

    def save_method(self):
        """ Prompts the user for and saves current method to a file path. """
        saved_file_path = self.screen.file_name_save.text()

        if not saved_file_path:  # Checks if a file path was actually specified.
            self.select_file()
            saved_file_path = self.screen.file_name_save.text()

            if not saved_file_path:
                return

        self.compile_method()  # Compile all step information into a method object

        with open(saved_file_path, 'wb') as saved_file:
            try:
                pickle.dump(self.method, saved_file)
            except pickle.PicklingError:  # Shouldn't occur unless the user really screws up.
                BarracudaQt.ErrorMessageUI(error_message='Could not save the method.')

    def select_file(self):
        file_path = QtWidgets.QFileDialog.getSaveFileName(self.screen, 'Select a file', os.getcwd(),
                                                          'METHOD(*.met)')
        if file_path[0]:
            file_path = file_path[0]
        else:
            return

        if os.path.splitext(file_path)[1] != '.met':
            BarracudaQt.ErrorMessageUI(error_message='Invalid File Extension')
            return

        self.screen.file_name_save.setText(file_path)

    def populate_table(self, method):
        self._populating_table = True

        self.screen.insert_table.clearContents()
        for row in range(self.screen.insert_table.rowCount()):
            self.screen.insert_table.removeRow(self.screen.insert_table.rowCount() - 1)

        self._form_data = []
        for step in method.steps:
            if step:
                self.add_step([step['Inlet']], [step['Outlet']], action_input=step['Type'], inlet_input=step['Inlet'],
                              outlet_input=step['Outlet'], time_input=step['Time'], value_input=step['Value'],
                              duration_input=step['Duration'], summary_input=step['Summary'])
                self._form_data += [step]

        self._populating_table = False

    def compile_method(self):
        """ Compiles all step information into a method object. """
        n = 0
        for data in self._form_data:
            if 'Type' in data.keys():
                data['Inlet'] = self.screen.insert_table.cellWidget(n, 5).currentText()
                data['Outlet'] = self.screen.insert_table.cellWidget(n, 6).currentText()
                data['Time'] = self.screen.insert_table.item(n, 1).text()
                data['Summary'] = self.screen.insert_table.item(n, 7).text()
                data['Value'] = self.screen.insert_table.item(n, 3).text()
                data['Duration'] = self.screen.insert_table.item(n, 4).text()
                n += 1

        self.method = Method(steps=self._form_data)


class SequenceScreenController:
    def __init__(self, screen, hardware, repository):
        self.screen = screen
        self.hardware = hardware
        self.repository = repository

        self._set_callbacks()
        self.add_row()

    def _set_callbacks(self):
        pass

    def add_row(self, filename=None, inlet=None, duration=None, sample=None, method=None):
        row_count = self.screen.method_table.rowCount()
        self.screen.method_table.insertRow(row_count)

        if row_count > 0:
            remove_button = QtWidgets.QPushButton('-')
            remove_button.setFixedWidth(38)
            remove_button.released.connect(lambda: self.remove_method())
            self.screen.method_table.setCellWidget(row_count-1, 0, remove_button)

        add_button = QtWidgets.QPushButton('+')
        add_button.setFixedWidth(38)
        add_button.released.connect(lambda: self.add_method())
        self.screen.method_table.setCellWidget(row_count, 0, add_button)

        sample_inject_inlet = QtWidgets.QTableWidgetItem()
        sample_inject_inlet.setText(inlet)
        self.screen.method_table.setItem(row_count, 1, sample_inject_inlet)

        sample_inject_duration = QtWidgets.QTableWidgetItem()
        sample_inject_duration.setText(duration)
        self.screen.method_table.setItem(row_count, 2, sample_inject_duration)

        sample_item = QtWidgets.QTableWidgetItem()
        sample_item.setText(sample)
        self.screen.method_table.setItem(row_count, 3, sample_item)

        method_item = QtWidgets.QTableWidgetItem()
        method_item.setText(method)
        self.screen.method_table.setItem(row_count, 4, method_item)

        filename_item = QtWidgets.QTableWidgetItem()
        filename_item.setText(filename)
        self.screen.method_table.setItem(row_count, 5, filename_item)

        sample_amount = QtWidgets.QTableWidgetItem()
        self.screen.method_table.setItem(row_count, 6, sample_amount)

    def add_method(self):
        open_file_path = QtWidgets.QFileDialog.getOpenFileNames(self.screen, 'Choose previous session',
                                                                os.getcwd(), 'METHOD(*.met)')
        if open_file_path[0]:  # Check if user selected a file or just exited.
            open_file_path = open_file_path[0][0]
        else:
            return

        if os.path.splitext(open_file_path)[1] != '.met':  # Check file for correct extension.
            message = 'Invalid file chosen.'
            BarracudaQt.ErrorMessageUI(message)
            return

        with open(open_file_path, 'rb') as open_file:
            try:
                data = pickle.load(open_file)
            except pickle.UnpicklingError:  # Should not occur unless user really screws up.
                message = 'Could not read in data from {}.'.format(open_file_path)
                BarracudaQt.ErrorMessageUI(message)
            else:
                self.add_row(filename=os.path.split(open_file_path)[1], method=open_file_path)

    def remove_method(self):
        current_row = self.screen.method_table.currentRow()
        self.screen.method_table.removeRow(current_row)

    def load_sequence(self):
        pass

    def save_sequence(self):
        pass


class RunScreenController:
    _stop = threading.Event()
    _update_delay = 0.125
    _xy_step_size = 1/1000  # µm

    _stop.set()
    _stop.clear()

    def __init__(self, screen, hardware, repository):
        self.screen = screen
        self.hardware = hardware
        self.repository = repository

        self._start_updating_display()
        self._set_callbacks()

    def _set_callbacks(self):
        if self.hardware.xy_stage_control:
            # fixme set callbacks for arrow keys? Create a checkbox in the xy form box
            self.screen.xy_up.released.connect(lambda: self.set_y(step=self.screen.xy_step_size.value()))
            self.screen.xy_down.released.connect(lambda: self.set_y(step=-self.screen.xy_step_size.value()))
            self.screen.xy_right.released.connect(lambda: self.set_x(step=self.screen.xy_step_size.value()))
            self.screen.xy_left.released.connect(lambda: self.set_x(step=-self.screen.xy_step_size.value()))
            self.screen.xy_x_value.selected.connect(lambda: self._value_display_interact(selected=True))
            self.screen.xy_y_value.selected.connect(lambda: self._value_display_interact(selected=True))
            self.screen.xy_x_value.unselected.connect(lambda: self._value_display_interact(selected=False))
            self.screen.xy_y_value.unselected.connect(lambda: self._value_display_interact(selected=False))
            self.screen.xy_x_value.returnPressed.connect(lambda: self.set_x(x=float(self.screen.xy_x_value.text())))
            self.screen.xy_y_value.returnPressed.connect(lambda: self.set_y(y=float(self.screen.xy_y_value.text())))
            self.screen.xy_set_origin.released.connect(lambda: self.set_origin())
            self.screen.xy_origin.released.connect(lambda: self.origin())
            self.screen.xy_stop.released.connect(lambda: self.stop_xy_stage())

        if self.hardware.objective_control:
            self.screen.objective_up.released.connect(lambda: self.set_objective(step=self.screen.objective_step_size.value()))
            self.screen.objective_down.released.connect(lambda: self.set_objective(step=-self.screen.objective_step_size.value()))
            self.screen.objective_value.returnPressed.connect(lambda: self.set_objective(height=float(self.screen.objective_value.text())))
            self.screen.objective_stop.released.connect(lambda: self.stop_objective())
            self.screen.objective_value.selected.connect(lambda: self._value_display_interact(selected=True))
            self.screen.objective_value.unselected.connect(lambda: self._value_display_interact(selected=False))

        if self.hardware.outlet_control:
            self.screen.outlet_up.released.connect(lambda: self.set_outlet(step=self.screen.outlet_step_size.value()))
            self.screen.outlet_down.released.connect(lambda: self.set_outlet(step=-self.screen.outlet_step_size.value()))
            self.screen.outlet_value.returnPressed.connect(lambda: self.set_outlet(height=float(self.screen.outlet_value.text())))
            self.screen.outlet_stop.released.connect(lambda: self.stop_outlet())
            self.screen.outlet_value.selected.connect(lambda: self._value_display_interact(selected=True))
            self.screen.outlet_value.unselected.connect(lambda: self._value_display_interact(selected=False))

            self.screen.pressure_rinse_state.positive_selected.connect(lambda: self.rinse_pressure())
            self.screen.pressure_off.released.connect(lambda: self.stop_pressure())

        if self.hardware.z_stage_control:
            self.screen.z_up.released.connect(lambda: self.set_z(step=self.screen.z_step_size.value()))
            self.screen.z_down.released.connect(lambda: self.set_z(step=-self.screen.z_step_size.value()))
            self.screen.z_value.returnPressed.connect(lambda: self.set_z(height=float(self.screen.z_value.text())))
            self.screen.z_stop.released.connect(lambda: self.stop_z_stage())
            self.screen.z_value.selected.connect(lambda: self._value_display_interact(selected=True))
            self.screen.z_value.unselected.connect(lambda: self._value_display_interact(selected=False))

        if self.hardware.laser_control:
            self.screen.laser_pfn.valueChanged.connect(lambda: self.set_pfn(value=self.screen.laser_pfn.value()))
            self.screen.laser_attenuation.valueChanged.connect(lambda: self.set_attenuation(value=self.screen.laser_attenuation.value()))
            self.screen.laser_burst_count.valueChanged.connect(lambda: self.set_burst(count=self.screen.laser_burst_count.value()))
            self.screen.laser_fire.released.connect(lambda: self.fire_laser())
            self.screen.laser_standby.released.connect(lambda: self.laser_on())
            self.screen.laser_off.released.connect(lambda: self.stop_laser())

        if self.hardware.daq_board_control:
            self.screen.voltage_value.valueChanged.connect(lambda: self.set_voltage(value=self.screen.voltage_value.value()))
            self.screen.voltage_on.released.connect(lambda: self.voltage_on())
            self.screen.voltage_off.released.connect(lambda: self.stop_voltage())

        self.screen.all_stop.released.connect(lambda: self.stop_all())

        self.screen.start_sequence.released.connect(lambda: self.start_sequence())
        self.screen.pause_sequence.released.connect(lambda: self.pause_sequence())
        self.screen.stop_sequence.released.connect(lambda: self.end_sequence())
        self.screen.add_method.released.connect(lambda: self.add_method())
        self.screen.remove_method.released.connect(lambda: self.remove_method())

    def _start_updating_display(self):
        if self.hardware.xy_stage_control:
            value = self.hardware.xy_stage_control.read_xy()
            self.screen.xy_x_value.setText("{:.3f}".format(float(value[0])))
            self.screen.xy_y_value.setText("{:.3f}".format(float(value[1])))

        if self.hardware.z_stage_control:
            value = self.hardware.z_stage_control.read_z()
            self.screen.z_value.setText("{:.3f}".format(float(value)))

        if self.hardware.outlet_control:
            value = self.hardware.outlet_control.read_z()
            self.screen.outlet_value.setText("{:.3f}".format(float(value)))

        if self.hardware.objective_control:
            value = self.hardware.objective_control.read_z()
            self.screen.objective_value.setText("{:.3f}".format(float(value)))

        threading.Thread(target=self._update_stages).start()

    def _value_display_interact(self, selected=False):
        logging.info(selected)
        if selected:
            self._stop.set()
        else:
            self._stop.clear()

    def _update_stages(self):
        while True:
            if self._stop.is_set():
                time.sleep(4*self._update_delay)
                continue

            if self.hardware.xy_stage_control:
                prev = self.hardware.xy_stage_control.position
                value = self.hardware.xy_stage_control.read_xy()
                if value != prev:
                    self.screen.xy_x_value.setText("{:.3f}".format(float(value[0])))
                    self.screen.xy_y_value.setText("{:.3f}".format(float(value[1])))
                time.sleep(self._update_delay)

            if self.hardware.z_stage_control:
                prev = self.hardware.z_stage_control.pos
                value = str(self.hardware.z_stage_control.read_z())
                if value != prev:
                    self.screen.z_value.setText("{:.3f}".format(float(value)))
                time.sleep(self._update_delay)

            if self.hardware.objective_control:
                prev = self.hardware.objective_control.pos
                value = str(self.hardware.objective_control.read_z())
                if value != prev:
                    self.screen.objective_value.setText("{:.3f}".format(float(value)))
                time.sleep(self._update_delay)

            if self.hardware.outlet_control:
                prev = self.hardware.outlet_control.pos
                value = str(self.hardware.outlet_control.read_z())
                if value != prev:
                    self.screen.outlet_value.setText("{:.3f}".format(float(value)))
                time.sleep(self._update_delay)

    def set_origin(self):
        pass

    def origin(self):
        pass

    def set_x(self, x=None, step=None):
        if step:
            self.hardware.xy_stage_control.set_rel_x(step*self._xy_step_size)
        elif x:
            self.hardware.xy_stage_control.set_x(x)

        value = self.hardware.xy_stage_control.read_xy()
        self.screen.xy_x_value.setText("{:.3f}".format(float(value[0])))

        if self._stop.is_set():
            self._stop.clear()

    def set_y(self, y=None, step=None):
        if step:
            self.hardware.xy_stage_control.set_rel_y(step*self._xy_step_size)
        elif y:
            self.hardware.xy_stage_control.set_y(y)

        value = self.hardware.xy_stage_control.read_xy()
        self.screen.xy_y_value.setText("{:.3f}".format(float(value[1])))

        if self._stop.is_set():
            self._stop.clear()

    def set_z(self, height=None, step=None):
        if step:
            self.hardware.z_stage_control.set_rel_z(step)
        elif height:
            self.hardware.z_stage_control.set_z(height)

        if self._stop.is_set():
            self._stop.clear()

    def set_objective(self, height=None, step=None):
        if step:
            self.hardware.objective_control.set_rel_z(step)
        elif height:
            self.hardware.objective_control.set_z(height)

        if self._stop.is_set():
            self._stop.clear()

    def set_outlet(self, height=None, step=None):
        if step:
            self.hardware.outlet_control.set_rel_z(step)
        elif height:
            self.hardware.outlet_control.set_z(height)

        if self._stop.is_set():
            self._stop.clear()

    def set_voltage(self, value=None):
        pass

    def set_pfn(self, value=None):
        pass

    def set_attenuation(self, value=None):
        pass

    def set_burst(self, count=None):
        pass

    def stop_xy_stage(self):
        pass

    def stop_outlet(self):
        pass

    def stop_objective(self):
        pass

    def stop_z_stage(self):
        pass

    def stop_pressure(self):
        pass

    def stop_laser(self):
        pass

    def stop_voltage(self):
        pass

    def stop_all(self):
        # Done in order of "If the next one would be the last one that executes properly, which would I want it to be"
        self.stop_laser()
        self.stop_voltage()
        self.stop_xy_stage()
        self.stop_objective()
        self.stop_z_stage()
        self.stop_outlet()
        self.stop_pressure()

        # fixme
        self.hardware.xy_stage_control.close()
        # self.hardware.image_control.close()
        sys.exit()

    def rinse_pressure(self):
        logging.info('Rinse')


    def fire_laser(self):
        pass

    def voltage_on(self):
        pass

    def laser_on(self):
        pass

    def add_method(self):
        pass

    def remove_method(self):
        pass

    def start_sequence(self):
        pass

    def pause_sequence(self):
        pass

    def end_sequence(self):
        pass


class DataScreenController:
    def __init__(self, screen, hardware, repository):
        self.screen = screen
        self.hardware = hardware
        self.repository = repository


class SystemScreenController:
    def __init__(self, screen, hardware, repository):
        self.screen = screen
        self.hardware = hardware
        self.repository = repository


pc = ProgramController()
