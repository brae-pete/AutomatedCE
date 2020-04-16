from abc import ABC, abstractmethod
from L2.Utility import UtilityControl, UtilityFactory
from L1.DAQControllers import DaqAbstraction

class LaserAbstraction(ABC):

    def __init__(self, controller):
        self.daqcontroller = controller
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


class Uniphase(LaserAbstraction, UtilityControl):

    def __init__(self, controller:DaqAbstraction, computer='port0/line0', laser_on='port0/line1', pulse='port0/line5'):
        super().__init__(controller)


        # Initialize the daq controller settings
        self.daqcontroller.add_do_channel(computer)
        self.daqcontroller.add_do_channel(laser_on)
        self.daqcontroller.add_do_channel(pulse)
        self._channels = {'computer': computer, 'laser_on': laser_on, 'pulse': pulse}
        self.daqcontroller.set_do_channel(self._channels['laser_on'], True)


    def _set_channels(self, values):
        for value, channel in zip(values, self._channels.keys()):
            self.daqcontroller.set_do_channel(channel, value)

    def laser_fire(self):
        """
        This is a thread blocking task. Requires the laser to be in standby mode before firing. We set the pulse to
        50 ms.
        :return:
        """
        if self.enable:
            self._set_channels([True,True,True])
            self.daqcontroller.update_do_channels()
            time.sleep(0.05)
            self._set_channels([False,True,False])
            self.daqcontroller.update_do_channels()

    def startup(self):
        """ Opens the laser and makes sure it is set to off"""
        self.enable = False
        self._set_channels([False, True, False])
        self.daqcontroller.update_do_channels()

    def shutdown(self):
        """ Close the resources """
        self.enable = False
        self._set_channels([False, True, False])
        self.daqcontroller.update_do_channels()

    def get_status(self):
        """
        Returns whether or not the laser is enabled to fire
        :return:
        """
        return {'laser':self.enable}