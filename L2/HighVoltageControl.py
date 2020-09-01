# Implement a Factory for the pressure control.
import logging
import struct
import threading
from abc import ABC, abstractmethod
import numpy as np
from L2.Utility import UtilityControl, UtilityFactory
from L1 import DAQControllers, Controllers


class HighVoltageAbstraction(ABC):
    """
    Utility class for controlling high voltage supplies.

    High Voltage control consists of a few main functions:
    set_voltage = Applies a pressure to the channel specified
    stop = Sets all voltages to zero
    start = Applies a voltage according to the corresponding set value
    get_voltage = Returns the voltage reading
    get_current = returns the current reading
    """

    def __init__(self, controller, role):
        self.daqcontroller = self.controller = controller
        self.role = role
        self._set_voltages = {}
        self._voltages = 0
        self._current = 0
        self.data = {'voltage': [], 'current': [], 'time_data': []}
        self._data_lock = threading.Lock()

    @abstractmethod
    def set_voltage(self, voltage, channel):
        """Sets the value to change the voltage to when start is called"""
        pass

    @abstractmethod
    def stop(self):
        """Sets all voltages to zero"""
        pass

    @abstractmethod
    def start(self):
        """Sets all voltages to the value specified by the set command"""
        pass

    @abstractmethod
    def get_voltage(self):
        """ Return in kV the voltage of the channels"""
        pass

    @abstractmethod
    def get_current(self):
        """ Return in uA the current of the channels"""
        pass

    def get_status(self):
        """Returns the set_voltages for each channel"""
        pass

    def get_data(self):
        """
        Returns the data dictionary
        :return:
        """
        with self._data_lock:
            return self.data.copy()


