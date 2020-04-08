from abc import ABC, abstractmethod
from L1 import Controllers
from L2 import PressureControl


class Director(ABC):
    """
    Directs the construction of the utilities object for the Systems class
    """

    def __init__(self):
        self._utility_builder = None
        self._controller_builder = None
        self._interpreter = None

    @abstractmethod
    def construct(self, config_file):
        pass

    def get_constructed_object(self):
        return self._utility_builder.constructed_object()


class Builder(ABC):
    """
    Our constructed object will be
    """

    def __init__(self, constructed_object):
        self.constructed_object = constructed_object

    def get_object(self):
        return self.constructed_object


class SystemsObject(object):

    def __init__(self):
        self.fields = {}

    def __getitem__(self, item):
        return self.fields[item]

    def __setitem__(self, key, value):
        self.fields[key] = value


class ControllerBuilder(Builder):

    def __init__(self):
        super().__init__(SystemsObject())

    def add_arduino(self, settings):
        self.constructed_object.fields[settings[1]] = Controllers.ArduinoController(settings[3])

    def add_simulated(self, settings):
        self.constructed_object.fields[settings[1]] = Controllers.SimulatedController(settings[3])


class UtilityBuilder(Builder):

    def __init__(self):
        super().__init__(SystemsObject())
        self._pressure_factory = PressureControl.PressureControlFactory()

    def add_pressure(self, controller, settings):
        self.constructed_object.fields['pressure'] = self._pressure_factory.build_object(controller)


class ConcreteDirector(Director):
    """ Builds the object that composes the Systems object in layer 3 of automation """

    def __init__(self):
        super().__init__()
        # Create the builders and set the interpreter
        self._utility_builder = UtilityBuilder()
        self._controller_builder = ControllerBuilder()
        self.set_interpreter(option='text')

    def set_interpreter(self, option):
        """
        Set the interpreter to be used to read the config file
        :param option: string [ options are: 'text']
        :return:
        """
        if option == 'text':
            self._interpreter = TextInterpreter()
        else:
            raise ValueError('Interpreter options are: "text" ')

    def construct(self, config_file):
        """
        Build the CE systems object using a config file. Config file type should match the interpreter settings (ie
        if using a text based config file use the 'text' interpreter). First build and create the controller objects
        then build and create utility objects.

        Returns the Utilities object

        :param config_file: string (filepath to the config file)
        :return:
        """
        controller_list, utility_list = self._interpreter.read_config(filepath=config_file)
        self._build_controllers(controller_list)
        self._build_utilities(utility_list, self._controller_builder.constructed_object)
        return

    def _build_controllers(self, controller_list):
        for controller in controller_list:
            settings = controller.split(',')
            control_type = settings[2].lower()
            if control_type == 'arduino':
                self._controller_builder.add_arduino(settings)
            elif control_type == 'simulated':
                self._controller_builder.add_simulated(settings)
            else:
                raise ValueError('Controller options are: "arduino", "simulated"')
        return self._controller_builder.get_object()

    def _build_utilities(self, utility_list, controllers):
        """
        Build the utility objects that compose the 2nd layer of automation
        :param utility_list: list of utility settings from a config file
        :param controllers:
        :return:
        """
        for utility in utility_list:
            settings = utility.split(',')
            utility_type = settings[1]
            controller = controllers[settings[2]]
            if utility_type == 'pressure':
                self._utility_builder.add_pressure(controller, settings)
            else:
                raise ValueError('Utility options are: "pressure"')


class Interpreter(ABC):
    """Interprets a config file"""

    @abstractmethod
    def read_config(self, filepath):
        """
        Returns a tuple containing a list of controllers and utilities to build
        :param filepath:
        :return: (['controller...'], ['utility...'])
        """
        pass


class TextInterpreter():
    """ Interprets a text config file according to the following rules:

    Define the controllers in the lines following "CONTROLLERS", specifying the type of controller and the port
    Format for controllers are: controller,<ID-Name>,<Controller-Type>,<Port>
    ID-name should be string identifier and should start with a alpha-numeric character
    Acceptable controller-types are: arduino, simulated

    Define the hardware utilities (individual hardware components) in the lines following "UTILITIES"
    Utility definitions follow the format utility,<utility-type>, <controller-id>, <arg1, arg2, arg3,...>
    Utility-type are:
           pressure            |   provides pressure control for the outlet
           xystage             |   provides XY stage control for a motorized microscope staage
     controller-id should match an ID specified under CONTROLLERS

    """

    def read_config(self, filepath):
        """
        Read and return the controller and utility settings from a text file specified by filepath
        :param filepath: string (filepath to the config file)
        :return : tuple ( [controllers...], [utilities...] )
        """
        with open(filepath, 'r') as in_file:
            cfg_list = in_file.readlines()
        cfg_list = [x.rstrip('\n') for x in cfg_list]
        controllers = self._get_controllers(cfg_list)
        utilities = self._get_utilities(cfg_list)
        return controllers, utilities

    @classmethod
    def _get_controllers(cls, cfg_list):
        "Returns a list of controller settings"
        controllers = cfg_list[cfg_list.index('CONTROLLERS') + 1:cfg_list.index("UTILITIES")]
        return cls._remove_comments(controllers)

    @classmethod
    def _get_utilities(cls, cfg_list):
        "Returns a list of utility settings"
        utilities = cfg_list[cfg_list.index("UTILITIES") + 1:]
        return cls._remove_comments(utilities)

    @staticmethod
    def _remove_comments(lines):
        """ Removes white space and comments """
        new_lines = []
        for line in lines:
            line = line.split('#')[0]
            if len(line) > 0:
                line = line.rstrip().lstrip()
                new_lines.append(line)
        return new_lines


if __name__ == "__main__":
    director = ConcreteDirector()
    director.construct(r"D:\Scripts\AutomatedCE\config\Test-System.cfg")
