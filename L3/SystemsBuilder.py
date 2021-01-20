import logging
import os
from abc import ABC, abstractmethod
from L1 import Controllers, DAQControllers
from L2 import PressureControl, XYControl, ZControl, HighVoltageControl, DetectorControl, LaserControl, \
    FilterWheelControl, ShutterControl, CameraControl, LightControl


class Director(ABC):
    """
    Directs the construction of the controllers and utilities object for the Systems class.
    Aside from construction contains two get functions to get the controllers and utilities object.
    These objects are like dictionaries that contain a key (either the type of utility or daqcontroller id) and
    the corresponding L2 or L1 class object.

    Google "Director Builder design pattern python" to get somewhat of an idea of how this was organized.
    """

    def __init__(self):
        self._utility_builder = None
        self._controller_builder = None
        self._interpreter = None

    @abstractmethod
    def construct(self, config_file):
        pass

    def get_utilities(self):
        return self._utility_builder.constructed_object.fields

    def get_controllers(self):
        return self._controller_builder.constructed_object.fields


class Builder(ABC):
    """
    Basic Builder Pattern
    """

    def __init__(self, constructed_object):
        self.constructed_object = constructed_object

    def get_object(self):
        return self.constructed_object


class ControlledObjects(object):
    """
    This contains a dictionary holding either the L1 or L2 objects.
    Set and get have defined so that you can treat treat this object like a dictionary

    For example:
    sys_obj = SystemsObject()
    sys_obj['new_item']=object() # Set a key equal to an object
    print(sys_obj['new_item']) # Retrieve the object for inspection
    """

    def __init__(self):
        self.fields = {}

    def __getitem__(self, item):
        return self.fields[item]

    def __setitem__(self, key, value):
        self.fields[key] = value


class ControllerBuilder(Builder):
    """
    Builds the daqcontroller Systems object. A separate add_<daqcontroller-type> function should be included for each
    daqcontroller listed in L1.Controllers. The add_* functions will create the daqcontroller object using the settings passed
    from a config file line. This object will be added to the constructed_object or the systems object.
    """

    def __init__(self):
        super().__init__(ControlledObjects())

    def add_arduino(self, settings):
        self.constructed_object.fields[settings[1]] = Controllers.ArduinoController(settings[3])

    def add_simulated(self, settings):
        self.constructed_object.fields[settings[1]] = Controllers.SimulatedController(settings[3])

    def add_micromanager(self, settings):
        if len(settings) < 4:
            raise ValueError('No Config file was provided: {}'.format(settings))
        self.constructed_object.fields[settings[1]] = Controllers.MicroManagerController(settings[2], settings[3])

    def add_prior(self, settings):
        self.constructed_object.fields[settings[1]] = Controllers.PriorController(settings[3])

    def add_digilent(self, settings):
        self.constructed_object.fields[settings[1]] = DAQControllers.DigilentDaq()

    def add_nidaqmx(self, settings):
        self.constructed_object.fields[settings[1]] = DAQControllers.NiDaq()

    def add_simulated_daq(self, settings):
        self.constructed_object.fields[settings[1]] = DAQControllers.SimulatedDaq()

    def add_kinesis(self, settings):
        controller = Controllers.SimulatedController()
        controller.id = 'kinesis'
        controller.port = settings[3]
        self.constructed_object.fields[settings[1]] = controller

    def add_pycromanager(self, settings):
        if len(settings) < 4:
            raise ValueError("No config was provided: {}".format(settings))
        self.constructed_object.fields[settings[1]] = Controllers.PycromanagerController(settings[2], settings[3])

    def add_lumencor(self, settings):
        self.constructed_object.fields[settings[1]] = Controllers.LumencorController(settings[3])