class PMOD_DAC(HighVoltageAbstraction):
    """
    Hardware Class for controlling the Bertran Power Supply via a PMOD DAC using an Arduino. This class keeps the monitor
    channels from the Arduino ADC connected to the DAC channels

    Pin 7 corresponds to the Bertan Enable PIN

    """
    _max_voltage = 5  # The absolute maximum voltage you can request
    _index = 0
    lock = threading.RLock()
    run_data = None

    def __init__(self, controller: (DAQControllers.DaqAbstraction, Controllers.ControllerAbstraction), role,
                 input_channels=(), output_voltage=(), output_current=()):
        """
        This class uses an arduino controller to create a analog output to control the bertan power supply. It uses
        a daqcontroller to read the current and voltage inputs
        Input channels correspond to the channel number on the Bertan starting at 1 and going up to 6.
        Ouput Voltage correspond to the daq input pins connected to the bertan redaout for a channels  voltage
        Output Current Channels correspond to the daq input ins connected to the bertan current readout.

        Config example:
        utility, (daq1&ard1), high_voltage, chip_voltage, bertan, [3,4,5], ['ai3','ai5','NA'], ['ai4','ai6','NA']
        * The Output voltage and current channels must be the same length as the input channels. If there is no
        port available, or the outputs from the power supply don't need to be recorded pass 'NA' instead. In the above
        example channel 5 of the bertan does not have voltage or current readout.

        This is a little trickier than the spellman in that we have two controllers to work with. One to set the analog
        output control voltage and one that reads it in.
        """
        super().__init__(controller, role)
        try:
            self.daqcontroller = controller[0]
            self.controller = controller[1]

        except TypeError:
            self.daqcontroller=controller
            self.controller = controller
        print(input_channels, output_voltage, output_current)
        assert len(output_current) == len(input_channels) == len(output_voltage), "All Bertan config channel lengths" \
                                                                                  "must match"
        # Set up DAC information
        self.voltages = {}
        self._input_channels = []
        self._voltage_scalar = 1
        self._current_scalar = 1
        for in_ch, out_voltage, out_current in zip(input_channels, output_voltage, output_current) :
            self.voltages[in_ch] = [0, 0]
            if out_voltage.upper() != "NA":
                self.daqcontroller.add_analog_input(out_voltage)
            if out_current.upper() != "NA":
                self.daqcontroller.add_analog_input(out_current)

            self._input_channels.append(out_voltage)
            self._input_channels.append(out_current)

        self.daqcontroller.add_callback(self._read_data, self._input_channels, 'wave', ())
    def _reset_data(self):
        v_data = {}
        c_data = {}
        for i in self.voltages.keys():
            v_data[i]=[]
            c_data[i]=[]
        with self.lock:
            self.data['voltage']=v_data
            self.data['current']=c_data


    def get_current(self):
        with self.lock:
            data = self.data['current'].copy()
        return data

    def get_voltage(self):
        with self.lock:
            data = self.data['voltage'].copy()
        return data

    def read_arduino(self):
        with self.lock:
            response = self.controller.read_until('\n'.encode())
        return response.decode()

    def load_changes(self):
        """
        Loads the changes from every channels input register to the DAC
        :return:
        """
        self.controller.send_command("U?00\n")

    def _load_channel_changes(self, chnl):
        """
        Loads changes from specific input channel to the DAC
        :param chnl:
        :return:
        """

        self.controller.send_command("U{}00\n".format(chnl))

    def _power_down(self):
        """
        Disables the Bertan Enable pin. Resets all the DAC.
        :return:
        """
        self.controller.send_command("X000\n")

    def _power_on(self):
        """
        Turns on the Bertan Enable Pin.
        :return:
        """
        self.controller.send_command("E000\n")

    def startup(self):
        """
        Resets the DAQ up the DAQ enable pin
        :return:
        """
        self._power_down()
        self._power_on()

    def start(self):
        with self.lock:
            self._reset_data()
        self.load_changes()
        self.daqcontroller.start_measurement()

    def stop(self):
        """
        Resets the daq and disables the daq enable pin
        :return:
        """
        self.daqcontroller.stop_measurement()
        self._power_down()

    def shutdown(self):
        """
        Rests the dac and powers down the enable pin
        :return:
        """
        self._power_down()

    def set_voltage(self, voltage, channel):  # Channel refers to channel number on Bertan, from 1 to 6
        """
        Sets the voltage of the DAC pin for a corresponding channel
        :param channel: int, 1-6 which Bertan channel you want to set the voltage
        :param voltage: float, between 0 -5,000 volts
        :return:
        """
        self.voltages[channel][1] = voltage
        if -self._max_voltage > voltage > self._max_voltage:
            logging.warning("Absolute voltage value must be less than {}} Volts".format(voltage))
        # PMOD_DAC is between 0 and 2.5 V
        if voltage > self._max_voltage:
            logging.error("ERROR: Voltage set beyond DAC capability")
            voltage = self._max_voltage
        # Convert to 16 bit unisigned int
        vout = int(voltage * 2 ** 12 / self._max_voltage)
        msb, lsb = divmod(vout, 0x100)
        with self.lock:
            self.controller.send_command("S{}".format(channel))
            self.controller.send_command(bytearray([msb, lsb]))
            self.controller.send_command("\n".encode())

    @staticmethod
    def _interpret_bytes(byte_data):
        """
        :param byte_data: From the Arduino, bytes object with a start byte 'S' or 83 that is 16 floats long (16*4).
        :return: numpy array of floats corresponding to the voltage [index 0-7] and current [index 8-15] values for channels 0-8
         of the PMOD DAC
        """
        idx = None
        for i in range(len(byte_data)):
            if byte_data[i] == 83:
                idx = i + 1
                break

        in_data = np.zeros((1, 16))  # Numpy creates array with 1 row and 16 columns of all zeroes
        # If we don't have a start index you will have to return a zeros array
        if idx is None:
            logging.warning("Did Not Find Start Character for Read Data")
            return in_data

        # Move through the bytes array and convert 4 bytes into a float for each of the 16 values in the numpy array
        for i in range(16):
            in_data[0][1] = struct.unpack('f', byte_data[idx + i * 4:idx + (i * 4 + 4)])[0]
        return in_data


    def _read_data(self, samples, time_elapsed, *args):
        """
        This function is called during a continuous acquisition of data from the ADC every time_data enough samples are acquired.
        Samples are two lists of data, the first index being for voltage and the second for voltage
        The samples are added to a thread-safe queue which is checked before returning get_current or get_voltage
        :param samples:
        :param args:
        :return:
        """
        # Empty queue
        scalars = [self._voltage_scalar, self._current_scalar]
        output_channels = list(self.voltages.keys())
        with self._data_lock:
            idx = 0
            outputs = []
            for odd_even, channel in enumerate(self._input_channels):
                # Only add data if we are getting data from our channels, channels that aren't recorded have the NA name
                scalar = scalars[odd_even%2]
                if channel.upper() != "NA":
                    data = np.mean(samples[idx] / scalar)
                    idx += 1
                    #print(len(samples))
                else:
                    data = np.nan
                try:
                    if odd_even%2 > 0:
                        self.data['current'][output_channels[int((odd_even-1)/2)]].append(data)
                    elif odd_even%2 == 0:
                        self.data['voltage'][output_channels[int((odd_even)/2)]].append(data)
                    else:
                        print("??")
                except IndexError:
                    print("Index Error: ",odd_even, len(output_channels))


            self.data['time_data'].append(time_elapsed)



