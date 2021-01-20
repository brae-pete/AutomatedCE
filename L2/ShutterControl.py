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

    def __init__(self, controller, role):
        self.controller = controller
        self.role = role
        self._state = False
        self.auto_capable = False

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
        return {'filter': self._state}

    def stop(self):
        """
        Stop does nothing.
        :return:
        """
        pass

    def set_auto_on(self):
        """
        Sets the auto shutter setting if possible
        :return:
        """
        pass

    def set_auto_off(self):
        """
        Sets the auto shutter off if possible
        :return:
        """
        pass



class MicroManagerShutter(ShutterAbstraction, UtilityControl):
    """ Class to control the filter wheel"""

    def __init__(self, controller, role):
        super().__init__(controller, role)
        self._dev_name = "N/A"

    def _get_device(self):
        """Retrive the shutter device name in Micromanager (assumes only one shutter exists) """
        # todo probably need to make this so the user specifiec which device name to use
        """ Finds the correct device name for the microcontroller"""
        if self._dev_name == "N/A":
            self._dev_name = self.controller.send_command('core,get_shutter_name').decode()
            if self._dev_name[0:4] == "ERR:":
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
        self._state = True

    def close_shutter(self):
        """closes the shutter"""
        self.controller.send_command('shutter,close,{}\n'.format(self._get_device()))
        self._state = False

    def get_shutter(self):
        """ Reads the filter wheel channel"""
        self._state = self.controller.send_command('shutter,get,{}\n'.format(self._get_device()))
        return self._state


class PycromanagerShutter(ShutterAbstraction, UtilityControl):
    """ Class to control the filter wheel"""

    def __init__(self, controller, role):
        super().__init__(controller, role)
        self._dev_name = "N/A"

    def startup(self):
        """
        Do nothing special on start up
        :return:
        """
        self._dev_name = self.controller.send_command(self.controller.get_device_name, args=('shutter',))

    def shutdown(self):
        """Do nothing special on shutdown. """
        pass

    def open_shutter(self):
        """ Opens the shutter"""
        self.controller.send_command(self.controller.core.set_shutter_open, args=(self._dev_name, True))
        self._state = True

    def close_shutter(self):
        """closes the shutter"""
        self.controller.send_command(self.controller.core.set_shutter_open, args=(self._dev_name, False))
        self._state = False

    def get_shutter(self):
        """ Reads the shutter state"""
        self._state = self.controller.send_command(self.controller.core.get_shutter_open, args=(self._dev_name,))
        return self._state

    def set_auto_on(self):
        """
        Sets the shutter to automaticlly open when an image is snapped (micromanager feature)
        :return:
        """
        self.controller.send_command(self.controller.core.set_auto_shutter, args=(True,))

    def set_auto_off(self):
        """
        Sets the shutter to automaticlly open when an image is snapped (micromanager feature)
        :return:
        """
        self.controller.send_command(self.controller.core.set_auto_shutter, args=(False,))


class ShutterFactory(UtilityFactory):
    """ Determines the type of xy utility object to return according to the daqcontroller id"""

    def build_object(self, controller, role, *args):
        if controller.id == 'micromanager':
            return MicroManagerShutter(controller, role)
        elif controller.id == 'pycromanager':
            return PycromanagerShutter(controller, role)
        else:
            return None


if __name__ == "__main__":
    from L1 import Controllers

    ctl = Controllers.MicroManagerController()
    ctl.open()
    sh = ShutterFactory().build_object(ctl)
    sh.open_shutter()
    sh.get_shutter()
    sh.close_shutter()
    sh.get_shutter()
    print(sh.get_status())
