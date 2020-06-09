import logging
import sys
import threading
import time
from abc import ABC, abstractmethod
import numpy as np

from L1 import Controllers
from L2.Utility import UtilityControl, UtilityFactory


def check_z(func):
    """ Decorator function to determine if the set value for the stage is within bounds
    This is decorator is used for every set_z function
    """

    def wrapper(self, z):
        if self.min_z < z < self.max_z:
            return func(self, z)
        else:
            logging.warning("z-set is not within bounds for z-stage {}".format(self.role))

    return wrapper


def check_rel_z(func):
    """Decorator function to determine if rel_z is within bounds"""

    def wrapper(self, rel_z):
        z = self.read_z() + rel_z
        if self.min_z < z < self.max_z:
            return func(self, rel_z)
        else:
            logging.warning("z-set is not within bounds for z-stage".format(self.role))

    return wrapper


class ZAbstraction(ABC):
    """
    Utility class for a Z-stage object.

    Specialized functions include:
    set_z: sets absolute position of the stage
    set_rel_z: jogs the stage up or down
    read_z: reads the current position from the stage
    set_home: sets the current position as 0 or home for the stage
    go_home: sends the stage to home or 0 position
    homing: moves the motor till it locates an endstop or limitswitch
    stop: stops the stage movement
    wait_for_move: waits for the stage to stop moving
    """

    def __init__(self, controller: Controllers.ControllerAbstraction, role: str):
        self.controller = controller
        self.role = role
        self._scale = 1
        self.z_inversion = 1
        self._offset = 0
        self.pos = 0
        self._default_pos = 24.5
        self.min_z = 0
        self.max_z = 25

    def _scale_values(self, z: float):
        "Called on values read from microcontroller"
        return (z / self._scale * self.z_inversion) + self._offset

    def _invert_scale(self, z: float):
        "Called on values to be sent to the microcontroller"
        return (z - self._offset) * self._scale * self.z_inversion

    def get_status(self):
        """Returns the position of the Z stage"""
        return {'z': self.pos}

    @abstractmethod
    def set_z(self, z: float):
        pass

    def set_rel_z(self, rel_z: float):
        pos = self.read_z()
        self.set_z(pos + rel_z)

    @abstractmethod
    def read_z(self):
        pass

    @abstractmethod
    def set_home(self):
        pass

    @abstractmethod
    def go_home(self):
        pass

    @abstractmethod
    def homing(self):
        pass

    def wait_for_move(self):
        pos = self.read_z()
        new_pos = pos + 1
        while np.abs(pos - new_pos) > 0.1:
            pos = new_pos
            new_pos = self.read_z()

    @abstractmethod
    def stop(self):
        """
        Stop the object movement.
        :return:
        """
        self.set_rel_z(0)


class ArduinoZ(ZAbstraction, UtilityControl):
    """ Utility class for moving a single axis motor with the PowerStep01 stepper driver and an Arduino.

    """
    velocity_max = 20  # mm/s
    acceleration = 5
    jerk = 0  # If constant acceleration, set jerk equal to 0

    def __init__(self, controller, role, **kwargs):
        super().__init__(controller, role)
        self._scale = 1
        self._offset = 30
        self.pos = 0
        self._default_pos = 24.5
        self.min_z = 0
        self.max_z = 30
        settings = {'direction': 1}
        if kwargs is not None:
            settings.update(kwargs)
        self.z_inversion = settings['direction']  # 0 For positive/forward motion is towards home

    def startup(self):
        """ on startup we need to go to the home position (raise all the way up)"""

        resp = self.controller.send_command("TESTING12345\n")
        self.homing()

    def shutdown(self):
        """ On shutdown don't do anything special"""
        pass

    @check_z
    def set_z(self, z):
        """ Sets the absolute z position"""
        z = self._invert_scale(z)
        self.controller.send_command("M0L{:+.3f}\n".format(z))

    def read_z(self):
        """ Reads the z position"""
        z = self.controller.send_command("M0L?\n")
        while "L?" != z[0:2]:
            z = self.controller.read_buffer()
        z = self._scale_values(float(z.strip('L?').strip('\n').strip('\r')))
        self.pos = z
        return z

    def set_home(self):
        """Adjusts where the default home position is"""
        self._offset = -self.read_z()
        self.min_z += self._offset
        self.max_z += self._offset

    def go_home(self):
        self.set_z(0)

    def stop(self):
        self.set_rel_z(0)

    def homing(self):
        """
        Sends the microcontroller to the limit switch. Sends the stepper to twice the normally allowed distance so
        that it will hit the limit switch which will stop the motor.

        _stepper_direction refers to if the stepper needs to move forwards or reverse. If stepper moves in opposite
        direction of the limit switch try changing this value.

        :return:
        """
        # self.controller.send_command("M0G{}{}\n".format(1, 1))

        # self.wait_for_move()
        self.max_z = 60
        self.set_z(59.75)
        self.max_z = 30