class SpellmanPowerSupply(HighVoltageAbstraction, UtilityControl):
    """
    National instrument control over a high Spellman 1000CZR Powersupply.
    Input Ports should be given in this order:
     Voltage Control - Analog Output,
     Voltage Read - Analog Input*,
     Current Read - Analog Input *

     * Inputs are optional and 'na' can be passed in place of a valid channel name.

     Config example for Digilent DAQ:
     utility, daq1, high_voltage, outlet_voltage, spellman, 0, 0, 'na'

     Config example for NI Daq:
     utility, daq1, high_voltage, outlet_voltage, spellman, 'ao0', 'ai0','ai2'

    It also incorporates the UtilityControl class for basic utility functions (shutdown, startup, get status, etc...)
    """

    def __init__(self, controller: DAQControllers.DaqAbstraction, role, hv_ao='ao0',
                 hv_ai='na', ua_ai='ai1'):
        super().__init__(controller, role)
        self._hv_channel = hv_ao
        self.daqcontroller.add_analog_output(hv_ao)

        inputs = []
        for channel in [hv_ai, ua_ai]:
            if channel.upper() != "NA":
                self.daqcontroller.add_analog_input(channel)
                inputs.append(channel)

        self._input_channels = [hv_ai, ua_ai]
        self.daqcontroller.add_callback(self._read_data, inputs, 'wave', ())
        self._voltage_scalar = 1 / 30 * 10  # kV setting / 30 kV * 5 V
        self._current_scalar = 1 / 3000 * 10  # uA / 100 uA * 5 V

    def startup(self):
        """
        On start up set all the voltage channels to zero
        :return:
        """
        self.stop()

    def shutdown(self):
        """
        On shutdown set all voltage channels to zero
        :return:
        """
        self.stop()

    def start(self):
        """
        Applies the voltages
        :return:
        """
        with self._data_lock:
            self.data = {'voltage': [], 'current': [], 'time_data': []}
        self.daqcontroller.start_voltage()
        self.daqcontroller.start_measurement()

    def stop(self):
        """Stop the voltage only (let the ADC keep acquiring)"""
        self.daqcontroller.stop_voltage()

    def set_voltage(self, voltage=0, channel='default'):
        """
        Changes the voltage settings for the given channel. Set channel to 'default' for a single channel system.
        voltage is the kilovoltage value as a float, channel is the channel identifier as a string
        :param voltage: kilovoltage to set to (float)
        :param channel: str
        :return:
        """
        if channel.lower() == 'default':
            channel = self._hv_channel
        voltage = voltage * self._voltage_scalar
        self.daqcontroller.set_channel_voltage(channel, voltage)

    def get_current(self):
        """
        Return the latest current reading in a thread safe manner
        :return:
        """
        with self._data_lock:
            return self.data['current'][-1]

    def get_voltage(self):
        """
        Return the latest voltage reading in a thread safe manner
        :return:
        """
        with self._data_lock:
            return self.data['voltage'][-1]

    def _read_data(self, samples, time_elapsed, *args):
        """
        This function is called during a continuous acquisition of data from the ADC every time_data enough samples are acquired.
        Samples are two lists of data, the first index being for voltage and the second for voltage
        The samples are added to a thread-safe queue which is checked before returning get_current or get_voltage
        :param samples:
        :param args:
        :return:
        """
        # Empty queue
        with self._data_lock:
            idx = 0
            outputs = []
            for channel, scalar in zip(self._input_channels,
                                       [self._voltage_scalar, self._current_scalar]):
                # Only add data if we are getting data from our channels, channels that aren't recorded have the NA name
                if channel.upper() != "NA":
                    outputs.append(np.mean(samples[idx] / scalar))
                    idx += 1

            self.data['time_data'].append(time_elapsed)
            self.data['current'].append(outputs[1])
            self.data['voltage'].append(outputs[0])


class HighVoltageFactory(UtilityFactory):
    """ Determines the type of pressure utility object to return according to the daqcontroller id"""

    def build_object(self, controller, role, *args):
        """
        Build the high voltage object,
        :param controller:
        :param role:
        :param args: settings list from utility
        :return:
        """
        settings = args[0]
        if settings[4] == 'spellman':
            return SpellmanPowerSupply(controller, role, settings[5], settings[6], settings[7])
        elif settings[4] == 'pmod':
            print(settings[5],settings[6],settings[7])

            return PMOD_DAC(controller, role, settings[5], settings[6], settings[7] )
        else:
            return None



def test_spellman():
    controller = SimulatedDaq()
    power = SpellmanPowerSupply(controller, role='testing', hv_ao='0', hv_ai='0', ua_ai='1')
    power.set_voltage(1000)
    power.start()
    time.sleep(1.5)
    power.get_voltage()

    return power


def test_pmod():

    return

if __name__ == "__main__":
    import time
    from L1.DAQControllers import SimulatedDaq
    from L1.Controllers import SimulatedController

    daqcontroller = SimulatedDaq()
    controller = SimulatedController()
    power = PMOD_DAC((daqcontroller,controller), 'testing', ('0', '1', '2', '3'), ('0', '1', '2', '3'), ('4', '5', '6', '7'))

