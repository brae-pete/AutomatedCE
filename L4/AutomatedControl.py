"""
This file contains the code necessary to run automated control over a capillary electrophoresis system.

"""
import os
import string
import threading
import time
from queue import Queue
from L3.SystemsBuilder import CESystem
from L4 import Util, Trajectory, FileIO, Electropherogram
from L1.Util import get_system_var
import logging
import matplotlib.pyplot as plt
import numpy as np
from typing import Union


def get_standard_unit(value):
    """
    Adjusts the value to a standard value. Standard values do not need to bea dded to the units dictionary.
    The scales for each value in the dictionary should be a multiplication scalar factor to reach the standard
    unit scale.

    Standard units are: mm (for distance), volts for Voltage, and seconds for time_data.

    Example:
    For value == '33 cm'
    program returns: 3.3 * units['cm'] or 3.3 * 10 = 33

    :param value: str
    :return: float or int
    """
    units = {'cm': 10, 'kv': 1000, 'min': 60}
    # Get Height (Assume mm and s)
    value = value.split(' ')
    assert value[0] != '', "Check method, one or more fields left blank on a step."

    value[0] = eval(value[0])
    if len(value) > 1:
        if value[1] in units.keys():
            value[0] *= units[value[1]]
    return value[0]


class Step:
    """
    Standardize data object containing all the information needed for a given automation step
    """
    special_commands = ['auto_cell', 'gate', 'collect', 'manual_cell', 'sample']

    def __init__(self, line):
        self.well_location = []  # um, um
        self.outlet_height = 0  # mm
        self.inlet_height = 10  # mm
        self.pressure = False
        self.vacuum = False
        self.voltage = 5  # kV
        self.time = 0  # seconds
        self.special = ''
        self.data = False

        # Read step
        self.read_line(line)

    @staticmethod
    def _get_true_false(value):
        value = value.upper()
        if value == '1' or value == 'TRUE' or value == 'T':
            return True
        else:
            return False

    def read_line(self, line):
        """
        Column order needs to match the followign:
        Columns:
        Location, Outlet Height, Inlet Height, Pressure, Vacuum, Voltage, Time, Special

        :param line:
        :return:
        """
        # Split into columns and remove white space
        columns = line.rstrip('\n').split('\t')
        columns = [x.rstrip().lstrip() for x in columns]

        # add name
        self.name = columns[0]

        # Add Location
        self.well_location = [col.rstrip().lstrip() for col in columns[1].split(',')]

        # Add Outlet Height (Assume mm)
        self.outlet_height = get_standard_unit(columns[2])

        # Add Inlet Height
        self.inlet_height = get_standard_unit(columns[3])

        # Add Pressure and Vacuum
        self.pressure = self._get_true_false(columns[4])
        self.vacuum = self._get_true_false(columns[5])

        # Get Voltage
        self.voltage = get_standard_unit(columns[6])

        # Get time_data
        self.time = get_standard_unit(columns[7])

        # Get Special
        if columns[8].lower() in self.special_commands:
            self.special = columns[8]

        # Get Data
        self.data = self._get_true_false(columns[9])


class Method(object):
    """
    Creates a Method object that groups automation steps in a sequential order for automated analysis. Well locations
    can be any well identifier listed in the template object.

    An example config file is shown below:

    # Automated method for a CE System
    # Columns are delimited by tabs (not commas) and column order should be matched
    # Default units for outlet is cm, for inlet is mm, for voltage is kV for time is seconds,
    # You may enter in cm, mm, kv, s, min to specify other units
    METHOD
    name	location	outlet_height	inlet_height	pressure	vacuum	voltage	time	special	data
    rinse	"well_1, sample_1"	0 cm	25 mm	1	0	0.0 kV	6 s		0
    step1	well_2	 -5 cm	15 mm	0	0	0.5 kV	0.25 min		1

    """

    def __init__(self, method_file):
        self.method_steps = []
        self.open_file(method_file)
        self._step_index = 0

    def open_file(self, method_file):
        """
        Read a text configuration file (tab delimited) where each column is an attribute of a step.
        Columns:
        Location, Outlet Height, Inlet Height, Pressure, Vacuum, Voltage, Time, Special
        :param method_file:
        :return:
        """

        with open(method_file, 'r') as in_file:
            lines = in_file.readlines()
        method_lines = [x.rstrip('\n').replace('"', '') for x in lines]
        for idx, line in enumerate(method_lines):
            if line.find('METHOD') > -1:
                break
        method_lines = method_lines[idx + 2:]

        for line in method_lines:
            if line.count('\t') == 9:
                logging.info("Adding step {}".format(line))
                self.method_steps.append(Step(line))
            else:
                raise "Error in method file: {} is not the right number of columns".format(line)