class SimulatedZ(ZAbstraction, UtilityControl):
    velocity_max = 20  # mm/s
    acceleration = 5
    jerk = 0  # If constant acceleration, set jerk equal to 0

    def __init__(self, controller, role):
        super().__init__(controller, role)

    def startup(self):
        self.set_z(0)

    def shutdown(self):
        self.set_z(0)

    def set_home(self):
        self.pos = 0

    def homing(self):
        self.set_home()

    def set_z(self, z: float):
        self.pos = z

    def read_z(self):
        return self.pos

    def go_home(self):
        self.set_z(0)

    def stop(self):
        pass


class PriorZ(ZAbstraction, UtilityControl):
    velocity_max = 20  # mm/s
    acceleration = 5
    jerk = 0  # If constant acceleration, set jerk equal to 0

    def __init__(self, controller, role):
        super().__init__(controller, role)
        self.min_z = 0
        self.max_z = 10
        self._scale = 10

    def startup(self):
        """ Do nothing special on start up"""
        pass

    def shutdown(self):
        """ Do nothing special on shutdown """
        pass

    def read_z(self):
        """ Read the current position"""
        self.pos = float(self.controller.send_command("PZ \r"))
        self.pos = self._scale_values(self.pos)
        return self.pos

    @check_z
    def set_z(self, z):
        """ Set the absolute position """
        z = self._invert_scale(z)
        self.controller.send_command("GZ {} \r".format(z))

    def stop(self):
        """ Stop the motor from moving"""
        self.controller.send_command("I \r")

    def go_home(self):
        """ Go to the 0 position"""
        self.controller.send_command('GZ 0\r')

    def set_home(self):
        """ Set the home position"""
        logging.warning("Set home not implemented")

    def homing(self):
        """ Go to the hardware homing point"""
        logging.warning("Homing not implemented")


class MicroManagerZ(ZAbstraction, UtilityControl):
    """ This admittedly is only for the objective, or Z-focus. It has not been tested with other Z-stages on
    micromanager.

    """
    velocity_max = 20  # mm/s
    acceleration = 5
    jerk = 0  # If constant acceleration, set jerk equal to 0

    def __init__(self, controller, role):
        super().__init__(controller, role)
        self.min_z = 0
        self.max_z = 10

    def startup(self):
        """ Do nothing special on start up"""
        self.set_z(0)

    def shutdown(self):
        """ Do nothing special on shutdown """
        pass

    def read_z(self):
        """ Read the current position"""
        self.pos = self.controller.send_command("obj,get_position\n")
        return self.pos

    @check_z
    def set_z(self, z):
        """ Set the absolute position """
        z = self._invert_scale(z)
        self.controller.send_command("obj,set_position,{} \n".format(z))

    def go_home(self):
        """ Go to the 0 position"""
        self.set_z(0)

    def set_home(self):
        """ Set the home position"""
        logging.warning("Set home not implemented")

    def homing(self):
        """ Go to the hardware homing point"""
        logging.warning("Homing not implemented")

    def stop(self):
        """
        Stop the hardware
        :return:
        """
        self.set_rel_z(0)


