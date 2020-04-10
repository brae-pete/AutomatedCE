import logging
from abc import ABC, abstractmethod

from L1 import Controllers
from L2.Utility import UtilityControl, UtilityFactory


def check_z(func):
    """ Decorator function to deterimine if the set value for the stage is within bounds"""

    def wrapper(self, z):
        if self.min_z < z < self.max_z:
            func(self, z)
        else:
            logging.warning("z-set is not within bounds for z-stage {}".format(self.role))
        return wrapper


def check_rel_z(func):
    """Decorator function to determine if rel_z is within bounds"""
    def wrapper(self, rel_z):
        z = self.read_z() + rel_z
        if self.min_z < z < self.max_z:
            func(self, rel_z)
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

    def __init__(self, controller : Controllers.ControllerAbstraction, role : str):
        self.controller = controller
        self.role = role
        self._scale = 1
        self._z_inversion = 1
        self._offset = 0
        self.pos = 0
        self._default_pos = 24.5
        self.min_z = 0
        self.max_z = 25

    def _scale_values(self, z : float):
        return z/self._scale *self._z_inversion + self._offset

    def _invert_scale(self, z : float):
        return (z-self._offset)*self._scale * self._z_inversion

    def get_status(self):
        """Returns the position of the Z stage"""
        return {'z':self.pos}

    @abstractmethod
    def set_z(self, z : float):
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
        pass


class ArduinoZ(ZAbstraction, UtilityControl):

    """ Utility class for moving a single axis motor with the PowerStep01 stepper driver and an Arduino.

    """
    def __init__(self, controller, role):
        super().__init__(controller, role)
        self._stepper_direction= 1 # 0 For positive/forward motion is towards home

    def startup(self):
        """ on startup we need to go to the home position (raise all the way up)"""
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
        self.pos = z
        return z

    def set_home(self):
        """Adjusts where the default home position is"""
        self._offset = -self.read_z()
        self.min_z += self._offset
        self.max_z += self._offset

    def go_home(self):
        self.set_z(0)

    def homing(self):
        """
        Sends the microcontroller to the limit switch. Sends the stepper to twice the normally allowed distance so
        that it will hit the limit switch which will stop the motor.

        _stepper_direction refers to if the stepper needs to move forwards or reverse. If stepper moves in opposite
        direction of the limit switch try changing this value.

        :return:
        """
        self.controller.send_command("M0G{}{}\n".format(self._stepper_direction, self._stepper_direction))
        self.max_z*=2
        self.set_z(self.max_z)
        self.wait_for_move()
        self.set_rel_z(0.1)
        self.wait_for_move()
        self.max_z = self.max_z/2


class PriorZ(ZAbstraction, UtilityControl):

    def __init__(self, controller, role):
        super().__init__(controller, role)
        self.min_z = 0
        self.max_z = 10


    def startup(self):
        """ Do nothing special on start up"""
        pass

    def shutdown(self):
        """ Do nothing special on shutdown """
        pass

    def read_z(self):
        """ Read the current position"""
        self.pos = self.controller.send_command("PZ \r")
        return self.pos

    @check_z
    def set_z(self, z):
        """ Set the absolute position """
        z = self._invert_scale(z)
        self.controller.send_command("GZ {} \r".format(z))

    def stop(self):
        """ Stop the motor from moving"""
        self.controller.send_command("D 0 \r")

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

