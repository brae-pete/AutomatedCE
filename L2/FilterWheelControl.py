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
        return {'filter': self._state}

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
            if self._dev_name[0:4] == "ERR:":
                self._dev_name = "N/A"
                raise ValueError('Filter Wheel Device name is not found in micromanager device list')
        return self._dev_name


class PriorFilter(FilterWheelAbstraction, UtilityControl):
    """
    Class to control a filter wheel using Prior Proscan.
    """

    def __init__(self, controller, role, **kwargs):
        super().__init__(controller, role)
        self._position_map = {4: 1, 5: 2, 6: 3, 7: 4, 8: 5, 9: 6, 10: 7, 1: 8,
                              2: 9, 3: 10}  # Camera Port is at key when access is at value

        settings = {'filter': 1}
        settings.update(kwargs)

        self._filter_wheel = settings['filter']  # which filter port on the proscan to use

    def startup(self):
        """ Do  nothing on startup"""
        self.controller.send_command(f"7 {self._filter_wheel},H\r")

    def stop(self):
        """
        Do Nothing on Shutdown
        :return:
        """
        pass

    def set_channel(self, channel, **kwargs):
        """
        Sets the filter wheel to the corresponding channel (starting at 1)


        :param channel: 1 to 10
        :param position: camera or access, determines wheter to move channel to the camera or access pport
        :return:
        """
        settings = {'position': 'camera'}
        settings.update(kwargs)

        channel = int(channel)
        assert 1 <= channel <= 10, "ERR: Filter channel must be between 1 and 10"
        if settings['position'].lower() == 'camera':
            channel = self._position_map[channel]

        self.controller.send_command(f'7 {self._filter_wheel},{channel}\r')

    def get_channel(self, **kwargs):
        """
        Reads the current filter wheel position
        :param kwargs:
        :return:
        """
        pass

    def shutdown(self):
        pass




class PycromanagerFilter(FilterWheelAbstraction, UtilityControl):
    """ Class to control the filter wheel"""

    def __init__(self, controller, role):
        super().__init__(controller, role)
        self._dev_name = "N/A"

    def startup(self):
        """
        Do nothing special on start up
        :return:
        """
        self._dev_name = self.controller.send_command(self.controller.get_device_name, args=('filter',))

    def shutdown(self):
        """Do nothing special on shutdown. """
        pass

    def set_channel(self, channel):
        """ Sets the filter wheel to the corresponding channel (starting at zero) """
        channel = int(channel)
        self.controller.send_command(self.controller.core.set_state, args=(self._dev_name, channel))
        self._state = channel

    def get_channel(self):
        """ Reads the filter wheel channel"""
        self._state = self.controller.send_command(self.controller.core.get_state, args=(self._dev_name,))
        return self._state

    def define_channels(self, **kwargs):
        """
        User defines channels where the key is the label (FITC, GFP, etc...) and the item is the channel integer
        :param kwars: key item pairs for the filter, 'FITC'=1, 'GFP'=0, etc...
        :return:
        """
        self.labels = kwargs