class KinesisZ(ZAbstraction, UtilityControl):
    """
    Kinesis Controller

    Contains all the libraries used to control Thorlabs labjack using Kinesis.
    For simulations, you can create a hardware componenet using the Kinesis Simulator application and
    use the corresponding SerialNumber for your simulated hardware id.
    """

    # Modules needed for Kinesis
    from L4.FileIO import get_system_var
    kinesis_path = get_system_var('kinesis')[0]
    sys.path.append(kinesis_path)

    import clr as clr

    # If you cannot load these modules, make sure that the system_var.txt has the correct path for the kinesis software
    # "C:\\Program Files\\Thorlabs\\Kinesis" is an example path to check. Install Kinesis if not aleady done.

    from System import String
    from System import Decimal
    from System import Collections

    clr.AddReference("Thorlabs.MotionControl.Controls")
    clr.AddReference("Thorlabs.MotionControl.DeviceManagerCLI")
    clr.AddReference("Thorlabs.MotionControl.GenericMotorCLI")
    clr.AddReference("Thorlabs.MotionControl.IntegratedStepperMotorsCLI")

    from Thorlabs.MotionControl import DeviceManagerCLI
    from Thorlabs.MotionControl import GenericMotorCLI
    from Thorlabs.MotionControl import IntegratedStepperMotorsCLI

    def __init__(self, controller: Controllers.ControllerAbstraction, role: str):
        super().__init__(controller, role)
        self._ser_no = controller
        self._lock = threading.Lock()

    def set_serial(self, ser_no):
        """Set the serial number for the device"""
        self._ser_no = ser_no

    def _open(self):
        """ Opens the device resources"""
        self.DeviceManagerCLI.DeviceManagerCLI.BuildDeviceList()
        self.device = self.IntegratedStepperMotorsCLI.LabJack.CreateLabJack(self._ser_no)
        self.device.Connect(self._ser_no)
        self.device.LoadMotorConfiguration(self._ser_no)
        self.device.WaitForSettingsInitialized(5000)
        _ = self.device.MotorDeviceSettings
        self.device.EnableDevice()
        self.device.StartPolling(250)

    def _set_velocity(self, velocity: float):
        """ Sets the velocity of the labjack motor"""
        v = velocity
        v = self.Decimal(velocity)
        vel_prms = self.device.GetVelocityParams()
        vel_prms.set_MaxVelocity(v)
        self.device.SetVelocityParams(vel_prms)

    def startup(self):
        """
        Open the hardware on startup
        :return:
        """
        self._open()
        self._set_velocity(3.5)

    def shutdown(self):
        """
        Close the hardware on shutdown
        :return:
        """
        self._close()

    def _close(self):
        self.device.Disconnect()

    def read_z(self):
        """ Read the Z information from the labjack"""
        with self._lock:
            self.pos = self._scale_values(float(str(self.device.DevicePosition)))
        return self.pos

    @check_z
    def set_z(self, z):
        """
        Sets the absolute position of the labjack, but will include a backlash calculation/motion. Do not use this
        if the capillary will be within 1mm a hard surface (glass slide, stage, etc...) as it will likely overshoot
        and break the capillary
        :param z:
        :return:
        """
        z = self.Decimal(self._invert_scale(z))
        self.stop()
        # Create a thread that will send the MoveTo command
        if self._home_check():
            threading.Thread(target=self.device.MoveTo, args=((z), 60000)).start()

    def stop(self):
        """ If stage is moving stop it """
        status = self.device.get_Status()

        self.device.Stop(0)

    def _get_travel_direction(self, rel_z):
        dist_up = self.z_inversion * rel_z
        if dist_up < 0:
            direction = self.GenericMotorCLI.MotorDirection.Backward
        else:
            direction = self.GenericMotorCLI.MotorDirection.Forward
        return direction

    def set_rel_z(self, rel_z):
        """
        Sets a relative amount to move, this uses a jog function and does not deal with backlash like set _z. Use this
        for when the capillary is near a hard surface.
        :param rel_z: float
        :return:
        """
        # Kinesis Jog command requires distance to travel and the direction
        direction = self._get_travel_direction(rel_z)
        distance = self.Decimal(float(np.abs(rel_z)))
        self.stop()
        jog_prms = self.device.GetJogParams()
        if distance != jog_prms.get_StepSize():
            jog_prms.set_StepSize(distance)
            self.device.SetJogParams(jog_prms)
        if self._home_check():
            threading.Thread(target=self.device.MoveJog, args=(direction, 60000,)).start()

    def _home_check(self):
        if self.device.NeedsHoming:
            logging.warning("Please Home Kinesis Labjack")
            return False
        return True

    def set_home(self):
        """
        Sets the home position
        :return:
        """
        logging.warning("Set home no implemented")

    def go_home(self):
        """ Moves down until the stage hits the mechanical stop that specifices the 0 mm mark
         """
        self.set_z(0)

    def homing(self):
        """
        Sends the microcontroller to the limit switch. Sends the stepper to twice the normally allowed distance so
        that it will hit the limit switch which will stop the motor.

        _stepper_direction refers to if the stepper needs to move forwards or reverse. If stepper moves in opposite
        direction of the limit switch try changing this value.

        :return:
        """
        threading.Thread(target=self.device.Home, args=(60000,)).start()


class ZControlFactory(UtilityFactory):
    """ Determines the type of xy utility object to return according to the daqcontroller id"""

    def build_object(self, controller, role):

        if controller.id == 'micromanager':
            return MicroManagerZ(controller, role)
        elif controller.id == 'prior':
            return PriorZ(controller, role)
        elif controller.id == 'arduino':
            return ArduinoZ(controller, role)
        elif controller.id == 'kinesis':
            return KinesisZ(controller, role)
        elif controller.id == 'simulator':
            return SimulatedZ(controller, role)
        else:
            return None


if __name__ == "__main__":
    from L1 import Controllers

    ctl = Controllers.MicroManagerController()
    ctl.open()
    Z = ZControlFactory().build_object(ctl, 'test')
    Z.set_z(20)