class BasicTemplateShape(object):
    max_height = 100  # maximum height inlet can travel (mm)

    def __init__(self, line):
        self.name = ''
        self.shape = ''
        self.size = [1, 1]
        self.xy = [0, 0]
        self.read_line(line)
        self.color = 'red'
        self.height = 0

    def read_line(self, line):
        """
        Populate the fields of a well. Example should be:
        name \t
        :param line:
        :return:
        """
        # remove white space
        line = line.replace('[', '').replace(']', '')
        line = line.split('\t')
        line = [x.rstrip().lstrip() for x in line]

        # Get properties
        self.name = line[0]
        self.shape = line[1].lower()
        if self.shape == 'circle':
            self.size = float(line[2])
        elif self.shape == 'rectangle':
            self.size = [float(x) for x in line[2].split(',')]

        self.xy = [float(x) for x in line[3].split(',')]

    def draw_shape(self, scale=1):

        if self.shape == 'rectangle':
            return self._draw_rectangle()

    def _draw_rectangle(self):

        # Convert to Bounding Box coordinates
        xy = [x - x1 / 2 for x, x1 in zip(self.xy, self.size)]
        rect = plt.Rectangle(xy, self.size[0], self.size[1], facecolor=self.color)
        return rect

    def get_intersection(self, xx, yy):
        """
        Get values where a line of points xx,yy intersect with the shape.
        Returns the height of the shape if they intersect or zero if there is no intersection
        :param xx:
        :param yy:
        :return:
        """
        if self.shape == 'circle':
            return self._get_circle_intersection(xx, yy)
        else:
            return self._get_box_intersection(xx, yy)

    def _get_box_intersection(self, xx, yy):
        minx, maxx = self.xy[0] - self.size[0] / 2, self.xy[0] + self.size[0] / 2
        miny, maxy = self.xy[1] - self.size[1] / 2, self.xy[1] + self.size[1] / 2
        zz = [self.height if minx < x < maxx and miny < y < maxy else 0 for x, y in zip(xx, yy)]
        return zz

    def _get_circle_intersection(self, xx, yy):
        x0, y0 = self.xy
        r = self.size
        zz = [self.height if (x - x0) ** 2 + (y - y0) ** 2 <= r ** 2 else 0 for x, y in zip(xx, yy)]
        return zz


class Well(BasicTemplateShape):

    def __init__(self, line):
        super().__init__(line)


class Ledge(BasicTemplateShape):

    def __init__(self, line):
        super().__init__(line)
        self._add_height(line)

    def _add_height(self, line):
        line = line.split('\t')
        self.height = eval(line[4])
        self.color = str(self.height / self.max_height)


