# Implement a Factory for the pressure control.
import threading
from abc import ABC, abstractmethod
from L2.Utility import UtilityControl, UtilityFactory
from L1 import DAQControllers


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
        self.daqcontroller = controller
        self.role = role
        self._set_voltages = {}
        self._voltages = {}
        self._current = {}


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

    def __init__(self, controller:DAQControllers.DaqAbstraction, role, hv_ao='ao0',
                 hv_ai='na', ua_ai='ai1'):
        super().__init__(controller, role)
        self._hv_channel = hv_ao
        self.daqcontroller.add_analog_output(hv_ao)

        inputs = []
        for channel in [hv_ai, ua_ai]:
            if channel.upper() != "NA":
                self.daqcontroller.add_analog_input(channel)
                inputs.append(channel)

        self.daqcontroller.add_callback(self._read_data, inputs, 'RMS', ())
        self._data_lock = threading.Lock()
        self._voltage_scalar = 1 / 30 * 5 # kV setting / 30 kV * 5 V
        self._current_scalar = 1 / 100 * 5 # uA / 100 uA * 5 V

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
        self.daqcontroller.start_voltage()
        self.daqcontroller.start_measurement()

    def stop(self):
        """Stop the voltage only (let the ADC keep acquiring)"""
        self.daqcontroller.stop_voltage()

    def set_voltage(self, voltage = 0, channel='default'):
        """
        Changes the voltage settings for the given channel. Set channel to 'default' for a single channel system.
        voltage is the kilovoltage value as a float, channel is the channel identifier as a string
        :param voltage: float
        :param channel: str
        :return:
        """
        if channel.lower() == 'default':
            channel = self._hv_channel
        voltage = voltage * self._voltage_scalar
        self.daqcontroller.set_channel_voltage( voltage, channel)

    def get_current(self):
        """
        Return the latest current reading in a thread safe manner
        :return:
        """
        with self._data_lock:
            return self._current

    def get_voltage(self):
        """
        Return the latest voltage reading in a thread safe manner
        :return:
        """
        with self._data_lock:
            return self._voltages

    def _read_data(self, samples, *args):
        """
        This function is called during a continuous acquisition of data from the ADC every time enough samples are acquired.
        Samples are two lists of data, the first index being for voltage and the second for voltage
        The samples are added to a thread-safe queue which is checked before returning get_current or get_voltage
        :param samples:
        :param args:
        :return:
        """
        # Empty queue
        with self._data_lock:
            self._current = samples[1]/ self._current_scalar
            self._voltages = samples[0]/self._voltage_scalar


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
        if controller.id == 'daq':
            settings = args[0]
            if settings[4]=='spellman':
                return SpellmanPowerSupply(controller, role, settings[5], settings[6], settings[7])
            else:
                return None
        else:
            return None


if __name__ == "__main__":
    import time
    from L1.DAQControllers import DigilentDaq
    controller = DigilentDaq()
    power = SpellmanPowerSupply(controller, hv_ao=0, hv_ai=0, ua_ai=1 )
    power.set_voltage(1000)
    power.start()
    time.sleep(1.5)
    power.get_voltage()




