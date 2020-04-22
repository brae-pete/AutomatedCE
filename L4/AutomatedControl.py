"""
This file contains the code necessary to run automated control over a capillary electrophoresis system.

"""
import threading
from queue import Queue
from L3.SystemsBuilder import CESystem
from L4 import Util, Trajectory
import matplotlib.pyplot as plt
import numpy as np


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

        # Read step
        self.read_line(line)

    @staticmethod
    def _get_standard_unit(value):
        """
        Adjusts the value to a standard value. Standard values do not need to bea dded to the units dictionary.
        The scales for each value in the dictionary should be a multiplication scalar factor to reach the standard
        unit scale.

        Standard units are: mm (for distance), volts for Voltage, and seconds for time.

        Example:
        For value == '33 cm'
        program returns: 3.3 * units['cm'] or 3.3 * 10 = 33

        :param value: str
        :return: float or int
        """
        units = {'cm': 10, 'kv': 1000, 'min': 60}
        # Get Height (Assume mm)
        value = value.split(' ')
        value[0] = eval(value[0])
        if len(value) > 1:
            if value[1] in units.keys():
                value[0] *= units[value[1]]
        return value[0]

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
        columns = [x.rstrip('').lstrip('') for x in columns]

        # Add Location
        self.well_location = [col.rstrip().lstrip() for col in columns[0].split(',')]

        # Add Outlet Height (Assume mm)
        self.outlet_height = self._get_standard_unit(columns[1])

        # Add Inlet Height
        self.inlet_height = self._get_standard_unit(columns[2])

        # Add Pressure and Vacuum
        self.pressure = self._get_true_false(columns[3])
        self.vacuum = self._get_true_false(columns[4])

        # Get Voltage
        self.voltage = self._get_standard_unit(columns[5])

        # Get time
        self.time = self._get_standard_unit(columns[6])

        # Get Special
        if columns[7].lower() in self.special_commands:
            self.special = columns[7]


class Method(object):

    def __init__(self, method_file):
        self.open_file(method_file)
        self.method_steps = []
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
        method_lines = method_lines[method_lines.index('METHOD') + 2:]
        self.method_steps = [Step(line) if len(line) == 8 else self._step_error(line) for line in method_lines]

    @staticmethod
    def _step_error(line):
        raise "Error in method file: {} is not the right number of columns".format(line)


class BasicTemplateShape(object):

    max_height = 100 # maximum height inlet can travel (mm)

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
        xy = [x-x1/2 for x, x1 in zip(self.xy, self.size)]
        rect = plt.Rectangle(xy,self.size[0], self.size[1], facecolor = self.color)
        return rect

    def get_intersection(self, xx,yy):
        """
        Get values where a line of points xx,yy intersect with the shape.
        Returns the height of the shape if they intersect or zero if there is no intersection
        :param xx:
        :param yy:
        :return:
        """
        if self.shape == 'circle':
            return self._get_circle_intersection(xx,yy)
        else:
            return self._get_box_intersection(xx,yy)

    def _get_box_intersection(self, xx,yy):
        minx, maxx = self.xy[0]-self.size[0]/2, self.xy[0]+self.size[0]/2
        miny, maxy = self.xy[1]-self.size[1]/2, self.xy[1]+self.size[1]/2
        zz = [self.height if minx < x < maxx and miny < y < maxy else 0 for x, y in zip(xx, yy)]
        return zz

    def _get_circle_intersection(self, xx, yy):
        x0,y0 = self.xy
        r = self.size
        zz = [self.height if (x-x0)**2 + (y-y0)**2 <= r**2 else 0 for x, y in zip(xx,yy)]
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
        self.color = str(self.height/self.max_height)


class Template(object):
    """
    Data storage object for defining a template
    """

    def __init__(self, template_file=r'D:\Scripts\AutomatedCE\config\template-test.txt'):
        self.ledges = {}
        self.wells = {}
        self.template_size = [0,0,1,1]
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
        return [lx,ly,ux, uy]

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
            lines=lines[2:]
            for line in lines:
                # Add the appropriate shape
                if shape == 'well':
                    new_shape = Well(line)
                else :
                    new_shape = Ledge(line)
                shapes[new_shape.name] = new_shape
        return shapes

    def draw_template(self):
        fig, ax = plt.subplots()
        ax.set_ylim(self.template_size[1],self.template_size[3])
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


class AutoRun:
    """
    Class that organizes and starts the calls for an automated Run
    """
    template: Template

    def __init__(self, system: CESystem):
        self.system = system  # L3 CE Systems object
        self.methods = []
        self.repetitions = 1
        self._queue = Queue()
        self.is_running = threading.Event()
        self.traced_thread = Util.TracedThread()
        self.traced_thread.name = 'AutoRun'

    def add_method(self, method_file=r'D:\Scripts\AutomatedCE\config\method-test.txt'):
        self.methods.append(Method(method_file))

    def start_run(self, rep_style='sequence'):
        """
        Start a run. This creates a thread-safe queue object and sets the run flag.
        A run can be created in two style types. The first will run
        :param rep_style:
        :return:
        """

        if rep_style == 'sequence':
            for rep in range(self.repetitions):
                for method in self.methods:
                    for step in method:
                        self._queue.put((step, rep))

        else:
            for method in self.methods:
                for rep in range(self.repetitions):
                    for step in method:
                        self._queue.put((step,rep))

        self.traced_thread = Util.TracedThread(target=self._run)
        self.traced_thread.name = 'AutoRun'
        self.traced_thread.start()

    def _run(self):
        """
        Makes the individual step calls for a compiled method sequence.
        :return:
        """
        while not self._queue.empty():
            (step, rep) = self._queue.get()

            # Get starting positions
            x, y = self.system.xy_stage.read_xy()
            z = self.system.inlet_z.read_z()
            xyz0 = [x,y,z]

            # Get Ending Positions
            x, y = self.template.wells[step.well_location[step.well_location[rep]]]
            z = step.inlet_height
            xyz1 = [x, y, z]

            Trajectory.safe_move(self.system, xyz0, xyz1, self.template)



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




if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import numpy as np