class Template(object):
    '''
    Data storage object for defining a template. Contains dictionaries of wells and ledges. Well names are used by
    Methods to define the location the stage should move to. Ledges are used to define a safe distance that capillary
    inlet should be at while moving over different areas of the template.

    Below is an example template config: Note the config is tab separated values.

    # Example Template File Format
    # Template files have three sections, ""SIZE"", """"WELLS"""" and """"LEDGES"""""""
    # ""SIZE should be defined before ""WELLS"" and ""WELLS should be defined before ""LEDGES"""
    # Wells contain XY coordinates for the XY stage to move to place well underneath capillary
    # XY units are in mm
    # Ledges contain Heights (in mm) that indicate a safe inlet height to travel at when crossing the specified area.
    # Size is dX,dY or dRadius depending on if 'rectangle' or 'circle' is the shape """

    DIMENSIONS
    Left X	Lower Y	Right X	Upper Y
    160	110	0	0
    WELLS
    Name	Shape	Size	XY
    sample_1	circle	2.5	"0,0"
    well_1	circle	2	"100,100"
    well_2	circle	2.4	"25,85"
    LEDGES
    name	shape	size	XY	z
    pcr_tubes	rectangle	"50,50"	"20,20"	17
    base	rectangle	"100,100"	"100,100"	2.5
    '''

    def __init__(self, template_file=r'D:\Scripts\AutomatedCE\config\template-test.txt'):
        self.ledges = {}
        self.wells = {}
        self.template_size = [0, 0, 1, 1]
        # Keep the template file path for saving purposes
        self._template_file = template_file
        self.open_file(template_file)

    def open_file(self, file):
        """
        Read Template File
        :param file:
        :return:
        """

        with open(file, 'r') as in_file:
            lines = in_file.readlines()

        # Remover Returns + String indicators
        lines = [x.rstrip('\n').rstrip('\t').replace('"', '') for x in lines]
        size_lines = lines[lines.index('DIMENSIONS'):lines.index('WELLS')]
        well_lines = lines[lines.index('WELLS'):lines.index('LEDGES')]
        ledge_lines = lines[lines.index('LEDGES'):]
        self.template_size = self._get_dimensions(size_lines)
        self.wells = self._add_shapes(well_lines, 'well')
        self.ledges = self._add_shapes(ledge_lines, 'ledge')

    @staticmethod
    def _get_dimensions(lines):
        assert len(lines) > 2, "ERR: No template DIMENSION specified."
        lines = lines[2]
        lines = lines.split('\t')
        [lx, ly, ux, uy] = float(lines[0]), float(lines[1]), float(lines[2]), float(lines[3])
        return [lx, ly, ux, uy]

    @staticmethod
    def _add_shapes(lines, shape):
        """
        Create a template object shape using the lines from a template file
        :param lines:
        :param shape:
        :return:
        """
        shapes = {}
        # Make sure we have more than the identifier and headers
        if len(lines) > 2:
            lines = lines[2:]
            for line in lines:
                # Add the appropriate shape
                if shape == 'well':
                    new_shape = Well(line)
                else:
                    new_shape = Ledge(line)
                shapes[new_shape.name] = new_shape
        return shapes

    def draw_template(self):
        fig, ax = plt.subplots()
        ax.set_ylim(self.template_size[1], self.template_size[3])
        ax.set_xlim(self.template_size[0], self.template_size[2])

        for _, shape in self.wells.items():
            ax.add_patch(shape.draw_shape())
        plt.show()
        return fig, ax

    def get_intersection(self, xx, yy):

        zz = np.zeros(len(xx))
        for _, ledge in self.ledges.items():
            zz += ledge.get_intersection(xx, yy)
        return zz

    def get_max_ledge(self):
        z_max = -1
        for _, ledge in self.ledges.items():
            if ledge.height > z_max:
                z_max = ledge.height
        return z_max