class UtilityBuilder(Builder):
    """
    Builds the utilities Systems object. A separate add_<utility-type> function should be included for each type of
    utility listed in L2. The corresponding factory for the utility should be used passing the daqcontroller that will be
    used for that utility. The add_* functions will create the utility object using the settings passed
    from a config file line. This object will be added to the constructed_object or the systems object.

    A single systems object can have multiple of the same type of utility classes as long as the roles have unique
    identifies. If roles are matching, the role whose utility was created last will overwrite the other matching role.


    """

    def __init__(self):
        super().__init__(ControlledObjects())
        self._pressure_factory = PressureControl.PressureControlFactory()
        self._xy_factory = XYControl.XYControlFactory()
        self._z_factory = ZControl.ZControlFactory()
        self._high_voltage_factory = HighVoltageControl.HighVoltageFactory()
        self._detector_factory = DetectorControl.DetectorFactory()
        self._laser_factory = LaserControl.LaserFactory()
        self._filter_wheel_factory = FilterWheelControl.FilterWheelFactory()
        self._shutter_factory = ShutterControl.ShutterFactory()
        self._camera_factory = CameraControl.CameraFactory()
        self._rgb_factory = LightControl.RGBControlFactory()

    def add_pressure(self, controller, settings):
        role = settings[3]
        self.constructed_object.fields[role] = self._pressure_factory.build_object(controller, role)

    def add_xy(self, controller, settings):
        role = settings[3]
        self.constructed_object.fields[role] = self._xy_factory.build_object(controller, role)

    def add_z(self, controller, settings):
        """
         Add a Z stage to the configuration.
         Settings order: Utility, controller_id, zstage, *key, *value

         keywords:
         invert: -1 to invert the direction \n
         scale: what to scale the microcontroller values by to get mm \n
         offset: when the controller is homed, what offset should be added to the home position \n
         default: default height to move to after homing \n
         min_z :lowest height to move to \n
         max_z: highest height oto move to \n

        :param controller:
        :param settings:
        :return:
        """
        role = settings[3]
        options = settings[4:]
        kwargs = {options[key]: options[key + 1] for key in range(0,len(options), 2)}
        self.constructed_object.fields[role] = self._z_factory.build_object(controller, role, **kwargs)

    def add_high_voltage(self, controller, settings):
        role = settings[3]
        self.constructed_object.fields[role] = self._high_voltage_factory.build_object(controller, role, settings)

    def add_detector(self, controller, settings):
        role = settings[3]
        self.constructed_object.fields[role] = self._detector_factory.build_object(controller, role, settings)

    def add_laser(self, controller, settings):
        role = settings[3]
        self.constructed_object.fields[role] = self._laser_factory.build_object(controller, role, settings)

    def add_filter_wheel(self, controller, settings):
        role = settings[3]
        self.constructed_object.fields[role] = self._filter_wheel_factory.build_object(controller, role)

    def add_shutter(self, controller, settings):
        role = settings[3]
        self.constructed_object.fields[role] = self._shutter_factory.build_object(controller, role)

    def add_camera(self, controller, settings):
        role = settings[3]
        self.constructed_object.fields[role] = self._camera_factory.build_object(controller, role)

    def add_rgb(self, controller, settings):
        role = settings[3]
        self.constructed_object.fields[role] = self._rgb_factory.build_object(controller, role)


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
        if using a text based config file use the 'text' interpreter). First build and create the daqcontroller objects
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
        """
        Determine which daqcontroller to add according to the config file.
        :param controller_list:
        :return:
        """
        for controller in controller_list:
            settings = controller.split(',')
            control_type = settings[2].lower()
            if control_type == 'arduino':
                self._controller_builder.add_arduino(settings)
            elif control_type == 'simulated':
                self._controller_builder.add_simulated(settings)
            elif control_type == 'micromanager':
                self._controller_builder.add_micromanager(settings)
            elif control_type == 'prior':
                self._controller_builder.add_prior(settings)
            elif control_type == 'digilent':
                self._controller_builder.add_digilent(settings)
            elif control_type == 'simulated_daq':
                self._controller_builder.add_simulated_daq(settings)
            elif control_type == 'nidaqmx':
                self._controller_builder.add_nidaqmx(settings)
            elif control_type == 'kinesis':
                self._controller_builder.add_kinesis(settings)
            elif control_type == 'pycromanager':
                self._controller_builder.add_pycromanager(settings)
            elif control_type == 'lumencor':
                self._controller_builder.add_lumencor(settings)
            else:
                raise ValueError('Entered invalid controller: {}'.format(control_type))
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
            #print(settings)
            settings=[x.split('&')  if ('&' in x) else x for x in settings]
            #print(settings)
            utility_type = settings[2]
            if type(settings[1]) is list:
                controller = [controllers[x] for x in settings[1]]
            else:
                controller = controllers[settings[1]]
            if utility_type == 'pressure':
                self._utility_builder.add_pressure(controller, settings)
            elif utility_type == 'xy':
                self._utility_builder.add_xy(controller, settings)
            elif utility_type == 'z':
                self._utility_builder.add_z(controller, settings)
            elif utility_type == 'high_voltage':
                self._utility_builder.add_high_voltage(controller, settings)
            elif utility_type == 'detector':
                self._utility_builder.add_detector(controller, settings)
            elif utility_type == 'laser':
                self._utility_builder.add_laser(controller, settings)
            elif utility_type == 'filter_wheel':
                self._utility_builder.add_filter_wheel(controller, settings)
            elif utility_type == 'shutter':
                self._utility_builder.add_shutter(controller, settings)
            elif utility_type == 'camera':
                self._utility_builder.add_camera(controller, settings)
            elif utility_type == 'rgb':
                self._utility_builder.add_rgb(controller,settings)
            else:
                raise ValueError('Entered invalid utility: {}'.format(utility_type))


