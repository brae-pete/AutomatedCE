# Implement a Factory for the pressure control.
import threading
from abc import ABC, abstractmethod
from queue import LifoQueue, Empty

from L2.Utility import UtilityControl, UtilityFactory
from L1 import DAQControllers
import numpy as np


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

    def __init__(self, controller):
        self.controller = controller
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


class NiSpellmanPowerSupply(HighVoltageAbstraction, UtilityControl):
    """
    National instrument control over a high Spellman 1000CZR Powersupply

    It also incorporates the UtilityControl class for basic utility functions (shutdown, startup, get status, etc...)
    """

    def __init__(self, controller, adc:DAQControllers.NiAnalogIn, dac:DAQControllers.NiAnalogOut, hv_ao='ao0',
                 hv_ai='ai3', ua_ai='ai1'):
        super().__init__(controller)
        self.adc = adc
        self._hv_channel = hv_ao
        self.dac = dac
        self.adc.add_channels([hv_ai, ua_ai])
        self.dac.add_channels([hv_ao])
        self.adc.add_callback_function(self._read_data, [hv_ai, ua_ai], 'RMS')
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
        self.dac.start_voltage()

    def stop(self):
        """Stop the voltage only (let the ADC keep acquiring)"""
        self.dac.stop_voltage()

    def set_voltage(self, voltage = 0 , channel = 'default'):
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
        self.dac.set_channel_voltage(channel, voltage)


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


class SimulatedPressure( UtilityControl):
    """
    Simulated pressure class. Uses the same ArduinoPressure class which should function as a simulated class
    when a SimulatedController object is used.
    """

    def __init__(self, controller):
        super().__init__(controller)
        # some private properties for the simulation
        self._pressure_valve = False
        self._vacuum_valve = False
        self._release_valve = False

    def _default_state(self):
        """ To get to default state, shut all valves then open the release valve"""
        self.seal()
        self.release()

    def startup(self):
        """ Sets valves to default state """
        self._default_state()

    def shutdown(self):
        """ Returns valves to default state """
        self._default_state()

    def get_status(self):
        """ Returns the status of the three solenoid valves"""
        return "Pressure: {}, Vacuum: {}, Release: {}".format(self._pressure_valve,
                                                              self._vacuum_valve,
                                                              self._release_valve)

    def rinse_pressure(self):
        """ Open the rinse pressure solenoid"""
        self._pressure_valve = True

    def rinse_vacuum(self):
        """ Open the vacuum pressure solenoid"""
        self._vacuum_valve = True

    def release(self):
        """ Open the release solenoid"""
        self._release_valve= True

    def seal(self):
        """Close all solenoid valves """
        self._release_valve = False
        self._vacuum_valve = False
        self._pressure_valve = False

class PressureControlFactory(UtilityFactory):
    """ Determines the type of pressure utility object to return according to the controller id"""

    def build_object(self, controller):
        if controller.id == 'arduino':
            return ArduinoPressure(controller)
        elif controller.id == 'simulator':
            return SimulatedPressure(controller)
        else:
            return None


if __name__ == "__main__":
    from L1.Controllers import SimulatedController
    controller = SimulatedController()
    pressure = SimulatedPressure(controller)