class AutoRun:
    """
    Class that organizes and starts the calls for an automated Run
    """

    def __init__(self, system: CESystem()):
        """
        Creates and AutoRun object that groups templates and methods together and coordinates the actions on a
        CE system object so that an automated run can take place.

        :param system:  CE system object that will be automated
        """
        self.system = system  # L3 CE Systems object
        self.methods = []
        self.gate = GateSpecial()
        self.repetitions = 1
        self.repetition_style = 'method'
        self._queue = Queue()
        self.is_running = threading.Event()
        self.traced_thread = Util.TracedThread()
        self.traced_thread.name = 'AutoRun'
        self.data_dir = get_system_var('data_dir')[0]
        self.safe_enabled = False
        self.template = None
        self.template: Template
        self.path_information = PathTrace()

    def add_method(self, method_file=r'default'):
        """
        Adds a method using a method config file to define the steps
        :param method_file: path to method config file
        :return:
        """
        if method_file.lower() == "default":
            method_file = os.path.abspath(os.path.join(os.getcwd(), '..', 'config\\method-test.txt'))
        self.methods.append(Method(method_file))

    def set_template(self, template_file=r'default'):
        """
        Sets the template that should be used. Uses a template config file to definen the well positions and
        ledge heights.
        :param template_file: path to template config file
        :return:
        """
        if template_file.lower() == "default":
            template_file = os.path.abspath(os.path.join(os.getcwd(), '..', 'config\\template-test.txt'))
        self.template = Template(template_file)

    def start_run(self, simulated=False):
        """
        Start a run. This creates a thread-safe queue object and sets the run flag.
        A run can be created in two style types. The first will run
        :param rep_style:
        :return:
        """
        assert self.template is not None, "Template has not been defined"
        rep_style = self.repetition_style.lower()
        self.repetitions = int(self.repetitions)
        if rep_style == 'sequence':  # run through all methods in the list before repeating
            for rep in range(self.repetitions):
                for method in self.methods:
                    for step in method.method_steps:
                        self._queue.put((step, rep))

        elif rep_style == 'method':  # repeat each method before moving to the next method in the list
            for method in self.methods:
                for rep in range(self.repetitions):
                    for step in method.method_steps:
                        self._queue.put((step, rep))

        self.traced_thread = Util.TracedThread(target=self._run, args=(simulated,))
        self.traced_thread.name = 'AutoRun'
        self.traced_thread.start()
        self.is_running.set()

    def error_message(self, state, process):
        if not state:
            logging.error("Error while moving during {}. Aborting".format(process))

    def _run(self, simulated=False):
        """
        Makes the individual step calls for a compiled method sequence.
        :return:
        """
        while not self._queue.empty():
            (step, rep) = self._queue.get()

            # Get the move positions
            xyz0, xyz1, well_name = self._get_move_positions(step, rep)

            self.path_information.append(f"Performing Step '{step.name}' at rep {rep}")
            self.path_information.append(f"Preparing for move to well {well_name}")
            # Move the System Safely
            if self.safe_enabled:
                state = Trajectory.SafeMove(self.system, self.template, xyz0, xyz1, simulated, self.path_information).move()
            else:
                state = Trajectory.StepMove(self.system, self.template, xyz0, xyz1, simulated, self.path_information).move()
            self.error_message(state, "System Move")

            # Move the inlet
            self.path_information.append(f"Outlet Height set to {step.outlet_height} mm")
            if not simulated:
                self.system.outlet_z.set_z(step.outlet_height)

                # Wait for both Z Stages to stop moving
                state = self.system.inlet_z.wait_for_target(xyz1[2])
                self.error_message(state, "Inlet Move Down")

                state = self.system.outlet_z.wait_for_target(step.outlet_height)
                self.error_message(state, "Outlet Move Down")

            # Run the special command for injections here
            after_special = True  # change this to false if we don't need to run the timed part of the step after

            # Run the special for Gating the separation here (get peak areas and set the next collection well)

            # Run the timed step
            if after_special:
                self._timed_step(step, simulated)
            # Output the electropherogram data
            if step.data:
                file_path = FileIO.get_data_filename(step.name, self.data_dir)
                self.path_information.append(f"Saving Data to {file_path}")
                if not simulated:
                    FileIO.OutputElectropherogram(self.system, file_path)

    def _get_move_positions(self, step, rep):
        """
        Gets the current and final positions for the step movement. Special collection method can override the final
        xy position.
        """

        # Get starting positions
        x, y = self.system.xy_stage.read_xy()
        z = self.system.inlet_z.read_z()
        xyz0 = [x, y, z]

        # Get Ending Positions, Special command for collection will override this
        x, y = self.template.wells[step.well_location[rep % len(step.well_location)]].xy
        z = step.inlet_height
        xyz1 = [x, y, z]

        return xyz0, xyz1, step.well_location[rep % len(step.well_location)]

    def _timed_step(self, step, simulated):
        """
        Run a timed step, applying the pressure, vacuum, and voltage as specified by the step
        :param step:
        :return:
        """
        # Keep track of the time_data we started applying forces
        st = time.time()

        # Apply Hydrodynamic Forces
        self.path_information.append(f"Pressure state changed to {step.pressure}, Vaccuum state changed to {step.vacuum}")
        if not simulated:
            if step.pressure:
                self.system.outlet_pressure.rinse_pressure()
            elif step.vacuum:
                self.system.outlet_pressure.rinse_vacuum()
            else:
                self.system.outlet_pressure.release()

        # Apply Electrokinetic Forces
        self.path_information.append(f"Voltage set to {step.voltage}")
        if not simulated:
            self.system.high_voltage.set_voltage(step.voltage, channel='default')
            self.system.high_voltage.start()
            self.system.detector.start()

        self.path_information.append("Timed run for {} s".format(step.time))
        # Wait while running
        while time.time() - st < step.time and self.is_running.is_set() and not simulated:
            time.sleep(0.05)

        # Stop applying the forces
        self.path_information.append(f"Stopping timed run after {time.time()-st} s")
        if not simulated:
            self.system.high_voltage.stop()
            self.system.detector.stop()

        self.path_information.append("Stopping timed run at {}".format(time.time() - st))
        threading.Thread(target=self.system.outlet_pressure.stop, name='PressureStop').start()

    def stop_run(self):
        """
        Stops the automated run and calls the System CE stop command.
        Not sure this Trace will be safe for the threads and hardware. If the thread is stopped while sending a command
        it may create an error.
        :return:
        """
        # Kill the thread using the trace and wait till the thread has been killed before continuing
        self.traced_thread.kill()
        self.traced_thread.join()
        self.system.stop_ce()


