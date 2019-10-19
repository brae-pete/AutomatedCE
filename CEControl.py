# Standard library modules
import sys
import os
import pickle
import threading
import logging
import time
import random
import datetime
# Custom modules for CE
import CESystems  # Hardware system classes
import CEObjects  # CE-specific data structures
import CEGraphic  # GUI classes
import FocusTesting
import Detection  # Cell Detection
import Lysis

# Installed modules
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np

from BarracudaQt import CERunLogic

HOME = False


# fixme have the program not load and start the systems on startup (for obvious reasons)


# Control Classes
class ProgramController:
    """Builds the pieces of the program and puts them together. Ooooooh we could probably just make this a function
    now that I think about it. Class is cooler though. hmmm"""

    def __init__(self):
        # Initialize system model, system hardware and the GUI
        self.repository = CEObjects.CERepository()
        self.hardware = CESystems.NikonEclipseTi()
        self.hardware.start_system()

        app = QtWidgets.QApplication(sys.argv)
        self.program_window = CEGraphic.MainWindow(self)

        # Connect the views to the controllers.
        self.gs_screen = self.program_window.getting_started_screen
        self.gs_control = GettingStartedScreenController(self.gs_screen, self.hardware, self.repository, self)

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

    def close_program(self):
        self.r_control.stop_all()


class GettingStartedScreenController:
    def __init__(self, screen, hardware, repository, parent):
        self.screen = screen
        self.hardware = hardware
        self.repository = repository
        self.parent = parent

        self._set_callbacks()

    def _set_callbacks(self):
        # self.screen.options.load_data.released.connect(lambda: self.load_data())
        # self.screen.options.load_method.released.connect(lambda: self.load_method())
        # self.screen.options.load_insert.released.connect(lambda: self.load_insert())
        # self.screen.options.load_sequence.released.connect(lambda: self.load_sequence())
        # self.screen.options.new_data.released.connect(lambda: self.new_data())
        # self.screen.options.new_method.released.connect(lambda: self.new_method())
        # self.screen.options.new_insert.released.connect(lambda: self.new_insert())
        # self.screen.options.new_sequence.released.connect(lambda: self.new_sequence())
        pass

    def _select_file(self, ext, ext_label):
        file_path = QtWidgets.QFileDialog.getSaveFileName(self.screen, 'Select a file', os.getcwd(),
                                                          '{}(*{})'.format(ext_label, ext))
        if file_path[0]:
            file_path = file_path[0]
        else:
            return None

        if os.path.splitext(file_path)[1] != ext:
            CEGraphic.ErrorMessageUI(error_message='Invalid File Extension')
            return None

        return file_path

    def load_data(self):
        data_file = self._select_file('.dat', 'DATA')

    def load_insert(self):
        insert_file = self._select_file('.ins', 'INSERT')

    def load_method(self):
        method_file = self._select_file('.met', 'METHOD')

    def load_sequence(self):
        sequence_file = self._select_file('.seq', 'SEQUENCE')

    def load_system(self):
        pass

    def new_data(self):
        self.parent.program_window.tabBar().setCurrentIndex(2)

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

        self._um2pix = 1 / 300
        self._mm2pix = 3
        self._stage_offset = self.hardware.xy_stage_offset
        self._stage_inversion = self.hardware.xy_stage_inversion
        self._initial = True
        self._initial_point = None

        self.screen.image_view.setSceneRect(0, 0, 584, 584)
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
        self.screen.init_grid_action.triggered.connect(lambda: self._calibrate_xy())
        self.screen.insert_table.currentCellChanged.connect(lambda: self.highlight_well())
        self.screen.select_file.released.connect(lambda: self.select_file())
        self.screen.save_file.released.connect(lambda: self.save_insert())

    def _calibrate_xy(self):
        self._stage_offset = self.hardware.get_xy()

    def highlight_well(self):
        """ Prompts the screen to highlight the well whose cell in the table is selected. """
        location = self.screen.insert_table.item(self.screen.insert_table.currentRow(), 1)
        if location:  # This check is necessary in case the last well is deleted.
            # Convert from the '({}, {})' format to [f, f]
            try:
                event_location = [float(x) for x in location.text().rsplit('(')[1].rsplit(')')[0].rsplit(',')]
                location = [(self.hardware.xy_stage_size[0] - event_location[0]) * self._um2pix,
                            (self.hardware.xy_stage_size[1] - event_location[1]) * self._um2pix]
            except ValueError:  # The user changed the table contents to an invalid coordinate
                CEGraphic.ErrorMessageUI(error_message='Well location is invalid.')
            else:
                self.screen.image_frame.highlight_item(location)

    def joystick(self):
        """ Prompts shapes to be created in the view via the joystick method. """
        # The event we are sending holds the current coordinates of the stage and converts them to pixel
        event_location = self.hardware.get_xy()
        logging.info(event_location)
        event_location = [event_location[0] - self.hardware.xy_stage_offset[0],
                          event_location[1] - self.hardware.xy_stage_offset[1]]
        logging.info(event_location)
        logging.info(self.hardware.xy_stage_offset)


        # We want the pixel location of the objective relative to the stage.
        event = [(self.hardware.xy_stage_size[0] - event_location[0]*self._stage_inversion[0]) * self._um2pix,
                 (self.hardware.xy_stage_size[1] - event_location[1]*self._stage_inversion[1]) * self._um2pix]
        logging.info(event)

        # If the user is trying to create and array or circle but hasn't specified radius, simply throw error.
        if not self.screen.circle_radius_input.text() and self.screen.image_frame.draw_shape != 'RECT':
            CEGraphic.ErrorMessageUI(error_message='Radius not specified.')
            return

        if self.screen.image_frame.draw_shape == 'CIRCLE':  # Only need to know radius of well.
            event.append(float(self.screen.circle_radius_input.text()) * self._mm2pix)

        elif self.screen.image_frame.draw_shape == 'ARRAY':  # Need to know dimensions of array and radius of wells.
            event.append(float(self.screen.circle_radius_input.text()) * self._mm2pix)
            event.append(float(self.screen.num_circles_horizontal_input.text()))
            event.append(float(self.screen.num_circles_vertical_input.text()))

        self.add_wells(event_location)

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

    def add_wells(self, location):
        """Adds well at location to table."""
        if self.screen.image_frame.draw_shape == 'CIRCLE':
            self._add_row(location, pixels=False)

        elif self.screen.image_frame.draw_shape == 'RECT':
            if self._initial:
                self._initial_point = location
            else:
                location = [self._initial_point[0] + (location[0] - self._initial_point[0]) / 2,
                            self._initial_point[1] + (location[1] - self._initial_point[1]) / 2]
                self._add_row(location, pixels=False)

        elif self.screen.image_frame.draw_shape == 'ARRAY':
            if self._initial:
                self._initial_point = location
            else:
                x = self._initial_point[0]
                y = self._initial_point[1]
                dx = (location[0] - self._initial_point[0]) / (int(self.screen.num_circles_horizontal_input.text()) - 1)
                dy = (location[1] - self._initial_point[1]) / (int(self.screen.num_circles_vertical_input.text()) - 1)
                for _ in range(int(self.screen.num_circles_horizontal_input.text())):
                    for _ in range(int(self.screen.num_circles_vertical_input.text())):
                        self._add_row([x, y], pixels=False)
                        logging.info('adding row with {}'.format([x, y]))
                        y += dy
                    y = self._initial_point[1]
                    x += dx

    def _add_row(self, well_location, label_saved=None, pixels=True):
        """ Adds a row to the table with the well label and location. """
        row_count = self.screen.insert_table.rowCount()
        self.screen.insert_table.insertRow(row_count)

        label = QtWidgets.QTableWidgetItem()
        location = QtWidgets.QTableWidgetItem()

        if not label_saved:
            label.setText('Well_{}'.format(row_count))  # Default well label is 'Well_[row_number]'
        else:
            label.setText(label_saved)
        if pixels:
            location.setText(
                '({:.0f}, {:.0f})'.format(well_location[0] / self._um2pix, well_location[1] / self._um2pix))
        else:
            location.setText('({:.0f}, {:.0f})'.format(well_location[0], well_location[1]))

        self.screen.insert_table.setItem(row_count, 0, label)
        self.screen.insert_table.setItem(row_count, 1, location)

    def remove_item(self, location):
        """ Removes row from table based on well location. """
        location[0] = (location[0] / self._um2pix - self._stage_offset[0]) / self._stage_inversion[0]
        location[1] = (location[1] / self._um2pix + self._stage_offset[1]) / self._stage_inversion[1]
        location = '({:.0f}, {:.0f})'.format(location[0], location[1])

        for row_index in range(self.screen.insert_table.rowCount()):
            item = self.screen.insert_table.item(row_index, 1)
            item_location = item.text()
            if item_location == location:
                self.screen.insert_table.removeRow(row_index)
                break

    def draw_circle(self):
        """Adjusts settings and inputs on screen for drawing a circle."""
        self.screen.image_frame.draw_shape = 'CIRCLE'
        self.screen.circle_radius_input.setEnabled(True)
        self.screen.num_circles_horizontal_input.setEnabled(False)
        self.screen.num_circles_vertical_input.setEnabled(False)

    def draw_rectangle(self):
        """Adjusts settings and inputs on screen for drawing a rectangle."""
        self.screen.image_frame.draw_shape = 'RECT'
        self.screen.circle_radius_input.setEnabled(False)
        self.screen.num_circles_horizontal_input.setEnabled(False)
        self.screen.num_circles_vertical_input.setEnabled(False)

    def draw_array(self):
        """Adjusts settings and inputs on screen for drawing an array of circles."""
        self.screen.image_frame.draw_shape = 'ARRAY'
        self.screen.circle_radius_input.setEnabled(True)
        self.screen.num_circles_horizontal_input.setEnabled(True)
        self.screen.num_circles_vertical_input.setEnabled(True)

    def clear_object(self):
        """Adjusts settings and inputs on screen for deleting an object."""
        self.screen.image_frame.draw_shape = 'REMOVE'
        self.screen.circle_radius_input.setEnabled(False)
        self.screen.num_circles_horizontal_input.setEnabled(False)
        self.screen.num_circles_vertical_input.setEnabled(False)

    def clear_area(self):
        """Adjusts settings and inputs on screen for clearing a specified area."""
        self.screen.image_frame.draw_shape = 'RAREA'
        self.screen.circle_radius_input.setEnabled(False)
        self.screen.num_circles_horizontal_input.setEnabled(False)
        self.screen.num_circles_vertical_input.setEnabled(False)

    def select_file(self):
        """Prompts user for insert file to eventually save to."""
        file_path = QtWidgets.QFileDialog.getSaveFileName(self.screen, 'Select a file', os.getcwd(),
                                                          'INSERT(*.ins)')
        if file_path[0]:
            file_path = file_path[0]
        else:
            return

        if os.path.splitext(file_path)[1] != '.ins':
            CEGraphic.ErrorMessageUI(error_message='Invalid File Extension')
            return

        self.screen.file_name.setText(file_path)

    def load_insert(self):
        """Prompts user for an insert file and loads the wells from that insert."""
        open_file_path = QtWidgets.QFileDialog.getOpenFileNames(self.screen, 'Choose previous session',
                                                                os.getcwd(), 'INSERT(*.ins)')
        if open_file_path[0]:
            open_file_path = open_file_path[0][0]
        else:
            return

        if os.path.splitext(open_file_path)[1] != '.ins':
            CEGraphic.ErrorMessageUI(error_message='Invalid file chosen')
            return

        with open(open_file_path, 'rb') as open_file:
            try:
                self.insert = pickle.load(open_file)
            except pickle.UnpicklingError:
                message = 'Could not read in data from {}'.format(open_file_path)
                CEGraphic.ErrorMessageUI(message)
            else:
                self.screen.image_frame.clear()
                self.screen.insert_table.clearContents()
                for row in range(self.screen.insert_table.rowCount()):
                    self.screen.insert_table.removeRow(self.screen.insert_table.rowCount() - 1)
                self.screen.file_name.setText(open_file_path)

                for well in self.insert.wells:
                    self.screen.image_frame.add_shape(well.shape, well.bound_box)
                    self._add_row(well.location, well.label, pixels=False)

    def save_insert(self):
        """Saves current insert in the previously selected file or opens a prompt if one is not selected."""
        if not self.screen.file_name.text():
            saved_file_path = QtWidgets.QFileDialog.getSaveFileName(self.screen, 'Specify file',
                                                                    os.getcwd(), 'INSERT(*.ins)')[0]
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
        """Creates an insert object based on the current well objects."""
        row_count = self.screen.insert_table.rowCount()
        wells = []

        for row_index in range(row_count):
            location = self.screen.insert_table.item(row_index, 1)

            event_location = [float(x) for x in location.text().rsplit('(')[1].rsplit(')')[0].rsplit(',')]
            pixel_location = [(self.hardware.xy_stage_size[0] - event_location[0]*self._stage_inversion[0]) * self._um2pix,
                              (self.hardware.xy_stage_size[1] - event_location[1]*self._stage_inversion[1]) * self._um2pix]

            label = self.screen.insert_table.item(row_index, 0).text()
            bounding_box = self.screen.image_frame.get_bounding_rect(pixel_location)
            shape = self.screen.image_frame.get_shape(pixel_location)

            new_well = CEObjects.Well(label=label, location=event_location, bounding_box=bounding_box, shape=shape)
            wells.append(new_well)

        self.insert = CEObjects.Insert(wells=wells, label='Default')


