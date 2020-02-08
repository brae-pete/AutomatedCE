from nidaqmx.constants import Edge
import nidaqmx
from nidaqmx.constants import TerminalConfiguration
import numpy as np
import logging
import time
import threading
from scipy import signal
import shutil
import os
import serial
import matplotlib.pyplot as plt

DEV = "/Dev1/"
CURRENT_OUT = "ai5"
VOLTAGE_IN = "ai1"
VOLTAGE_OUT = 'ao1'
RFU = "ai3"


class NIDAQ_USB:
    model = 'USB-6211'
    max_freq = 250000  # Sampling frequency
    bit_depth = 16
    devices = ['Dev1']
    analog_inputs = ['ai0', 'ai1', 'ai2', 'ai3', 'ai4', 'ai5', 'ai6', 'ai7', 'ai8', 'ai10',
                     'ai11', 'ai12', 'ai13', 'ai14', 'ai15']
    analog_outputs = ['ao0', 'ao1']
    digital_IO_ports = ['port0', 'port1']
    digital_lines = ['line0:3']
    counter_channel = ['ctr0', 'ctr1', 'freqout']
    counter_mode = ['Pulse Train Generation', 'Edge Counting']
    pulse_terminal = ['PFI4']
    ni_tasks = {'ADC': nidaqmx.Task(), 'DAC': nidaqmx.Task()}

class DAC:

    def __init__(self, channels=None):
        if channels is None:
            channels = [1, 2, 3]
        self.voltages={}
        for i in channels:
            self.voltages[i]=[0,0]

    def set_voltage(self, chnl, voltage):
        self.voltages[chnl][1]=voltage

    def get_voltage_setting(self, chnl):
        return self.voltages[chnl][1]

    def load_changes(self):
        """
        Implement the changes in the DAC
        :return:
        """
        for key in self.voltages:
            self.voltages[key][0]=self.voltages[key][1]


class NI_DAC(DAC, NIDAQ_USB):
    """
    Basic digital to analog converter. The user passes in the channels that need to be created.

    >>> dac = NI_DAC(channels=['ao0'])
    >>> dac.set_voltage(12,'ao0')
    >>> dac.load_changes()

    """

    def __init__(self, channels=None, dev=0):
        # Create the task
        if channels is None:
            channels = ['ao0', 'ao1']
        self.task = nidaqmx.Task()
        self.ni_tasks['adc'] = self.task
        # Create a data variable
        self.data = np.zeros([len(channels), 0])
        self.voltages = {}
        # Add the channels
        for chan in channels:
            self.task.ao_channels.add_ao_voltage_chan('/' + self.devices[dev] + '/' + chan)
            self.voltages[chan] = [0, 0]  # current, set kV
        # Configure the Timing
        self.task.start()
        self.load_changes()

        # Voltage ramp (NI only)
        self._voltage_ramp = 10  # kV/s

    def set_voltage(self, chnl, voltage):
        """Change the set voltage on the channel. Need to run load changes to see an effect """
        self.voltages[chnl][1] = voltage
        return True

    def load_changes(self):
        """
        Load the changes into the DAC.
        :return:
        """
        write_list = []
        for chan in self.voltages:
            current_v, set_v = self.voltages[chan]
            write_list.append([set_v])
            self.voltages[chan] = [set_v, set_v]
        if len(write_list) == 1:
            write_list = write_list[0]
        self.task.write(write_list)

class ADC:

    def __init__(self, channels=['ai1', 'ai2', 'ai3'], mode = 'finite', sampling =50000, samples =5000, dev =0, lock=threading.RLock()):
        self.channels=channels
        self.mode = mode
        self.sampling=sampling
        self.samples=samples
        self.output_data_count = 1  # for oversampling, output the r
        self.downsampled_freq = self.sampling/self.samples*self.output_data_count
        self.dev=dev
        self.data_lock = lock

        # Create a data variable
        self.data = np.zeros([len(channels), 0])

    def start(self):
        """
        Start acquiring data. For the sample class we call read once, but read may
        be an event or timer that repeatedly adds to the data.
        :return:
        """
        self.read()

    def read(self):
        """
        Generate some sample data. The read function should append to the
        Data field along the columns (axis=1).
        """
        with self.data_lock:
            self.data = np.append(self.data, np.random.rand(len(self.channels),100), axis=1)

    def stop(self):
        """
        Stop acquiring data.
        For our sample class this is not needed.
        :return:
        """
        return

    def reset_data(self):
        with self.data_lock:
            self.data = np.zeros([len(self.channels), 0])
