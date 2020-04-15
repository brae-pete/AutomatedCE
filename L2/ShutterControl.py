from abc import ABC, abstractmethod
from L2.Utility import UtilityControl, UtilityFactory


class ShutterAbstraction(ABC):
    """
    Utility class for Controlling a Filter wheel.

    Pressure control consists of a few main functions:
    rinse_pressure = Applies a pressure to the outlet
    rinse_vacuum = Applies a vacuum to the outlet
    release = Opens the outlet to atmospheric pressure
    seal = Closes the outlet, sealing it from all pressure sources
    """

    def __init__(self, controller):
        self.controller = controller
        self._state = False

    @abstractmethod
    def open_shutter(self):
        """
        Opens the shutter
        :return:
        """
        pass

    @abstractmethod
    def close_shutter(self):
        """
        Closes the shutter
        """
        pass

    @abstractmethod
    def get_shutter(self):
        """
        Gets the current shutter state, False = closed, True = open
        :return:
        """
        pass

    def get_status(self):
        """Retrieves the last known state of the device """
        return {'filter':self._state}


class MicroManagerShutter(ShutterAbstraction, UtilityControl):
    """ Class to control the filter wheel"""

    def __init__(self, controller):
        super().__init__(controller)
        self._dev_name = "N/A"

    def _get_device(self):
        """Retrive the shutter device name in Micromanager (assumes only one shutter exists) """
        #todo probably need to make this so the user specifiec which device name to use
        """ Finds the correct device name for the microcontroller"""
        if self._dev_name == "N/A":
            self._dev_name = self.controller.send_command('core,get_shutter_name').decode()
            if self._dev_name[0:4]=="ERR:":
                self._dev_name = "N/A"
                raise ValueError('Shutter Device name is not found in micromanager device list')
        return self._dev_name

    def startup(self):
        """
        Do nothing special on start up
        :return:
        """
        pass

    def shutdown(self):
        """Do nothing special on shutdown. """
        pass

    def open_shutter(self):
        """ Opens the shutter"""
        self.controller.send_command('shutter,open,{}\n'.format(self._get_device()))
        self._state=True

    def close_shutter(self):
        """closes the shutter"""
        self.controller.send_command('shutter,close,{}\n'.format(self._get_device()))
        self._state = False

    def get_shutter(self):
        """ Reads the filter wheel channel"""
        self._state = self.controller.send_command('shutter,get,{}\n'.format(self._get_device()))
        return self._state



class ShutterControlFactory(UtilityFactory):
    """ Determines the type of xy utility object to return according to the daqcontroller id"""

    def build_object(self, controller):
        if controller.id == 'micromanager':
            return MicroManagerShutter(controller)
        else:
            return None

if __name__ == "__main__":
    from L1 import Controllers
    ctl = Controllers.MicroManagerController()
    ctl.open()
    sh = ShutterControlFactory().build_object(ctl)
    sh.open_shutter()
    sh.get_shutter()
    sh.close_shutter()
    sh.get_shutter()
    print(sh.get_status())