class PathTrace:
    """
    Stores the path (all moves and positions) of the current run and calls the assined callbacks when new information
    is added to the history.
    """

    def __init__(self):
        super().__init__()
        self._callbacks = []
        self.path = []

    def add_callback(self, function):
        """
        New callback function is added to the list of callbacks
        :param function: function to call, should accept single string parameter
        """
        self._callbacks.append(function)

    def append(self, information: str):
        """
        Adds new piece of information to the list of path information. Sends the information to the callbacks.
        :param information:
        :return:
        """
        self.path.append(information)
        for fnc in self._callbacks:
            fnc(information)

    def extend(self, data):
        """
        Adds multiple bits of data to the list of path information, sends the information to the callbacks
        :param data: list of string information to be added
        :return:
        """
        for information in data:
            self.append(data)


class GateSpecial:
    """
    Analyzes the electropherogram following a separation and determines where to send the next collection XY well

    Start by defining peaks using the add_peak function. Once peaks have been defined use the set_gate function.

    gates = GateSpecial()
    gates.add_peak('standard', 20.0, 29.5)
    gates.add_peak('sample', 45.5, 60)
    gates.set_gate(0.5, 'well_1', 'sample', 'standard')
    """

    def __init__(self):
        self.gates = []
        self.peaks = {}
        self.target = ''

    def add_peak(self, peak_name: str, start_time: float, stop_time: float):
        """
        Adds a new peak location that can be used when creating gates. Time start and stop should be tolerant
        for any migration differences throughout the course of the experiment.

        :param peak_name: identifier for this peak, should be unique
        :param start_time: time point the peak starts at
        :param stop_time: time point the peak ends at
        :return:
        """
        self.peaks[peak_name] = (start_time, stop_time)

    def set_gate(self, ratio: float, well_name: str, peak1: str, *peaks: str):
        """
        Sets the gate parameters.

        Ratio is the ratio of peak 1 to the sum of peak 1 and all the peaks listed in peaks. If the value is greater
        than the ratio it will set the next collection to the well_name specified.

        example input:
        x.set_gates(0.4, 'well_2', 'pk1', 'pk2', 'pk3')

        :param ratio: value between 0 and 1, gate ratio for pk1/(sum(peaks,peak1))
        :param well_name: name of well in the template
        :param peak1: peak identifier set by add_time_bounds
        :param peaks: one or more peak identifiers set by add_time_bounds, should not include peak1
        :return:
        """
        self.gates.append((ratio, well_name, peak1, peaks))

    def check_gates(self, time_data: np.ndarray, rfu_data: np.ndarray):
        """
        Checks if there are any gates whose requirements are met by the electropherogram data.
        Peak areas are time and baseline corrected from the Electropherograms module.

        :param time_data: array of time_data points for an electropherogram
        :param rfu_data: array of data points for an electropherogram
        :return: whether any gate condition was met
        :rtype: bool
        """

        for ratio, well_name, peak1, peaks in self.gates:
            # Get the area of the first peak
            peak_start, peak_stop = self.peaks[peak1]
            peak1_area = Electropherogram.get_corrected_peak_area(time_data, rfu_data, peak_start, peak_stop)
            total_area = peak1_area
            # Get the area of the remaining peaks
            for peak_start, peak_stop in peaks:
                total_area += Electropherogram.get_corrected_peak_area(time_data, rfu_data, peak_start, peak_stop)
            if peak1_area / total_area < ratio:
                self.target = well_name
                return True
        self.target = ""
        return False