class LumencorFilter(FilterWheelAbstraction, UtilityControl):

    def startup(self):
        """
        Send the power cycle start commands
        :return:
        """
        cmd_1 = bytearray.fromhex("5702FF50")
        cmd_2 = bytearray.fromhex("5703AB50")
        for cmd_i in [cmd_1, cmd_2]:
            self.controller.send_command(cmd_i)

    def get_channel(self):
        pass

    def shutdown(self):
        self.set_channel(['red','green','cyan','uv','teal','blue'],0)

    def set_channel(self, channel):
        """
        Writes to the Lumencor to turn on the specified lights

        Channel Enable Command String:
        Byte 1, Bit 0, controls Red. 0 enables, 1 disables.
        Byte 1, Bit 1, controls Green. 0 enables, 1 disables.
        Byte 1, Bit 2, controls Cyan. 0 enables, 1 disables.
        Byte 1, Bit 3, controls UV. 0 enables, 1 disables.
        Byte 1, Bit 5, controls Blue. 0 enables, 1 disables.
        Byte 1, Bit 6, controls Teal. 0 enables, 1 disables.

        Note- If the Green Channel is enabled, then no other channels can
        be enabled simultaneously. If other channels are enabled, then the
        green channel enable will have priority.
        Examples:
        4F 7E 50- Enables Red, Disables Green,Cyan,Blue,UV,Teal.
        4F 7D 50- Enables Green, Disables Red,Cyan,Blue,UV,Teal.
        4F 7B 50- Enables Cyan, Disables Red,Green,Blue,UV,Teal.
        4F 5F 50- Enables Blue, Disables Red,Green,Cyan,UV,Teal.
        4F 77 50- Enables UV, Disables Red,Green,Cyan,Blue,Teal.
        4F 3F 50- Enables Teal, Disables Red,Green,Cyan,Blue,UV.
        4F 7F 50- Disables All.
        4F 5B 50- Enables Cyan and Blue, Disables all others.
        4F 3E 50- Enables Red and Teal, Disables all others.

        :param channel:
        :return:
        """
        if type(channel) is int:
            channel = [channel]
        label_to_channel = {'red': 0, 'green': 1, 'cyan': 2, 'uv': 3, 'blue': 5, 'teal': 6}

        byte_channel = ['1'] * 7
        byte_channel[7-4]='1'
        #print(byte_channel)
        for chn in channel:
            lbl = 6-label_to_channel[chn]
            byte_channel[lbl] = '0'
            #print(f'chn {chn}, lbl {lbl}, byte_channel={byte_channel}')

        byte_channel = int("".join(byte_channel), 2)
        cmd = bytearray.fromhex('4f')
        cmd.append(byte_channel)
        cmd = cmd + bytearray.fromhex('50')
        #print(cmd)
        self.controller.send_command(cmd)

    def set_intensity(self, channel, level):
        """
        Set the Intensity level fo rthe channel at th especified level.
        Red, Green, Cyan, and UV use IIC addr 18
        Blue and Teal use IIC addr 1A

        IIC DAC Intensity Control Command Strings:
        Byte 5 is the DAC IIC Address. Red, Green, Cyan and UV use
        IIC Addr = 18. Blue and Teal use IIC Addr = 1A.
        Byte 3, Bit 3, selects RED DAC if IIC Addr =18. 1 selects.
        Byte 3, Bit 2, selects GREEN DAC if IIC Addr =18. 1 selects.
        Byte 3, Bit 1, selects CYAN DAC if IIC Addr =18. 1 selects.
        Byte 3, Bit 0, selects UV DAC if IIC Addr =18. 1 selects.
        Byte 3, Bit 1, selects TEAL DAC if IIC Addr =1A. 1 selects.
        Byte 3, Bit 0, selects BLUE DAC if IIC Addr =1A. 1 selects.
        Byte 2, Bits 3..0, Contain the high nibble of 8-bit DAC data.
        Byte 1, Bits 7..4, Contain the low nibble of 8-bit DAC data.
        Note- this 8-bit data is inverted. 0xFF is full off,
        0X00 is full on.
        Examples:
        53 18 03 0F FF F0 50- Sets R,G,C,U DACS to 0xFF (Full off)
        53 18 03 0F F0 00 50- Sets R,G,C,U DACS to 0x00 (Full on)
        53 18 03 01 FA A0 50- Sets UV DAC to 0xAA
        53 18 03 02 F5 50 50- Sets CYAN DAC to 0x55
        53 18 03 04 F8 00 50- Sets GREEN DAC to 0x80
        53 18 03 08 F6 60 50- Sets RED DAC to 0x66
        53 1A 03 01 F4 40 50- Sets BLUE DAC to 0x44
        53 18 03 05 F2 20 50- Sets UV and GREEN DACS to 0x22
        53 1A 03 02 F6 60 50- Sets TEAL DACS to 0x66

        :param channel:
        :param level:
        :return:
        """
        assert level <= 1, "Level must be a vlaue between 0 and 1"
        level = 255 - int(level * 255)
        level_lsb, level_msb = get_level_bytes(level)

        label_to_channel_a = {'red': 3, 'green': 2, 'cyan': 1, 'uv': 0}
        label_to_channel_b = {'teal': 1, 'blue': 0}

        byte_3_a = ['0'] * 8
        byte_3_b = ['0'] * 8
        byte_5_a = None
        byte_5_b = None
        cmd_prefix = bytearray.fromhex('53')

        if type(channel) is list:
            for chn in channel:
                #  get DAC A channels
                if chn in list(label_to_channel_a.keys()):
                    byte_5_a = bytearray.fromhex('18')
                    byte_3_a[7-label_to_channel_a[chn]] = '1'
                # get DAC B Channels
                elif chn in list(label_to_channel_b.keys()):
                    byte_5_b = bytearray.fromhex('1A')
                    byte_3_b[7-label_to_channel_b[chn]] = '1'

        if byte_5_a is not None:
            byte_3 = bytes([int("".join(byte_3_a), 2)])
            #print(f"byte3: {byte_3}, byte_3_a: {byte_3_a}")
            cmd = cmd_prefix + byte_5_a + bytes.fromhex('03') + byte_3 + level_msb + level_lsb + bytes.fromhex('50')
            self.controller.send_command(cmd)
            #print(cmd)

        if byte_5_b is not None:
            byte_3 = bytes([int("".join(byte_3_b), 2)])
            cmd = cmd_prefix + byte_5_b + bytes.fromhex('03') + byte_3 + level_msb + level_lsb + bytes.fromhex('50')
            self.controller.send_command(cmd)
            #print(cmd)


def get_level_bytes(value):
    """
    returns a 8 bit number split according to lumencors
    weird way of loading a 8 bit dac.
    :param value:
    :return:
    """
    bit_0 = bytes([value & int('00001111', 2) << 4])
    bit_1 = bytes([int('11110000',2)|(value >> 4)])
    return bit_0, bit_1


class FilterWheelFactory(UtilityFactory):
    """ Determines the type of xy utility object to return according to the daqcontroller id"""

    def build_object(self, controller, role, *args):
        if controller.id == 'micromanager':
            return MicroManagerFilterWheel(controller, role)
        elif controller.id == 'pycromanager':
            return PycromanagerFilter(controller, role)
        elif controller.id == 'prior':
            return PriorFilter(controller,role)
        elif controller.id == 'lumencor':
            return LumencorFilter(controller,role)
        else:
            return None


if __name__ == "__main__":
    from L1 import Controllers

    ctl = Controllers.LumencorController(port="COM7")
    ctl.open()
    fw = LumencorFilter(ctl, 'lol')

