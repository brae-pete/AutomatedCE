import threading
import time
from abc import ABC, abstractmethod
from L2.Utility import UtilityControl, UtilityFactory
from L1.DAQControllers import DaqAbstraction


class LaserAbstraction(ABC):

    def __init__(self, controller, role):
        self.daqcontroller = controller
        self.role = role
        self.enable = False

    def set_parameters(self, *args):
        """ Set laser parameters """
        pass

    def laser_standby(self):
        """ Laser is ready to fire in this mode"""
        self.enable = True

    def laser_stop(self):
        """ Stop firing the laser, remove laser from standby"""
        self.enable = False

    def laser_fire(self):
        """ Fire the laser """
        if self.enable:
            return True
        return False

    def close(self):
        """ Close the laser hardware resources"""
        self.enable = False
        return True

    def laser_check(self):
        """ Returns the status of the laser"""
        return self.enable

    def _set_channels(self, values):
        for value, channel in zip(values, self._channels.keys()):
            channel = self._channels[channel]
            self.daqcontroller.set_do_channel(channel, value)


class Uniphase(LaserAbstraction, UtilityControl):
    """
    Utility class for control over a Uniphase laser using the digital outputs from a DAQ controller.

    User must supply the digial output channels that connect to the computer, laser on/off, and pulse lines of the
    Uniphase 9 pin D-sub.

    Config example National Instrument daq:
    utility,daq1,laser,lysis_laser,uniphase,port0/line0,port0/line1,port0/line5
    """

    def __init__(self, controller: DaqAbstraction, role, computer='port0/line0', laser_on='port0/line1',
                 pulse='port0/line5'):
        super().__init__(controller, role)

        # Initialize the daq controller settings
        self.daqcontroller.add_do_channel(computer)
        self.daqcontroller.add_do_channel(laser_on)
        self.daqcontroller.add_do_channel(pulse)
        self._channels = {'computer': computer, 'laser_on': laser_on, 'pulse': pulse}
        self.daqcontroller.set_do_channel(self._channels['laser_on'], True)

    def laser_fire(self):
        """
        This is a thread blocking task. Requires the laser to be in standby mode before firing. We set the pulse to
        50 ms.
        :return:
        """
        if self.enable:
            self._set_channels([True, True, True])
            self.daqcontroller.update_do_channels()
            time.sleep(0.05)
            self._set_channels([True, True, False])
            self.daqcontroller.update_do_channels()

    def laser_standby(self):
        """ Laser is ready to fire in this mode"""
        self.enable = True
        self._set_channels([True, True, False])

    def startup(self):
        """ Opens the laser and makes sure it is set to off"""
        self.enable = False
        self._set_channels([False, False, False])
        self.daqcontroller.update_do_channels()

    def shutdown(self):
        """ Close the resources """
        self.enable = False
        self._set_channels([False, False, False])
        self.daqcontroller.update_do_channels()

    def get_status(self):
        """
        Returns whether or not the laser is enabled to fire
        :return:
        """
        return {'laser': self.enable}

    def stop(self):
        """
        Stop diables the enable flag
        :return:
        """
        self.enable = False


class NewWaveBNC(LaserAbstraction, UtilityControl):
    """
    Utility class for control over a NewWave laser using the digital outputs from a DAQ controller.

    User must supply the digial output channels that connect to the lamp fire BNC port

    Config example National Instrument daq:
    utility,daq1,laser,lysis_laser,newwave,port0/line0
    """

    def __init__(self, controller, role, lamp_switch=None):
        super().__init__(controller, role)

        self._channels = {'lamp_switch': lamp_switch}
        self.daqcontroller.add_do_channel(lamp_switch)

    def laser_fire(self):
        """
        This is a thread blocking task. Requires the laser to be in standby mode before firing. We set the pulse to
        50 ms.
        :return:
        """
        if self.enable:
            self._set_channels([True])
            self.daqcontroller.update_do_channels()
            time.sleep(0.001)
            self._set_channels([False])
            self.daqcontroller.update_do_channels()

    def startup(self):
        """ Opens the laser and makes sure it is set to off"""
        self.enable = False
        self._set_channels([False])
        self.daqcontroller.update_do_channels()

    def shutdown(self):
        """ Close the resources """
        self.enable = False
        self._set_channels([False])
        self.daqcontroller.update_do_channels()

    def get_status(self):
        """
        Returns whether or not the laser is enabled to fire
        :return:
        """
        return {'laser': self.enable}

    def stop(self):
        """
        Stop diables the enable flag
        :return:
        """
        self.enable = False


class LaserFactory(UtilityFactory):
    """ Determines the type of detector utility object to return according to the controller id"""

    def build_object(self, controller, role, *args):
        """
        Build the high voltage object,
        :param controller:
        :param role:
        :param args: settings list from utility
        :return:
        """
        print(controller.id)
        if controller.id == 'daq':
            settings = args[0]
            print(settings[4])
            if settings[4] == 'uniphase':
                return Uniphase(controller, role, settings[5], settings[6], settings[7])
            elif settings[4] == 'newwave':
                return NewWaveBNC(controller, role, settings[5])
            else:
                return None
        else:
            return None
