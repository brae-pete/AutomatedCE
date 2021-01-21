# Implement a Factory for the pressure control.
import time
from abc import ABC, abstractmethod
from L2.Utility import UtilityControl, UtilityFactory


class RGBAbstraction(ABC):
    """
    Turn on RGB light source
    """

    def __init__(self, controller, role, **kwargs):
        self.controller = controller
        self.role = role
        self.state = 'Off'
        self.channels = {'R': 'On', 'G': 'Off', 'B': 'Off'}

    @abstractmethod
    def turn_on_channel(self, channel):
        pass

    @abstractmethod
    def turn_off_channel(self, channel):
        pass


class RGBArduino(RGBAbstraction, UtilityControl):
    """
    RGB ARduino control over the capillary inlet
    """

    def __init__(self, controller, role, **kwargs):
        super().__init__(controller, role, **kwargs)

    def turn_on_channel(self, channel):
        """
        Turns on the specified channels.

        :param channel: 'R', 'G', or 'B'
        :return:
        """

        self.controller.send_command(f'L{channel}1\n')
        self.channels[channel] = 'On'
        self.state = "R:{}, G:{}, B:{}".format(*[x for _, x in self.channels.items()])
        return self.state

    def turn_off_channel(self, channel):
        """
        Turns off the specified channesl

        :param channel:  'R', 'G', or 'B'
        :return:
        """
        self.controller.send_command(f'L{channel}0\n')
        self.channels[channel] = 'Off'
        self.state = "R:{}, G:{}, B:{}".format(*[x for _, x in self.channels.items()])
        return self.state

    def get_status(self):
        """
        Returns the state of each RGB
        :return:
        """
        return self.state

    def shutdown(self):
        """
        Turns off each of the RGB channels
        :return:
        """
        [self.turn_off_channel(x) for x in self.channels.keys()]

    def startup(self):
        """
        No need to do anything
        :return:
        """
        return

    def stop(self):
        """
        No need to do anything
        :return:
        """
        return




class RGBControlFactory(UtilityFactory):
    """ Determines the type of pressure utility object to return according to the daqcontroller id"""

    def build_object(self, controller, role, **kwargs):
        if controller.id == 'arduino':
            return RGBArduino(controller, role, **kwargs)
        else:
            return None