class Interpreter(ABC):
    """Interprets a config file"""

    @abstractmethod
    def read_config(self, filepath):
        """
        Returns a tuple containing a list of controllers and utilities to build
        :param filepath:
        :return: (['daqcontroller...'], ['utility...'])
        """
        pass


class TextInterpreter:
    """ Interprets a text config file according to the following rules:

    Define the controllers in the lines following "CONTROLLERS", specifying the type of daqcontroller and the port
    Format for controllers are: daqcontroller,<ID-Name>,<Controller-Type>,<Port>
    ID-name should be string identifier and should start with a alpha-numeric character
    Acceptable daqcontroller-types are: arduino, simulated

    Define the hardware utilities (individual hardware components) in the lines following "UTILITIES"
    Utility definitions follow the format utility,<utility-type>, <daqcontroller-id>, <arg1, arg2, arg3,...>
    Utility-type are:
           pressure            |   provides pressure control for the outlet
           xystage             |   provides XY stage control for a motorized microscope staage
     daqcontroller-id should match an ID specified under CONTROLLERS

    """

    def read_config(self, filepath):
        """
        Read and return the daqcontroller and utility settings from a text file specified by filepath
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
        """Returns a list of daqcontroller settings"""
        controllers = cfg_list[cfg_list.index('CONTROLLERS') + 1:cfg_list.index("UTILITIES")]
        return cls._remove_comments(controllers)

    @classmethod
    def _get_utilities(cls, cfg_list):
        """Returns a list of utility settings"""
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


class SystemAbstraction(ABC):

    def __init__(self):
        self.controllers = {}
        self.utilities = {}

    def load_config(self, config_file="default"):
        """
        Load the controllers and utitily objects, and assign them to the CE System utilities.
        :param config_file:
        :return:
        """
        if config_file.lower() == "default":
            config_file = os.path.abspath(os.path.join(os.getcwd(), 'config\\TestChip.cfg'))

        director = ConcreteDirector()
        director.construct(config_file)
        utilities = director.get_utilities()

        # Update the class utility properties
        for key, value in utilities.items():
            self.__setattr__(key, value)
        print(utilities)
        self.utilities = utilities
        self.controllers = director.get_controllers()

    def open_controllers(self):
        """
        Open the controller resources
        :return:
        """
        for name, controller in self.controllers.items():
            print("OPENING: ", name, controller)
            controller.open()

    def close_controllers(self):
        """
        Close the controller resources
        :return:
        """
        for name, controller in self.controllers.items():
            controller.close()

    def startup_utilities(self):
        """
        Initializes the hardware Utility resources.
        :return:
        """

        for name, utility in self.utilities.items():
            if utility is None:
                logging.info(f"{name} not configured.")
                continue
            print("Starting up: {}, {}".format(name, utility))
            utility.startup()

    def shutdown_utilities(self):
        """
        Puts utility objects in their shutdown state
        :return:
        """
        for _, utility in self.utilities.items():
            try:
                utility.shutdown()
            # We need to make sure all modules shutdown, so if there is an error, keep shutting down what you can.
            except Exception as e:
                logging.warning(e)
                logging.warning(f"{utility} had error on shutdown")



class CESystem(SystemAbstraction):
    """
    CE System object. Contains all the utility functions needed for an automated CE system.
    Each utility will be declared as a property of the class after load_config is called.

    Care should be taken to only call methods from the utility classes that have been defined by the class abstraction.
    This enables the CE System to swap between different vendors for hardware easily.

    """

    def __init__(self):
        super().__init__()
        # Define list of Utilities Needed for this class (this makes it so we can dynamically type with this class)
        self.outlet_pressure = PressureControl.PressureAbstraction
        self.xy_stage = XYControl.XYAbstraction
        self.objective = ZControl.ZAbstraction
        self.outlet_z = ZControl.ZAbstraction
        self.inlet_z = ZControl.ZAbstraction
        self.filter_wheel = FilterWheelControl.FilterWheelAbstraction
        self.shutter = ShutterControl.ShutterAbstraction
        self.camera = CameraControl.CameraAbstraction
        self.high_voltage = HighVoltageControl.HighVoltageAbstraction
        self.detector = DetectorControl.DetectorAbstraction
        self.lysis_laser = LaserControl.LaserAbstraction
        self.inlet_rgb = LightControl.RGBAbstraction

    def stop_ce(self):
        """
        Command to stop a list of Utilities when stopping a run
        :return:
        """
        stop_list = [self.high_voltage, self.xy_stage, self.inlet_z, self.objective, self.outlet_z,
                     self.outlet_pressure, self.lysis_laser]

        for utility in stop_list:
            try:
                utility.stop()
            except Exception as e:
                logging.error(f"ERR: {utility} did not stop. \n {e}")


if __name__ == "__main__":
    os.chdir('..')
    system = CESystem()
    system.load_config()
    system.open_controllers()