class MethodScreenController:
    def __init__(self, screen, hardware, repository):
        self.screen = screen
        self.hardware = hardware
        self.repository = repository

        self._um2pix = 1 / 300
        self._mm2pix = 3
        self._stage_offset = self.hardware.xy_stage_offset
        self._stage_inversion = self.hardware.xy_stage_inversion
        self._selecting = False
        self._step_well = None
        self._form_data = []
        self._populating_table = False
        self._well_labels = ['None']

        self.screen.image_view.setSceneRect(0, 0, 512, 512)
        self.screen.image_frame.controller = self

        self.dialogs = {'Separate': CEGraphic.SeparateDialog,
                        'Rinse': CEGraphic.RinseDialog,
                        'Inject': CEGraphic.InjectDialog}

        self.method = None
        self.insert = None

        self.add_step(self._well_labels, self._well_labels)
        self._set_callbacks()

    def _set_callbacks(self):
        """Assigns callback functions to widgets and signals in the screen."""
        self.screen.select_file.released.connect(lambda: self.load_insert())
        self.screen.image_frame.selectionChanged.connect(lambda: self.selecting())
        self.screen.reload_button.released.connect(lambda: self.reload_insert())
        self.screen.save_file.released.connect(lambda: self.save_method())
        self.screen.select_file_save.released.connect(lambda: self.select_file())
        self.screen.load_file_method.released.connect(lambda: self.load_method())

    def selecting(self):
        """If the user is selecting an inlet for the step this function assigns the selected inlet."""
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
                        self.screen.well_location.setText(str(well.location))
                        break

    def step_well_change(self, combobox):
        """Handles the user selecting 'Select' as an inlet option, setting appropriate variables."""
        if combobox.currentText() == 'Select' and not self._populating_table:
            self._selecting = True
            self._step_well = combobox

    def add_step(self, inlets, outlets, action_input=None, inlet_input=None, outlet_input=None,
                 time_input=None, value_input=None, duration_input=None, summary_input=None,
                 inlet_travel_input=None, outlet_travel_input=None):
        """Adds a new step to the table for the user to fill out."""
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

        inlet_travel = QtWidgets.QDoubleSpinBox()
        inlet_travel.setMaximum(25)
        inlet_travel.setMinimum(0)
        if inlet_travel_input:
            inlet_travel.setValue(inlet_travel_input)
        else:
            inlet_travel.setValue(0)
        inlet_travel.setSuffix('mm')
        self.screen.insert_table.setCellWidget(row_count, 7, inlet_travel)

        outlet_travel = QtWidgets.QDoubleSpinBox()
        outlet_travel.setMaximum(25)
        outlet_travel.setMinimum(-25)
        if outlet_travel_input:
            outlet_travel.setValue(outlet_travel_input)
        else:
            outlet_travel.setValue(0)
        outlet_travel.setSuffix('cm')
        self.screen.insert_table.setCellWidget(row_count, 8, outlet_travel)

        blank_summary = QtWidgets.QTableWidgetItem()
        if summary_input:
            blank_summary.setText(summary_input)
        self.screen.insert_table.setItem(row_count, 9, blank_summary)

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
            self.screen.insert_table.setCellWidget(row_count - 1, 0, remove_button)

    def remove_step(self):
        """Removes the specified row from the table."""
        current_row = self.screen.insert_table.currentRow()
        self._form_data.remove(self._form_data[current_row])
        self.screen.insert_table.removeRow(current_row)

    def set_step_conditions(self, dialog, dialog_data):
        """ Sets table values based on form data from dialog. """
        logging.info(dialog_data)
        current_row = self.screen.insert_table.currentRow()

        data = {'Type': dialog}
        data.update({key: dialog_data[key]() for key in dialog_data.keys()})

        try:
            self._form_data[current_row] = data
        except IndexError:
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
        self.screen.insert_table.setItem(current_row, 9, summary_item)

    def load_dialog(self, dialog_type):
        """ Loads the appropriate dialog based on user input in table. """
        if not self._populating_table:
            current_row = self.screen.insert_table.currentRow()
            try:
                inlet = self.screen.insert_table.cellWidget(current_row, 5).currentText()
                outlet = self.screen.insert_table.cellWidget(current_row, 6).currentText()
            except AttributeError:
                inlet = 'Select'
                outlet = 'Select'
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
            CEGraphic.ErrorMessageUI(error_message='Invalid file chosen')
            return

        with open(open_file_path, 'rb') as open_file:
            try:
                self.insert = pickle.load(open_file)
            except pickle.UnpicklingError:  # Errors due to file corruption or wrong files with right ext.
                message = 'Could not read in data from {}'.format(open_file_path)
                CEGraphic.ErrorMessageUI(message)
            else:
                self.screen.image_frame.clear()  # Clear image frame for new insert.
                self.screen.file_name.setText(open_file_path)

                # for row in range(self.screen.insert_table.rowCount()):  # Clears the table
                #     self.screen.insert_table.removeRow(self.screen.insert_table.rowCount()-1)

                for well in self.insert.wells:  # Loads the new shapes onto the frame
                    logging.info(well.bound_box)
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
            CEGraphic.ErrorMessageUI(error_message='Invalid file chosen')
            return

        with open(open_file_path, 'rb') as open_file:
            try:
                self.insert = pickle.load(open_file)
            except pickle.UnpicklingError:  # Errors due to file corruption or wrong files with right ext.
                message = 'Could not read in data from {}'.format(open_file_path)
                CEGraphic.ErrorMessageUI(message)
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
            CEGraphic.ErrorMessageUI(message)
            return

        self.screen.file_name_save.setText(open_file_path)

        with open(open_file_path, 'rb') as open_file:
            try:
                data = pickle.load(open_file)
            except pickle.UnpicklingError:
                message = 'Could not read in data from {}.'.format(open_file_path)
                CEGraphic.ErrorMessageUI(message)
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
                CEGraphic.ErrorMessageUI(error_message='Could not save the method.')

    def select_file(self):
        """Prompts the user to select a file to eventually save to."""
        file_path = QtWidgets.QFileDialog.getSaveFileName(self.screen, 'Select a file', os.getcwd(),
                                                          'METHOD(*.met)')
        if file_path[0]:
            file_path = file_path[0]
        else:
            return

        if os.path.splitext(file_path)[1] != '.met':
            CEGraphic.ErrorMessageUI(error_message='Invalid File Extension')
            return

        self.screen.file_name_save.setText(file_path)

    def populate_table(self, method):
        """Populates table with new insert."""
        self._populating_table = True

        self.screen.insert_table.clearContents()
        for row in range(self.screen.insert_table.rowCount()):
            self.screen.insert_table.removeRow(self.screen.insert_table.rowCount() - 1)

        self._form_data = []
        for step in method.steps:
            if step:
                self.add_step([step['Inlet']], [step['Outlet']], action_input=step['Type'], inlet_input=step['Inlet'],
                              outlet_input=step['Outlet'], time_input=step['Time'], value_input=step['Value'],
                              duration_input=step['Duration'], summary_input=step['Summary'],
                              inlet_travel_input=step['InletTravel'], outlet_travel_input=step['OutletTravel'])
                self._form_data += [step]

        self._populating_table = False

    def compile_method(self):
        """ Compiles all step information into a method object. """
        n = 0
        for data in self._form_data:
            if 'Type' in data.keys():
                data['InletTravel'] = self.screen.insert_table.cellWidget(n, 7).value()
                data['OutletTravel'] = self.screen.insert_table.cellWidget(n, 8).value()
                data['Inlet'] = self.screen.insert_table.cellWidget(n, 5).currentText()
                data['Outlet'] = self.screen.insert_table.cellWidget(n, 6).currentText()
                data['Time'] = self.screen.insert_table.item(n, 1).text()
                data['Summary'] = self.screen.insert_table.item(n, 9).text()
                data['Value'] = self.screen.insert_table.item(n, 3).text()
                data['Duration'] = self.screen.insert_table.item(n, 4).text()
                n += 1

        self.method = CEObjects.Method(steps=self._form_data, insert=self.insert)


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
            self.screen.method_table.setCellWidget(row_count - 1, 0, remove_button)

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
            CEGraphic.ErrorMessageUI(message)
            return

        with open(open_file_path, 'rb') as open_file:
            try:
                data = pickle.load(open_file)
            except pickle.UnpicklingError:  # Should not occur unless user really screws up.
                message = 'Could not read in data from {}.'.format(open_file_path)
                CEGraphic.ErrorMessageUI(message)
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
    _pixel2um = 1
    _calibrating_ratio = False
    _setting_laser = False
    _first_calibration_point = None
    _xy_step_size = 1  # 1 is µm, mm would be 1000
    _clearance_height = 10
    _run_thread = None
    _laser_poll_flag = False
    _laser_on_time = 0  # seconds
    _laser_max = 60
    _laser_on = threading.Event()
    _stop_thread_flag = threading.Event()
    _pause_flag = threading.Event()
    _inject_flag = threading.Event()
    _live_feed = threading.Event()
    _plot_data = threading.Event()
    _laser_position = None
    _t = 350
    _start = True
    mover = None

    _stop.set()
    _stop.clear()
    _last_cell_positions = {'xy': None, 'cap': None, 'obj': None, 'well': None}

    # Screen Background Functions
    def __init__(self, screen, hardware, repository):
        self.screen = screen
        self.hardware = hardware
        self.lyse = Lysis.Lysis(hardware=hardware)

        self.repository = repository

        self.methods = []
        self.methods_id = []
        self.insert = None
        self.injection_wait = 4.5
        self._um2pix = 1 / 300
        self._mm2pix = self._um2pix * 1000
        self._detector = Detection.CellDetector(self.hardware)
        self._stage_offset = [0,0]
        self._stage_inversion = self.hardware.xy_stage_inversion
        self._new_pixmap = None
        self._event = None
        self.screen.live_feed_scene.setSceneRect(0, 0, 512, 512)

        # Set up logging window in the run screen.
        self.log_handler = CEGraphic.QPlainTextEditLogger(self.screen.output_window)
        self.log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO)
        logging.info('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')

        logging.info('System Updates')

        self._add_row("", "")
        self._start_updating_display()
        self._set_callbacks()

    def _set_callbacks(self):
        """Assigns callbacks to all widgets and signals for the run screen."""
        self.screen.temp_find_button.released.connect(lambda: threading.Thread(target=self.find_cell).start())
        self.screen.temp_calibrate_button.released.connect(lambda: self.calibrate_system())
        self.screen.live_feed_scene.calibrating_crosshairs.connect(lambda: self._screen_selection())
        self.screen.temp_pixel_conversion_button.released.connect(lambda: self._calibrating_image_ratio(False))
        self.screen.temp_laser_set.released.connect(lambda: self._setting_laser_position(False))
        self.screen.temp_focus_button.released.connect(lambda: threading.Thread(target=self.focus).start())
        self.screen.temp_pic_button.released.connect(lambda: threading.Thread(target=self.take_training_images).start())
        self.screen.save_plot.released.connect(lambda: self.save_plot())
        self.screen.reset_plot.released.connect(lambda: self.reset_plot())
        self.screen.view_plot.released.connect(lambda: self.view_plot())

        if self.hardware.hasXYControl:
            self.screen.xy_up.released.connect(
                lambda: self.hardware.set_xy(rel_xy=[0, self.screen.xy_step_size.value() * self._xy_step_size]))
            self.screen.xy_down.released.connect(
                lambda: self.hardware.set_xy(rel_xy=[0, -self.screen.xy_step_size.value() * self._xy_step_size]))
            self.screen.xy_right.released.connect(
                lambda: self.hardware.set_xy(rel_xy=[self.screen.xy_step_size.value() * self._xy_step_size, 0]))
            self.screen.xy_left.released.connect(
                lambda: self.hardware.set_xy(rel_xy=[-self.screen.xy_step_size.value() * self._xy_step_size, 0]))
            self.screen.xy_x_value.selected.connect(lambda: self._value_display_interact(selected=True))
            self.screen.xy_y_value.selected.connect(lambda: self._value_display_interact(selected=True))
            self.screen.xy_x_value.unselected.connect(lambda: self._value_display_interact(selected=False))
            self.screen.xy_y_value.unselected.connect(lambda: self._value_display_interact(selected=False))
            self.screen.xy_x_value.returnPressed.connect(
                lambda: self.hardware.set_xy(xy=[float(self.screen.xy_x_value.text()), self.hardware.get_xy()[1]]))
            self.screen.xy_y_value.returnPressed.connect(
                lambda: self.hardware.set_xy(xy=[self.hardware.get_xy()[0], float(self.screen.xy_y_value.text())]))
            self.screen.xy_set_origin.released.connect(lambda: self.hardware.set_xy_home())
            # self.screen.xy_origin.released.connect(lambda: self.hardware.home_xy())
            self.screen.xy_stop.released.connect(lambda: self.hardware.stop_xy())
        else:
            self.screen.enable_xy_stage_form(False)

        if self.hardware.hasObjectiveControl:
            self.screen.objective_up.released.connect(
                lambda: self.hardware.set_objective(rel_h=self.screen.objective_step_size.value()))
            self.screen.objective_down.released.connect(
                lambda: self.hardware.set_objective(rel_h=-self.screen.objective_step_size.value()))
            self.screen.objective_value.returnPressed.connect(
                lambda: self.hardware.set_objective(h=float(self.screen.objective_value.text())))
            self.screen.objective_stop.released.connect(lambda: self.hardware.stop_objective())
            self.screen.objective_value.selected.connect(lambda: self._value_display_interact(selected=True))
            self.screen.objective_value.unselected.connect(lambda: self._value_display_interact(selected=False))
            self.screen.objective_set_home.released.connect(lambda: self.hardware.set_objective_home())
            self.screen.objective_home.released.connect(lambda: self.hardware.home_objective())
        else:
            self.screen.enable_objective_form(False)

        if self.hardware.hasOutletControl:
            self.screen.outlet_up.released.connect(
                lambda: self.hardware.set_outlet(rel_h=self.screen.outlet_step_size.value()))
            self.screen.outlet_down.released.connect(
                lambda: self.hardware.set_outlet(rel_h=-self.screen.outlet_step_size.value()))
            self.screen.outlet_value.returnPressed.connect(
                lambda: self.hardware.set_outlet(h=float(self.screen.outlet_value.text())))
            self.screen.outlet_stop.released.connect(lambda: self.hardware.stop_outlet())
            self.screen.outlet_value.selected.connect(lambda: self._value_display_interact(selected=True))
            self.screen.outlet_value.unselected.connect(lambda: self._value_display_interact(selected=False))
            self.screen.outlet_set_home.released.connect(lambda: self.hardware.set_outlet_home())
            self.screen.outlet_home.released.connect(lambda: self.hardware.home_outlet())
        else:
            self.screen.enable_outlet_form(False)

        if self.hardware.hasPressureControl:
            self.screen.pressure_rinse_state.positive_selected.connect(lambda: self.hardware.pressure_rinse_start())
            self.screen.pressure_rinse_state.negative_selected.connect(lambda: self.hardware.pressure_rinse_stop())
            self.screen.pressure_valve_state.positive_selected.connect(lambda: self.hardware.pressure_valve_open())
            self.screen.pressure_valve_state.negative_selected.connect(lambda: self.hardware.pressure_valve_close())
            self.screen.pressure_off.released.connect(lambda: self.hardware.stop_pressure())
        else:
            self.screen.enable_pressure_form(False)

        if self.hardware.hasInletControl:

            self.screen.z_up.released.connect(lambda: self.hardware.set_z(rel_z=-self.screen.z_step_size.value()))
            self.screen.z_down.released.connect(lambda: self.hardware.set_z(rel_z=self.screen.z_step_size.value()))
            self.screen.z_value.returnPressed.connect(lambda: self.hardware.set_z(float(self.screen.z_value.text())))
            self.screen.z_stop.released.connect(lambda: self.hardware.stop_z())
            self.screen.z_value.selected.connect(lambda: self._value_display_interact(selected=True))
            self.screen.z_value.unselected.connect(lambda: self._value_display_interact(selected=False))
            self.screen.z_set_home.released.connect(lambda: self.hardware.set_z_home())
            self.screen.z_home.released.connect(lambda: threading.Thread(target=self.hardware.home_z).start())
        else:
            self.screen.enable_z_stage_form(False)

        if self.hardware.hasLaserControl:
            self.screen.laser_fire_check.setEnabled(True)
            self.screen.laser_pfn.returnPressed.connect(
                lambda: self.hardware.set_laser_parameters(pfn=self.screen.laser_pfn.text()))
            self.screen.laser_attenuation.returnPressed.connect(
                lambda: self.hardware.set_laser_parameters(att=self.screen.laser_attenuation.text()))
            self.screen.laser_burst_count.returnPressed.connect(
                lambda: self.hardware.set_laser_parameters(burst=self.screen.laser_burst_count.text()))
            self.screen.laser_fire.released.connect(lambda: self.hardware.laser_fire())
            self.screen.laser_standby.released.connect(lambda: self.hardware.laser_standby())
            self.screen.laser_stop.released.connect(lambda: self.hardware.laser_stop())
            self.screen.laser_off.released.connect(lambda: self.stop_laser())
            self.screen.laser_check.released.connect(lambda: threading.Thread(target=self.hardware.laser_check).start())
        else:
            self.screen.enable_laser_form(False)

        if self.hardware.hasVoltageControl:
            self.screen.voltage_value.valueChanged.connect(
                lambda: self.hardware.set_voltage(self.screen.voltage_value.value()))
            self.screen.voltage_off.released.connect(lambda: self.hardware.stop_voltage())
        else:
            self.screen.enable_voltage_form(False)

        if self.hardware.hasCameraControl:
            self.screen.live_option.positive_selected.connect(lambda: self._switch_feed(True))
            self.screen.live_option.negative_selected.connect(lambda: self._switch_feed(False))
            self.screen.focus_feed.released.connect(lambda: self.focus())
            self.screen.camera_load.released.connect(lambda: self.hardware.open_image())
            self.screen.camera_close.released.connect(lambda: self.hardware.close_image())
            self.screen.buffer_save.released.connect(lambda: self._save_sequence())
        else:
            self.screen.enable_live_feed(False)

        if self.hardware.hasLEDControl:
            self.screen.r_channel.released.connect(
                lambda x=self.screen.r_channel:
                self.hardware.turn_on_led('R') if x.isChecked() else self.hardware.turn_off_led('R'))
            self.screen.dance_button.released.connect(
                lambda x=self.screen.dance_button:
                self.hardware.turn_on_dance() if x.isChecked() else self.hardware.turn_off_dance())
            self.screen.g_channel.released.connect(
                lambda x=self.screen.g_channel:
                self.hardware.turn_on_led('G') if x.isChecked() else self.hardware.turn_off_led('G'))
            self.screen.b_channel.released.connect(
                lambda x=self.screen.b_channel:
                self.hardware.turn_on_led('B') if x.isChecked() else self.hardware.turn_off_led('B'))

        self.screen.all_stop.released.connect(lambda: self.stop_all())

        self.screen.start_sequence.released.connect(lambda: self.start_sequence())
        self.screen.pause_sequence.released.connect(lambda: self.pause_sequence())
        self.screen.stop_sequence.released.connect(lambda: self.end_sequence())
        self.screen.inject_capture_button.released.connect(lambda: self.inject_capture())

        self.screen.inject_cell_pos.released.connect(lambda: self.lyse.cap_control.record_cell_height())
        self.screen.inject_cap_pos.released.connect(lambda: self.lyse.cap_control.record_cap_height())
        self.screen.inject_lower_cap.released.connect(lambda: self.lyse.lower_capillary())
        self.screen.inject_burst_lyse.released.connect(lambda pfn=self.screen.laser_pfn,
                                                       attn=self.screen.laser_attenuation,
                                                       : threading.Thread(target = self.lyse.post_movement_lysis, args= (pfn.text(),
                                                                                       attn.text())).start())

        self.screen.clear_output.released.connect(lambda: self.clear_output_window())
        self.screen.save_output.released.connect(lambda: self.save_output_window())
        self.screen.feed_updated.connect(lambda: self.screen.feed_pointer.setPixmap(self._new_pixmap))
        self.screen.xy_updated.connect(lambda: self.screen.live_feed_scene.draw_crosshairs(self._event))

    def _start_updating_display(self):
        """Initializes all the processes for updating the live display (stage positions, live feed, etc)"""
        threading.Thread(target=self._update_live_feed, daemon=True).start()
        threading.Thread(target=self._update_plot, daemon=True).start()

        if self.hardware.hasXYControl:
            value = self.hardware.get_xy()
            if value is not None:
                self.screen.xy_x_value.setText("{:.3f}".format(float(value[0])))
                self.screen.xy_y_value.setText("{:.3f}".format(float(value[1])))
            else:
                logging.error('Live updates of stage/motor positions disabled.')
                return

        if self.hardware.hasInletControl:
            value = self.hardware.get_z()
            if value is not None:
                self.screen.z_value.setText("{:.3f}".format(float(value)))
            else:
                logging.error('Live updates of stage/motor positions disabled.')
                return

        if self.hardware.hasOutletControl:
            value = self.hardware.get_outlet()
            logging.info(value)
            if value is not None:
                self.screen.outlet_value.setText("{:.3f}".format(float(value)))
            else:
                logging.error('Live updates of stage/motor positions disabled.')
                return

        if self.hardware.hasObjectiveControl:
            value = self.hardware.get_objective()
            logging.info(value)
            if value is not None:
                self.screen.objective_value.setText("{:.3f}".format(float(value)))
            else:
                logging.error('Live updates of stage/motor positions disabled.')
                return

        threading.Thread(target=self._update_stages, daemon=True).start()

    def _value_display_interact(self, selected=False):
        """Pauses or starts value update on stage positions when user clicks on or clicks off the edit box."""
        logging.info(selected)
        if selected:
            self._stop.set()
        else:
            self._stop.clear()

    def _update_stages(self):
        """Updates the live positions of the stages and motors in the edit boxes."""
        while True:
            if self._stop.is_set():
                time.sleep(4 * self._update_delay)
                continue

            value = self.hardware.get_xy()
            self.screen.xy_x_value.setText("{:.3f}".format(float(value[0])))
            self.screen.xy_y_value.setText("{:.3f}".format(float(value[1])))
            time.sleep(self._update_delay)

            value = self.hardware.get_z()
            self.screen.z_value.setText("{:.3f}".format(float(value)))
            time.sleep(self._update_delay)

            value = self.hardware.get_objective()
            self.screen.objective_value.setText("{:.3f}".format(float(value)))
            time.sleep(self._update_delay)

            value = self.hardware.get_outlet()
            self.screen.outlet_value.setText("{:.3f}".format(float(value)))
            time.sleep(self._update_delay)

    def _update_live_feed(self):
        """Loads either the new image for the live feed or moves the crosshairs on the insert view."""
        while True:
            if self._live_feed.is_set() and self.hardware.hasCameraControl and self.hardware.camera_state():
                try:
                    image = self.hardware.get_image()
                except ValueError:
                    logging.error("Value Error, could not load image")
                    continue

                if image is None:
                    continue
                self._new_pixmap = self.screen.update_pixmap(camera=True)

                self.screen.feed_updated.emit()
                time.sleep(.01)

            elif self.hardware.hasXYControl:
                event_location = self.hardware.get_xy()
                self._event = [(self.hardware.xy_stage_size[0] - event_location[0]*self._stage_inversion[0]) * self._um2pix,
                               (self.hardware.xy_stage_size[1] - event_location[1] *self._stage_inversion[1]) * self._um2pix]

                self.screen.xy_updated.emit()
            else:
                break

    def _update_plot(self):
        """Updates the plots with new data from the DAQ."""
        # self._plot_data.set()  # fixme
        if self.hardware.hasVoltageControl:
            while True:
                data = self.hardware.get_data()
                with self.hardware.daq_board_control.data_lock:
                    rfu = data['rfu'][:]
                    kv = data['volts'][:]
                    ua = data['current'][:]
                freq = self.hardware.daq_board_control.downsampled_freq


                if self._plot_data.is_set():
                    threading.Thread(target=self.screen.update_plots, args=(rfu, ua, freq)).start()

                if len(kv) > 4:
                    try:
                        kv = np.mean(kv[-4:-1])
                        ua = np.mean(ua[-4:-1])
                    except IndexError:
                        return

                time.sleep(.25)

    def _save_sequence(self):
        open_file_path = QtWidgets.QFileDialog.getExistingDirectory(self.screen, 'Select Folder to save to')
        if open_file_path == -1:
            return
        self.hardware.save_buffer(open_file_path, 'capture.avi')

    def save_plot(self):

        # returns tuple (file_path_file_name.csv, extension)
        open_file_path = QtWidgets.QFileDialog.getSaveFileName(self.screen, 'Choose previous session',
                                                               os.getcwd(), '(*.csv)')
        # Save data
        self.hardware.save_data(open_file_path[0])

    def reset_plot(self):
        self.hardware.daq_board_control._clear_data()

    def view_plot(self):
        check = self.screen.view_plot.isChecked()
        if check:
            self._plot_data.set()
        else:
            self._plot_data.clear()
        return

    def _switch_feed(self, live):
        """Switches the feed between live feed from camera or insert view with live XY position."""
        if not live:
            logging.info('Switching to insert view.')
            self.hardware.stop_feed()
            self._new_pixmap = self.screen.update_pixmap(camera=False)
            self.screen.feed_updated.emit()
            time.sleep(.1)
            self._load_insert()
            self._live_feed.clear()
            time.sleep(.1)
        else:
            logging.info('Switching to live feed.')
            self.screen.clear_feed_scene()
            time.sleep(.1)
            self.hardware.start_feed()
            self._live_feed.set()
            time.sleep(.1)

    def _load_insert(self):
        """Loads the insert for the method onto the live view."""
        if self.insert:
            for well in self.insert.wells:
                self.screen.live_feed_scene.add_shape(well.shape, well.bound_box)

    def _laser_timer(self, start_time):
        """Countdown timer for laser device."""
        while True:
            if self._laser_on.is_set():
                _laser_rem_time = self.hardware.laser_max_time - (time.time() - start_time)
                if _laser_rem_time > 0:
                    self.screen.laser_timer.setText('{:.1f}s'.format(_laser_rem_time))
                    time.sleep(1)
                else:
                    self._laser_on.clear()
            else:
                self.screen.laser_timer.setText('0s')
                self.screen.laser_fire_check.setEnabled(False)
                self.screen.laser_fire_check.setChecked(False)
                break

    def _calibrating_image_ratio(self, crosshair_set=False):
        if crosshair_set:
            if self._first_calibration_point:
                logging.info('Second calibration point.')
                second_calibration_point = [self.hardware.get_xy(), self.screen.live_feed_scene.crosshair_location]

                pixel_dx = second_calibration_point[1][0] - self._first_calibration_point[1][0]
                meter_dx = second_calibration_point[0][0] - self._first_calibration_point[0][0]
                pixel_dy = second_calibration_point[1][1] - self._first_calibration_point[1][1]
                meter_dy = second_calibration_point[0][1] - self._first_calibration_point[0][1]
                pixel_d = np.sqrt(pixel_dx ** 2 + pixel_dy ** 2)
                meter_d = np.sqrt(meter_dx ** 2 + meter_dy ** 2)
                logging.info('{},{},{}'.format(pixel_dx, pixel_dy, pixel_d))
                logging.info('{},{},{}'.format(meter_dx, meter_dy, meter_d))

                self._pixel2um = meter_d / pixel_d
                self._detector.pix2um = self._pixel2um

                self._first_calibration_point = None
                self.screen.live_feed_scene.calibrating = False
                logging.info('Conversion is {}'.format(self._pixel2um))
                self._calibrating_ratio = False
            else:
                logging.info('First calibration point.')
                self._first_calibration_point = [self.hardware.get_xy(), self.screen.live_feed_scene.crosshair_location]
        else:
            self._calibrating_ratio = not self._calibrating_ratio

    def _setting_laser_position(self, crosshair_set=False):
        """
        Sets the laser position to crosshair location (pixels? or um?)

        :param crosshair_set:
        :return:
        """
        if crosshair_set:
            self._laser_position = self.screen.live_feed_scene.crosshair_location
            self._detector.laser_spot = self._laser_position
            logging.info('Setting laser position to {}'.format(self._laser_position))
            self._setting_laser = False
        else:
            self._setting_laser = not self._setting_laser

    def _screen_selection(self):
        if self._setting_laser:
            self._setting_laser_position(True)
        if self._calibrating_ratio:
            self._calibrating_image_ratio(True)
        else:
            pass

    # Hardware Control Function
    def calibrate_system(self):
        """Walks user through the necessary system calibrations that can't be done automatically."""
        if not self.hardware.hasXYControl:
            return

        if self._start:
            if not self.screen.live_feed_scene.calibrating:
                message = 'Follow the instructions in the output window to calibrate the system.'
                CEGraphic.PermissionsMessageUI(message)

                message = 'Calibrating Instructions' \
                          '2. If you are doing single cell analysis, focus the objective (manually or automatically.\n' \
                          '3. Once focused, select an object on the live feed.\n' \
                          '4. Move the XY stage until the object is on the opposite side of the live feed.\n' \
                          '5. Reselect the object.\n'
                logging.info(message)
            else:
                logging.info('Ending Calibration')

            self.screen.live_feed_scene.calibrating = not self.screen.live_feed_scene.calibrating
            self._start = False
        else:
            if not self._first_calibration_point:
                logging.info('First calibration point.')
                self._first_calibration_point = [self.hardware.get_xy(), self.screen.live_feed_scene.crosshair_location]

            else:
                logging.info('Second calibration point.')
                second_calibration_point = [self.hardware.get_xy(), self.screen.live_feed_scene.crosshair_location]

                pixel_dx = second_calibration_point[1][0] - self._first_calibration_point[1][0]
                meter_dx = second_calibration_point[0][0] - self._first_calibration_point[0][0]
                pixel_dy = second_calibration_point[1][1] - self._first_calibration_point[1][1]
                meter_dy = second_calibration_point[0][1] - self._first_calibration_point[0][1]
                pixel_d = np.sqrt(pixel_dx ** 2 + pixel_dy ** 2)
                meter_d = np.sqrt(meter_dx ** 2 + meter_dy ** 2)

                self._pixel2um = meter_d / pixel_d
                self._detector.pix2um = self._pixel2um
                self._first_calibration_point = None
                self.screen.live_feed_scene.calibrating = False
                logging.info('Conversion is {}'.format(self._pixel2um))
                self._start = True

    def stop_laser(self):  # keeper
        """Stops laser as well as alters appropriate items on the view."""
        self.hardware.laser_close()
        self.screen.laser_fire_check.setEnabled(False)
        self.screen.laser_timer.setText('0s')
        self._laser_on.clear()

    def stop_all(self):
        """Stops and closes all hardware devices. Exits program."""
        self._stop_thread_flag.set()
        self._stop.set()

        if self.hardware.hasLaserControl:
            logging.warning('Stopping Laser')
            threading.Thread(target=self.hardware.laser_close).start()

        if self.hardware.hasVoltageControl:
            logging.warning('Stopping Voltage')
            threading.Thread(target=self.hardware.close_voltage).start()

        if self.hardware.hasXYControl:
            logging.warning('Stopping XY')
            threading.Thread(target=self.hardware.close_xy).start()

        if self.hardware.hasOutletControl:
            logging.warning('Stopping Outlet')
            threading.Thread(target=self.hardware.close_outlet).start()

        if self.hardware.hasInletControl:
            logging.warning('Stopping Inlet')
            threading.Thread(target=self.hardware.close_z).start()

        if self.hardware.hasPressureControl:
            logging.warning('Stopping Pressure')
            threading.Thread(target=self.hardware.pressure_close).start()

        if self.hardware.hasObjectiveControl:
            logging.warning('Stopping Objective')
            threading.Thread(target=self.hardware.close_objective).start()

        if self.hardware.hasCameraControl:
            logging.warning('Stopping Camera')
            threading.Thread(target=self.hardware.close_image).start()

        sys.exit()

    def fire_laser(self):
        """Fires the laser."""

        def fire():
            executed = self.hardware.laser_fire()
            if not executed:
                logging.error('Error firing laser. Maker sure laser_fire() is properly defined in the hardware class.')

        threading.Thread(target=fire, daemon=True).start()  # Separate thread because it takes a few seconds.

    def laser_on(self):
        """Turns on laser."""
        if self._laser_poll_flag:
            logging.info('Adding {}s to timer.'.format(self.hardware.laser_max_time))
            self.hardware.laser_max_time += self.hardware.laser_max_time
        else:
            response = self.hardware.laser_standby()
            if response:
                self._laser_on.set()
                self.screen.laser_fire_check.setEnabled(True)
                threading.Thread(target=self._laser_timer, args=(time.time(),)).start()
            else:
                logging.error('Error starting laser. Make sure laser_standby() in hardware class is defined correctly.')

    def check_system(self):
        """Performs any available system checks and logs output."""
        if self.hardware.xy_stage_control and self.hardware.outlet_control and self.hardware.pressure_control and \
                self.hardware.daq_board_control:  # fixme
            return True
        return False

    # Sequence Table Functions
    def add_method(self):
        """ Prompts the user for and loads a method file. """
        open_file_path = QtWidgets.QFileDialog.getOpenFileNames(self.screen, 'Choose previous session',
                                                                os.getcwd(), 'METHOD(*.met)')
        if open_file_path[0]:
            open_file_path = open_file_path[0][0]
        else:
            return

        if os.path.splitext(open_file_path)[1] != '.met':
            message = 'Invalid file chosen.'
            CEGraphic.ErrorMessageUI(message)
            return

        with open(open_file_path, 'rb') as open_file:
            try:
                data = pickle.load(open_file)
            except pickle.UnpicklingError:
                message = 'Could not read in data from {}.'.format(open_file_path)
                CEGraphic.ErrorMessageUI(message)
            else:
                if self.insert:
                    logging.info('insertloaded')
                    if self.insert.label != data.insert.label and self.insert.wells != data.insert.wells:
                        CEGraphic.ErrorMessageUI('The insert for this method does not match the insert for previously'
                                                 ' loaded methods.')
                        return
                else:
                    self.insert = data.insert
                    if not self._live_feed.is_set():
                        self._load_insert()

                self.methods.append(data)
                self.methods_id.append( open_file_path.split('/')[-1][:-4] )
                self._add_row(open_file_path, data.steps[0]['Summary'])

    def remove_method(self):
        current_row = self.screen.sequence_display.currentRow()
        self.screen.sequence_display.removeRow(current_row)
        try:
            self.methods.pop(current_row)
            self.methods_id.pop(current_row)
        except IndexError:
            logging.warning("Methods popped incorrectly")

    def _add_row(self, method_file, summary):
        row_count = self.screen.sequence_display.rowCount()
        self.screen.sequence_display.insertRow(row_count)

        if row_count > 0:
            remove_button = QtWidgets.QPushButton('-')
            remove_button.setFixedWidth(38)
            remove_button.released.connect(lambda: self.remove_method())
            self.screen.sequence_display.setCellWidget(row_count - 1, 0, remove_button)

            method_file_name = QtWidgets.QTableWidgetItem()
            method_file_name.setText(method_file)
            self.screen.sequence_display.setItem(row_count - 1, 1, method_file_name)

            method_summary = QtWidgets.QTableWidgetItem()
            method_summary.setText(summary)
            self.screen.sequence_display.setItem(row_count - 1, 2, method_summary)

        add_button = QtWidgets.QPushButton('+')
        add_button.setFixedWidth(38)
        add_button.released.connect(lambda: self.add_method())
        self.screen.sequence_display.setCellWidget(row_count, 0, add_button)

    # Neural Net Functions
    def take_training_images(self):
        logging.info('Taking Images')

        stack = self._t
        self._t += 1
        save_location = "zStack_{}_{}_{}.png".format(int(time.time()), stack, 0)
        increment = 3
        num_pictures = 40
        sleepy_time = 0.25

        start_z = self.hardware.get_objective()

        self.hardware.record_image(save_location)
        time.sleep(sleepy_time)

        start = self.hardware.get_objective()
        for _ in range(1, int(num_pictures / 2)):
            self.hardware.set_objective(self.hardware.get_objective() + increment)
            time.sleep(sleepy_time)
            end = self.hardware.get_objective()
            save_location = "zStack_{}_{}_{}.png".format(int(time.time()), stack, round(end - start))
            logging.info(save_location)

            self.hardware.record_image(save_location)
            time.sleep(sleepy_time)

        self.hardware.set_objective(start_z)
        time.sleep(sleepy_time * 6)

        for _ in range(1, int(num_pictures / 2)):
            self.hardware.set_objective(self.hardware.get_objective() - increment)
            time.sleep(sleepy_time)
            end = self.hardware.get_objective()
            save_location = "zStack_{}_{}_{}.png".format(int(time.time()), stack, round(end - start))
            logging.info(save_location)

            self.hardware.record_image(save_location)
            time.sleep(sleepy_time)

        self.hardware.set_objective(start_z)
        time.sleep(sleepy_time * 6)

    def focus(self):
        """Focuses the objective."""

        def user_focused():
            focus_stop_flag.set()
            self.hardware.objective_focus = self.hardware.get_objective()

        def continue_focusing():
            focus_pause_flag.clear()

        def cancel_focusing():
            focus_stop_flag.set()
            focus_pause_flag.clear()

        def prompt_user():
            message = '10+ Attempts made at focusing. Manually focus objective and click \'Okay,\' or click \'Keep ' \
                      'Trying\' to \nallow the network to continue focusing or cancel the run.'
            CEGraphic.PermissionsMessageUI(permissions_message=message, pos_function=user_focused,
                                           other_function=continue_focusing, other_label='Keep Trying',
                                           neg_function=cancel_focusing)
            focus_pause_flag.set()
            while focus_pause_flag.is_set():
                time.sleep(2)

        if not self.hardware.image_control:
            return None

        if self.hardware.system_id != 'BARRACUDA':
            logging.error('Cannot auto focus on this system.')
            return False

        if not self.hardware.get_network_status():
            logging.info('Loading networks. Takes up to 15-20 seconds normally.')
            threading.Thread(target=self.hardware.prepare_networks).start()
            start_time = time.time()
            while not self.hardware.get_network_status():
                if (time.time() - start_time) > 60:
                    logging.error('Networks took too long to load.')
                    return False
                time.sleep(3)
            logging.info('Networks loaded.')

        focus_tolerance = 3
        negative_tolerance = 0.01
        focus_stop_flag = threading.Event()
        focus_pause_flag = threading.Event()
        attempts = 1
        distances = [None, None, None, None, None, None, None, None, None, None, None]

        s = time.time()
        while True:
            # Get an image and run the network to get a predicted distance from focus.
            # image = self.hardware.get_image()
            s_2 = time.time()
            distance, score, negative_score = self.hardware.get_focus()
            logging.info('{}, {}, {}'.format(distance, score, time.time() - s_2))
            distances[(attempts - 1) % 10] = distance
            logging.info(distances)

            # If the network predicts we are at or near zero, stop and record current position as the focus point.
            if focus_tolerance >= distance >= -focus_tolerance:
                logging.info('Focused in {}'.format(time.time() - s))
                self.hardware.objective_focus = self.hardware.get_objective()
                return True

            # Compare the score of the negative of the prediction, if it is high enough change the sign.
            move = -distance + random.randint(-2, 2)
            if negative_score > negative_tolerance and distance > 0:
                move = -move

            # Move the objective according to predicted distance.
            logging.info('Movement is {}'.format(move))
            self.hardware.set_objective(rel_h=move)
            time.sleep(1)

            # If the attempts to get in focus exceed 5, prompt the user to choose: a) allow network to keep trying,
            # b) manually set focus, or c) cancel the run.
            if attempts > 0:
                return False
                # prompt_user() fixme
                # attempts = 1
            elif attempts == 3:
                self.hardware.set_objective(rel_h=2)
            elif attempts == 5:
                self.hardware.set_objective(rel_h=2)

            # If the stop flag is set then exit the focusing program.
            if focus_stop_flag.is_set():
                logging.info('Auto-Focusing stopped.')
                return False

            attempts += 1

    def create_mover(self):
        xy = self.hardware.get_xy()
        self.mover = Detection.Mover(xy)

    def find_cell(self):
        """ Finds a cell"""
        if self.mover is None:
            logging.warning("Creating Mover")
            self.mover = Detection.Mover(self.hardware.get_xy)
            return
        self._detector.mover_find_cell(self.mover)

        """
        def adjust_laser(cell_n):
            x1 = cell_n[0] - self._laser_position[0]
            y1 = cell_n[1] - self._laser_position[1]
            x2 = cell_n[2] - self._laser_position[0]
            y2 = cell_n[3] - self._laser_position[1]
            return [x1, y1, x2, y2]

        def smart_move(repetitions):
            if iterations > (repetitions ** 2 + repetitions):
                repetitions += 1

            if iterations <= repetitions ** 2:
                move = [0, 150 * (-1) ** repetitions]
            else:
                move = [-150 * (-1) ** repetitions, 0]

            moved = self.hardware.set_xy(rel_xy=move)
            if not moved:
                return False
            return True

        repetitions = 1
        iterations = 1

        if not self.hardware.hasCameraControl or not self.hardware.hasXYControl:
            return None
        else:
            focused = self.focus()
            if not focused:
                return None
            time.sleep(1)

        if not self.hardware.get_network_status():
            logging.info('Loading networks. Takes up to 15-20 seconds normally.')
            threading.Thread(target=self.hardware.prepare_networks).start()
            start_time = time.time()
            while not self.hardware.get_network_status():
                if (time.time() - start_time) > 60:
                    logging.error('Networks took too long to load.')
                    return False
                time.sleep(3)
            logging.info('Networks loaded.')

        start_time = time.time()
        max_time = 60  # s
        min_separation = 10  # µm

        while True:
            if time.time() - start_time > max_time:
                logging.info('Cell not found.')
                return None

            cell_data = self.hardware.get_cells()

            if cell_data is None:
                return None

            cell_boxes, score = cell_data  # cell_boxes are in format [xmin, ymin, xmax, ymax]

            adjusted_cell_boxes = []
            if self._laser_position is not None:
                for cell in cell_boxes:
                    new_cell = adjust_laser(cell)
                    adjusted_cell_boxes.append(new_cell)
                cell_boxes = adjusted_cell_boxes

            cell_boxes = [[float(y) * float(self._pixel2um) for y in x] for x in cell_boxes]

            for cell in cell_boxes:
                cell_radius = np.sqrt(((cell[2] - cell[0]) / 2) ** 2 + ((cell[3] - cell[1]) / 2) ** 2)
                centroid = [(cell[2] - cell[0]) / 2 + cell[0], (cell[3] - cell[1]) / 2 + cell[1], cell_radius]
                self.screen.live_feed_scene.draw_rect(cell, single=True)

                for other_cell in cell_boxes:
                    if other_cell != cell:
                        other_cell_radius = np.sqrt(
                            ((other_cell[2] - other_cell[0]) / 2) ** 2 + ((other_cell[3] - other_cell[1]) / 2) ** 2)
                        centroid_separation = np.sqrt((cell[0] + cell[2] / 2 - other_cell[0] - other_cell[2] / 2) ** 2 +
                                                      (cell[1] + cell[3] / 2 - other_cell[1] - other_cell[3] / 2) ** 2)
                        cell_separation = centroid_separation - cell_radius - other_cell_radius

                        if cell_separation < min_separation:
                            pass  # fixme
                            # break
                else:
                    pass  # fixme
                    # self.hardware.set_xy(rel_xy=[centroid[1], -centroid[0]])
                    # return cell
            else:
                return True
                smart_move(repetitions)
                time.sleep(0.25)
                focused = self.focus()
                if not focused:
                    return None

                iterations += 1
    """

    # Run Control Functions
    def start_sequence(self):
        if self._pause_flag.is_set():
            logging.info('Continuing run ...')
            self._pause_flag.clear()
            return

        logging.info('Starting run ...')
        self._plot_data.set()
        self._run_thread = threading.Thread(target=self.run).start()

    def pause_sequence(self):
        logging.info('Pausing run ...')
        self._pause_flag.set()

    def end_sequence(self):
        logging.info('Stopping run ...')
        self.hardware.set_voltage(0)
        self._stop_thread_flag.set()

    def inject_capture(self):
        threading.Thread(target=self._capture_logic).start()

    def _capture_logic(self):
        logging.info('Capture Data')
        # Check if to acquire Cell Z-stacks
        if int(self.screen.inject_cell_box.checkState()) == 2:
            logging.info("Capture cell z_stack...")
            cell_focus = FocusTesting.CellFocusAuxillary(self.hardware)
            self.hardware.set_z(rel_z=-2)
            self.hardware.z_stage_control.wait_for_move()
            cell_focus.start_acquisition()
            self.hardware.set_z(rel_z=2)
            self.hardware.z_stage_control.wait_for_move()

        # Check if to acquire capillary z-stacks
        if int(self.screen.inject_cap_box.checkState()) == 2:
            logging.info("Capture Capillary Stack...")
            self.hardware.set_objective(rel_h=80)
            self.hardware.objective_control.wait_for_move()
            cap_focus = FocusTesting.CapillaryFocusAuxillary(self.hardware)
            cap_focus.start_acquisition()
            self.hardware.set_objective(rel_h=-80)
            self.hardware.objective_control.wait_for_move()

    def run(self):
        if not self.check_system():
            logging.error('Unable to start run.')
        repetitions = self.screen.repetition_input.value()
        flags = [self._pause_flag, self._stop_thread_flag, self._inject_flag, self._plot_data]
        runs = CERunLogic.RunMethod(self.hardware, self.methods, repetitions, self.methods_id,
                                    flags, self.insert, self.screen.run_prefix.text())
        state = runs.start_run()
        return state
        """
        for method, method_id in zip(self.methods, self.methods_id):

            repetitions = self.screen.repetition_input.value()
            run_state = self.run_method(method, repetitions, method_id)
            if not run_state:
                logging.info('Run stopped.')
                self._stop_thread_flag.clear()
                return False
        logging.info('Sequence Completed.')
        return True
        """

    def record_cell_info(self):
        xy = self.hardware.get_xy()
        cap = self.hardware.get_z()
        obj = self.hardware.get_objective()
        self._last_cell_positions['xy'] = xy
        self._last_cell_positions['cap'] = cap
        self._last_cell_positions['obj'] = obj
        return

    def run_method(self, method, repetitions, method_id):
        def check_flags():
            while self._pause_flag.is_set():
                if self._stop_thread_flag.is_set():
                    #self._plot_data.clear()
                    return False
                if self._inject_flag.is_set():
                    self.record_cell_info()
                self._plot_data.clear()
                time.sleep(0.2)
                continue
            if self._stop_thread_flag.is_set():
                self._plot_data.clear()
                return False
            self._plot_data.set()
            return True

        def move_inlet(inlet_travel):
            if self._stop_thread_flag.is_set():
                return
            self.hardware.set_z(inlet_travel)
            self.hardware.wait_z()
            return check_flags()

        def move_outlet(outlet_travel):
            if self._stop_thread_flag.is_set():
                return
            self.hardware.set_outlet(rel_h=outlet_travel)

            time.sleep(2)
            return check_flags()

        def move_objective(objective_position):
            if self._stop_thread_flag.is_set():
                return
            self.hardware.set_objective(objective_position)
            return check_flags()

        def move_xy_stage(inlet_location):
            if self._stop_thread_flag.is_set():
                return
            if inlet_location is None:
                logging.error('Unable to make next XY movement.')
                return False
            self.hardware.set_xy(xy=inlet_location)
            self.hardware.wait_xy()
            return check_flags()

        def wait_sleep(wait_time):
            """ Returns false if wait time was interupted by stop command"""
            start_time = time.time()
            while time.time()-start_time< wait_time and not self._stop_thread_flag.is_set():
                time.sleep(0.05)

            if self._stop_thread_flag.is_set():
                logging.warning("CE Run Stopped during Separation")
                return False
            return True

        def separate():
            if self._stop_thread_flag.is_set():
                return
            voltage_level = None
            pressure_state = None

            if step['SeparationTypeVoltageRadio']:
                voltage_level = float(step['ValuesVoltageEdit'])
            elif step['SeparationTypeCurrentRadio']:
                logging.error('Unsupported: Separation with current')
                return False
            elif step['SeparationTypePowerRadio']:
                logging.error('Unsupported: Separation with power')
                return False

            # Give user option to run combo of pressure and voltage
            if step['SeparationTypePressureRadio']:
                pressure_state = True
            elif step['SeparationTypeVacuumRadio']:
                logging.error('Unsupported: Separation with vacuum')
                return False

            if step['SeparationTypeWithPressureCheck']:
                pressure_state = True
            elif step['SeparationTypeWithVacuumCheck']:
                logging.error('Unsupported: Separation with vacuum.')
                return False

            duration = float(step['ValuesDurationEdit'])

            if voltage_level:
                self.hardware.set_voltage(voltage_level)

            if pressure_state:
                self.hardware.pressure_rinse_start()

            state = wait_sleep(duration)
            # Save Data
            now = datetime.datetime.now()
            file_name = "{}_{}_step_{}_rep_{}.csv".format( self.screen.run_prefix.text(),method_id, step_id, rep)
            save_path = os.path.join(save_dir, file_name)
            self.hardware.save_data(save_path)
            self.hardware.set_voltage(0)
            self.hardware.pressure_rinse_stop()

            return state



        def rinse():
            if self._stop_thread_flag.is_set():
                return
            pressure_state = None
            if step['PressureTypePressureRadio']:
                pressure_state = True
            elif step['PressureTypeVacuumRadio']:
                logging.error('Unsupported: Rinsing with vacuum.')
                return False

            duration = float(step['ValuesDurationEdit'])

            if pressure_state:
                self.hardware.pressure_rinse_start()

            time.sleep(duration)
            self.hardware.pressure_rinse_stop()

            return True

        def semi_auto_cell():
            if self._stop_thread_flag.is_set():
                return
            # If wells are the same move back one.
            if self._inject_flag.is_set():
                return False
            xy = self._last_cell_positions['xy']
            if xy is not None:
                move_xy_stage(xy)

                cap = self._last_cell_positions['cap']
                if cap is not None:
                    move_inlet(cap)

                obj = self._last_cell_positions['obj']
                if cap is not None:
                    move_objective(obj)
            self._inject_flag.set()


            return True

        def inject():
            if self._stop_thread_flag.is_set():
                return
            pressure_state = False
            voltage_level = None

            if step['InjectionTypeVoltageRadio']:
                voltage_level = float(step['ValuesVoltageEdit'])
            elif step['InjectionTypePressureRadio']:
                pressure_state = True
            elif step['InjectionTypeVacuumRadio']:
                logging.error('Unsupported: Injection with vacuum.')
                return False

            duration = float(step['ValuesDurationEdit'])

            if step['SingleCell']:
                if step['AutoSingleCell']:
                    logging.info("Automated single cell....")

                else:
                    semi_auto_cell()
                    logging.info('Run is paused. Locate and lyse cell.')
                    self._pause_flag.set()
                    state_n = check_flags()
                    if not state_n:
                        return False

            if pressure_state:
                self.hardware.pressure_rinse_start()

            if voltage_level:
                self.hardware.set_voltage(voltage_level)

            time.sleep(duration)
            self.hardware.set_objective(h=1000)
            self.hardware.set_voltage(0)
            self.hardware.pressure_rinse_stop()

            #Record buffer of injection after lysis.

            if step['SingleCell']:
                file_name = "{}_{}_step{}_rep{}".format(self.screen.run_prefix.text(), method_id, step_id, rep)
                save_path = os.path.join(save_dir, file_name)
                self.hardware.save_buffer(save_path, 'cell_lysis.avi')

            self.hardware.objective_control.wait_for_move()

            return True

        def create_run_folder():
            cwd = os.getcwd()
            now = datetime.datetime.now()
            folder_name = self.screen.run_prefix.text() + now.strftime("RunData__%Y_%m_%d__%H_%M_%S")
            save_dir = os.path.join(cwd, 'Data',  folder_name)
            try:
                os.makedirs(save_dir, exist_ok=True)
                return save_dir
            except FileExistsError:
                return save_dir

        # fixme prompt for alternate input if user selects unsupported type.

        save_dir = create_run_folder()

        for rep in range(repetitions):
            state = check_flags()
            if not state:
                return False
            previous_step = None
            self._inject_flag.clear()
            for step_id, step in enumerate(method.steps):
                if 'Type' in step.keys():
                    logging.info('{} Step: {}'.format(step['Type'], step['Summary']))
                    state = check_flags()
                    if not state:
                        return False
                    step_start = time.time()

                    state = move_inlet(0.25)

                    if not state:
                        return False

                    try:
                        cycles = int(step['TrayPositionsIncrementEdit'])
                    except ValueError:
                        state = move_xy_stage(self.insert.get_well_xy(step['Inlet']))
                    else:
                        if rep + 1 > cycles:
                            state = move_xy_stage(
                                self.insert.get_next_well_xy(step['Inlet'], int(np.floor(rep / cycles))))
                        else:
                            state = move_xy_stage(self.insert.get_well_xy(step['Inlet']))
                    if not state:
                        return False

                    if previous_step == 'Inject' and time.time() - step_start < self.injection_wait:
                        time.sleep(abs(self.injection_wait - (time.time() - step_start)))
                        state = check_flags()
                        if not state:
                            return False

                    state = move_outlet(step['OutletTravel'])
                    if not state:
                        return False

                    state = move_inlet(step['InletTravel'])
                    if not state:
                        return False

                    if step['Type'] == 'Separate':
                        executed = separate()
                        if not executed:
                            return False

                    elif step['Type'] == 'Rinse':
                        executed = rinse()
                        if not executed:
                            return False

                    elif step['Type'] == 'Inject':
                        executed = inject()

                        if not executed:
                            return False

                    logging.info('Step completed.')

                    previous_step = step['Type']
        return True

    # Output Terminal Functions
    def clear_output_window(self):
        self.log_handler.widget.clear()
        logging.info('System Updates')

    def save_output_window(self):
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