class TemplateMaker:

    def __init__(self):
        """
        :param system: L3 System object for CE Systems
        """
        self.wells = {}
        self.ledges = {}
        self.dimensions = []
        self.header = ""

    def add_array(self, label, xy1, xy2, rows, columns, diameter, shape='circle'):
        """
        Adds an array of vials. Vials will have label with incrementing number after the name.
         Adds to the dictionary  of wells.
        :param label: identifer to be used for these wells ("Inlet, Sample, etc...")
        :param xy1: xy position of the first well
        :param xy2: xy position of the second well
        :param rows: how many rows (y direction) for the array
        :param cols: how many columns (x direction) for the array
        :param diameter: diameter of the wells
        :param shape: type of shape to create an array of (circle currenlty only shape supported)
        """

        x1, y1 = xy1
        x2, y2 = xy2
        delta_x = (x2 - x1) / columns
        delta_y = (y2 - y1) / rows

        for x, letter in zip(range(1, columns + 1), string.ascii_lowercase):
            for y in range(rows):
                center = [x1 + delta_x * x, y1 + delta_y * y]

                name = self.get_original_name(f"{label}_{letter}{y}")
                self.wells[name] = [shape, diameter, center]

    def get_original_name(self, name, type='well'):
        """
        Returns a unique name for dictionary of wells
        :param name: name to check if it is unique
        :return: unique name
        """
        original_name = name
        idx = 0
        types = {'well': self.wells, 'ledge': self.ledges}
        while name in types[type].keys():
            name = original_name + f"{idx}"
        return name

    def add_well(self, name, xy1, size, shape):
        """
        Adds a well to the dictionary
        :param name: well label, should be unique otherwise a number will be appended.
        :param xy1: xy position of the center of the well
        :param size: the size of the shape, either a tuple for rectangles, or float for circles
        :param shape: type of shape to add
        :return:
        """

        name = self.get_original_name(name)
        self.wells[name] = [shape, size, xy1]

    def add_ledge(self, name, xy1, size, shape, height):
        """
        Adds a ledge to the dictionary.
        :param name: ledge label, should be unique otherwise a number will be appended to make it unique
        :param xy1: xy position of the ledge shape
        :param size: size of the ledge
        :param shape: shape of the ledge
        :param height: height of the ledge
        :return:
        """
        name = self.get_original_name(name)
        self.ledges[name] = [shape, size, xy1, height]

    def save_to_file(self, filepath):
        """
        Saves the template information, including template dimensions, well information, and ledge information
        to a Template File
        :param filepath: filepath to save the file
        :param header: String of header information, hash '#' symbol will be appended to each new line character.
        :return: True if successful, False if missing dimensions
        """
        if not self.dimensions:
            logging.warning("No dimensions set, please set dimensions")
            return False

        with open(filepath, 'w') as f_out:
            f_out.write(self.header.replace('\n', '\n#'))
            f_out.write("\n")
            f_out.write("DIMENSIONS\n Left X\tLower Y\tRight X\tUpper Y\n")
            x1, y1, x2, y2 = self.dimensions
            f_out.write(f"{x1}\t{y1}\t{x2}\t{y2}\n")
            f_out.write("WELLS\nName\tShape\tSize\tXY\n")
            for name, info in self.wells.items():
                shape, size, xy1 = info
                f_out.write(f"{name}\t{shape}\t{size}\t{xy1}\n")
            f_out.write("LEDGES\nName\tShape\tSize\tXY\tHeight\n")
            for name, info in self.ledges.items():
                shape, size, xy, height = info
                f_out.write(f"{name}\t{shape}\t{size}\t{xy}\t{height}\n")
        return True

    def add_dimension(self, left_x, lower_y, right_x, upper_y):
        """
        Adds dimensions for the overall template
        :param left_x:
        :param lower_y:
        :param right_x:
        :param upper_y:
        :return:
        """
        self.dimensions = [left_x, lower_y, right_x, upper_y]


class AutoSpecial:
    pass


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import numpy as np
    import logging

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    system = CESystem()
    system.load_config()
    system.open_controllers()
    system.detector.set_oversample_frequency(20000, 10)
    auto = AutoRun(system)
    auto.add_method()
    auto.set_template()
    auto.repetitions = 2
    auto.start_run()
