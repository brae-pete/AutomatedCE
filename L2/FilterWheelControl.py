from abc import ABC, abstractmethod
from L2.Utility import UtilityControl, UtilityFactory


class FilterWheelAbstraction(ABC):
    """
    Utility class for Controlling a Filter wheel.

    Pressure control consists of a few main functions:
    rinse_pressure = Applies a pressure to the outlet
    rinse_vacuum = Applies a vacuum to the outlet
    release = Opens the outlet to atmospheric pressure
    seal = Closes the outlet, sealing it from all pressure sources
    """

    def __init__(self, controller, role):
        self.controller = controller
        self.role = role
        self._state = 0

    @abstractmethod
    def set_channel(self, channel):
        """
        Move the filter wheel to the selected channel
        :param channel: int (integer represented desired channel)
        :return:
        """
        pass

    @abstractmethod
    def get_channel(self):
        """
        Get the corresponding filter wheel channel
        :return: int (integer representing desired channel)
        """
        pass

    def get_status(self):
        """Retrieves the last known state of the device """
        return {'filter':self._state}

    def stop(self):
        """
        Stop does nothing
        :return:
        """
        pass


class MicroManagerFilterWheel(FilterWheelAbstraction, UtilityControl):
    """ Class to control the filter wheel"""

    def __init__(self, controller, role):
        super().__init__(controller, role)
        self._dev_name = "N/A"

    def startup(self):
        """
        Do nothing special on start up
        :return:
        """
        pass

    def shutdown(self):
        """Do nothing special on shutdown. """
        pass

    def set_channel(self, channel):
        """ Sets the filter wheel to the corresponding channel (starting at zero) """
        self.controller.send_command('filter,set,{},{}\n'.format(self._get_device(), channel))
        self._state = channel

    def get_channel(self):
        """ Reads the filter wheel channel"""
        self._state = self.controller.send_command('filter,get,{}\n'.format(self._get_device()))
        return self._state

    def _get_device(self):
        """ Finds the correct device name for the microcontroller"""
        if self._dev_name == "N/A":
            self._dev_name = self.controller.send_command('core,get_filterwheel_name').decode()
            if self._dev_name[0:4]=="ERR:":
                self._dev_name = "N/A"
                raise ValueError('Filter Wheel Device name is not found in micromanager device list')
        return self._dev_name


class FilterWheelFactory(UtilityFactory):
    """ Determines the type of xy utility object to return according to the daqcontroller id"""

    def build_object(self, controller, role, *args):
        if controller.id == 'micromanager':
            return MicroManagerFilterWheel(controller, role)
        else:
            return None

if __name__ == "__main__":
    from L1 import Controllers
    ctl = Controllers.MicroManagerController()
    ctl.open()
    fw = FilterWheelFactory().build_object(ctl)
    fw.set_channel(2)
    fw.get_channel()
    print(fw.get_status())