class NI_ADC(ADC, NIDAQ_USB):
    """
    Basic Analog to Digital Converter. The user can specify the mode (continuous, finite).
    When Basic_ADC is initialized the user passes in the analog input channels they
    want to measure.

    Be sure that both the nidaqmx python library and the NIDaqMX Base is installed. NiDaqMX base (version 15.1 or higher)
    must be installed from national instruments website, it does not automatically install when the
    USB-6211 or other daq card is plugged in.

    >>>adc = Basic_ADC(channels = ['ai1', 'ai2'], mode = 'finite')
    >>>adc.start()
    >>> data = adc.read()
    """
    modes = {'continuous': nidaqmx.constants.AcquisitionType.CONTINUOUS,
             'finite': nidaqmx.constants.AcquisitionType.FINITE}

    configuration = {'diff':TerminalConfiguration.DIFFERENTIAL,
                     'RSE':TerminalConfiguration.RSE,
                     'NRSE':TerminalConfiguration.NRSE}

    def __init__(self, channels=['ai1', 'ai2', 'ai3'],configs={}, mode='finite', sampling=100000, samples=10000, dev=0,
                 output_data=1):

        # Create the task
        super().__init__(channels, mode, sampling, samples, dev)
        self.task = nidaqmx.Task()
        self.ni_tasks['adc'] = self.task
        self.output_data_count=output_data

        # Add the channels
        for chan in channels:
            if chan in configs.keys():
                config = self.configuration[configs[chan]]
            else:
                config = TerminalConfiguration.RSE

            self.task.ai_channels.add_ai_voltage_chan('/' + self.devices[dev] + '/' + chan,
                                                      terminal_config=config)

        # Configure the Timing
        self.mode = self.modes[mode]
        self.task.timing.cfg_samp_clk_timing(sampling, samps_per_chan=samples, sample_mode=self.mode)
        self.downsampled_freq = self.sampling/self.samples*self.output_data_count

    def start(self):
        if self.mode == self.modes['continuous']:
            self.task.register_every_n_samples_acquired_into_buffer_event(self.samples, self.read)
        self.task.start()

    def read(self, *args):
        """ Read the data from the analog input channels and append it to the data array"""
        try:
            samples = np.asarray(self.task.read(number_of_samples_per_channel=self.samples))
            self._samples = samples
        except nidaqmx.errors.DaqError:
            return 1

        with self.data_lock:
            interval = np.floor(samples.shape[1] / self.output_data_count)
            for i in range(self.output_data_count):
                avg_samples = np.mean(samples[:, int(interval * i):int(interval * (i + 1))], axis=1).reshape(
                    self.data.shape[0], 1)
                self._avg_samples = avg_samples
                self.data = np.append(self.data, avg_samples, axis=1)

        return 0

    def stop(self):
        """
        Stop reading from the daq
        :return:
        """
        self.task.stop()

class PMOD_DAC(DAC):
    """
    Hardware Class for controlling the Bertran Power Supply via a PMOD DAC using an Arduino. This class keeps the monitor
    channels from the Arduino ADC connected to the DAC channels

    Pin 7 corresponds to the Bertan Enable PIN

    """
    _max_voltage = 2.5  # The absolute maximum voltage you can request
    _index = 0
    lock = threading.Lock()
    run_data=None

    def __init__(self, channels=None, port="COM3"):  # Brae, what is COM4????
        """
        This class communicates with the Arduino via Serial communication. We use the pyserial library for all of the
        serial communication functions.
        :param port: string. Which communication port on the PC corresponds to the Arduino. You can determine this using
        the Arduino software or by inspecting the PORTS tree under device manager.
        """
        #Set up Serial Communication Port
        if channels is None:
            channels = [1, 2, 3]
        self.ser = serial.Serial()  # Serial communication object thats responible for communicating with the arduino
        self.ser.port = port
        self.ser.baudrate = 1000000
        self.ser.open()
        self.ser.timout = 1

        #Set up DAC information
        self.voltages = {}
        for i in channels:
            self.voltages[i] = [0, 0]

    def read_arduino(self):
        with self.lock:
            response = self.ser.read_until('\n'.encode())
        return response.decode()

    def load_changes(self):
        """
        Loads the changes from every channels input register to the DAC
        :return:
        """
        with self.lock:
            self.ser.write("U?00\n".encode())

    def _load_channel_changes(self, chnl):
        """
        Loads changes from specific input channel to the DAC
        :param chnl:
        :return:
        """
        with self.lock:
            self.ser.write("U{}00\n".format(chnl).encode())

    def _power_down(self):
        """
        Disables the Bertan Enable pin. Resets all the DAC.
        :return:
        """
        with self.lock:
            self.ser.write("X000\n".encode())

    def _power_on(self):
        """
        Turns on the Bertan Enable Pin.
        :return:
        """
        with self.lock:
            self.ser.write("E000\n".encode())

    def set_voltage(self, channel, voltage):  # Channel refers to channel number on Bertan, from 1 to 6
        """
        Sets the voltage of the DAC pin for a corresponding channel
        :param channel: int, 1-6 which Bertan channel you want to set the voltage
        :param voltage: float, between 0 -5,000 volts
        :return:
        """
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
            self.ser.write("S{}".format(channel).encode())
            self.ser.write(bytearray([msb, lsb]))
            self.ser.write("\n".encode())

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


class Data:
    """ Data class to retrieve the correct data values"""

    def __init__(self, adc_in=None):
        if adc_in is None:
            adc_in =ADC()
        self.adc_in=adc_in

    def get_last_value(self, chnl):
        return self.adc_in.data[-1, chnl]

    def get_column(self, chnl):
        return self.adc_in.data[:, chnl]


class Filter:
    """ Filter class for the finished chromatogram"""

    def __init__(self):
        #Butter Filter
        self.cutoff=2
        self.sampling=10
        self.order = 5
        self.padlen=24
        self.padtype='constant'
        self.mode="Butter"

    def filter_data(self, data):
        if self.mode =='Butter':
            return self.butter(data)
        elif self.mode == 'Savgol':
            return self.savgol(data)

    def _butter_lowpass(self):
        nyq = 0.5*self.sampling
        normal_cutoff = self.cutoff/nyq
        b,a = signal.butter(self.order, normal_cutoff, btype='low', analog=False)
        return b,a

    def butter(self, data):
        b,a = self._butter_lowpass()
        return signal.filtfilt(b,a, data, padlen=self.padlen, padtype=self.padtype)


class DAQBoard:
    freq = 50000  # Sampling frequency for analog inputs


if __name__ == "__main__":
    adc = NI_ADC(channels = ['ai0', 'ai14', 'ai15'],configs={'ai0':'diff'}, mode='continuous', sampling = 80000, samples=10000)
    adc.start()
