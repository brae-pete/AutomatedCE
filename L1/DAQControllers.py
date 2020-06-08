"""
Code responsible for Analog to digital and digital to analog conversions using daq cards or devices like
national instruments or digilent branded instruments.

"""
import logging
import threading
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from queue import Queue
import numpy as np

from ctypes import *
import sys

# Allow the user to only install the libraries they need. If the libraries aren't available, we won't load the classes
DIGILENT_LOAD = True
NIDAQMX_LOAD = True

try:
    from L1 import dwfconstants

    if sys.platform.startswith("win"):
        dwf = cdll.dwf
    elif sys.platform.startswith("darwin"):
        dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
    else:
        dwf = cdll.LoadLibrary("libdwf.so")
except OSError:
    logging.info("Digilent dll Libraries are not downloaded, Digilent devices will not run")
    DIGILENT_LOAD = False

try:
    import nidaqmx
    from nidaqmx.constants import TerminalConfiguration
except ModuleNotFoundError:
    logging.info("nidaqmx python module is not downloaded, Nidaqmx devices will not run")
    NIDAQMX_LOAD = False

class DaqAbstraction(ABC):

    def __init__(self, **kwargs):
        self._send_funcs = []
        self._lock = threading.Lock()
        self._callbacks = []
        self._set_ai_channels = []
        self._set_ao_channels = []
        self._rate = 1000
        self._total_samples = 0 # used to keep track of time_data
        self._set_voltages = {}
        self._current_voltages = {}
        self._lock = threading.Lock()
        self._read_thread = threading.Thread()
        self.id = 'daq'


        pass

    def open(self):
        """
        By default the DAQ's don't need to be opened or closed
        :return:
        """
        pass

    def close(self):
        """
        By default DAQ's don't need to be opened or closed
        :return:
        """
        pass

    @abstractmethod
    def add_analog_input(self, channels, *args):
        """
        Configures the analog input channel
        :param channels: list
        :param kwargs: dict
        :return:
        """
        pass

    @abstractmethod
    def add_analog_output(self, channel):
        """
        Configures an analog output channel
        :param channel:
        :return:
        """

    @abstractmethod
    def set_sampling_frequency(self, rate):
        """
        Sets the sampling rate (in Hz) for the analog input channels

        :param rate: float
        :return:
        """
        pass

    def get_sampling_frequency(self):
        """
        Returns the current sampling frequency target
        :return:
        """
        return self._rate

    @abstractmethod
    def start_measurement(self):
        """
        Starts reading data from the ADC
        :return:
        """
        pass

    @abstractmethod
    def stop_measurement(self):
        """
        Stop reading data from the ADC
        :return:
        """
        pass

    def add_callback(self, func, chnls, mode='RMS', *args):
        """
        Adds a call back function that will be called when the data is collected
        :param func: function object
        :param chnls: list of analog input channels
        :param mode: str  [ "RMS" or "Wave" to get the RMS average or the waveform ]
        :param args: any arguments that should be passed
        :return:
        """
        self._callbacks.append([func, chnls, mode, *args])

    def _send_data(self, data, total_samples):
        """
        Copies and sends data to the corresponding callback functions.
        Outputs the data array, the time_data it took to acquire this array, and channels gathered
        :param data: array of samples, either ndarray where each col is a channel, or list where each
        index is a sample
        :param total_samples:
        :return:
        """

        # Get the total time_data elapsed since the start_measurment was last called
        time_elapsed = total_samples/self._rate
        for callback_info in self._callbacks:
            [func, channels, mode, args] = callback_info
            out_data = []

            # This should be re-written to use numpy arrays only
            if type(data)== np.ndarray:
                data = list(data.transpose())

            if len(self._set_ai_channels)==1:
                data = [data, data]

            if mode.upper() == 'RMS':
                for chan in channels:
                    idx = self._set_ai_channels.index(chan)
                    out_data.append(np.mean(data[idx]))
            else:
                for chan in channels:
                    idx = self._set_ai_channels.index(chan)
                    out_data.append(np.asarray(data[idx]))
            threading.Thread(target=func, args=(data, time_elapsed, channels, args)).start()

    @abstractmethod
    def set_channel_voltage(self, channel: str, voltage: float):
        pass

    @abstractmethod
    def start_voltage(self):
        pass

    @abstractmethod
    def stop_voltage(self):
        pass

    def add_do_channel(self, channel):
        pass

    def set_do_channel(self, channel, value):
        pass

    def update_do_channels(self):
        pass


if NIDAQMX_LOAD: # Only create the class if the python module is downloaded
    class NiDaq(DaqAbstraction):
        """
        National instrument (NI) control of a digital to analog converter using nidaqmx.
        NI daqmx uses tasks, which hold channels that can be configured according to
        the experiment needs.
        """

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            # Init settings
            settings = {'Device':'Dev1'}
            if kwargs is not None:
                settings.update(kwargs)

            self._task = nidaqmx.Task()
            self._ao_task = nidaqmx.Task()
            self._total_samples = 0
            self._device = settings['Device']
            self._samples = 0
            self._do_task = nidaqmx.Task()
            self._set_do_values = OrderedDict()
            self._set_ao_voltages=[]

        def add_analog_output(self, channel):
            """
            Add channels to the list

            Channels is the identifier string corresponding to the channel on the national instruments analog output
            Examples may be 'ao0, or ao1'.

            :param channel: str
            :param kwargs: dict
            :return:
            """
            if channel in self._set_ao_channels:
                logging.warning("Channel already added")
                return
            with self._lock:
                self._set_ao_channels.append(channel)
                self._set_ao_voltages.append(0)
                self._ao_task.ao_channels.add_ao_voltage_chan('/' + self._device + '/' + channel)

        def add_analog_input(self, channel: str, volt_range=5, **kwargs):
            """
            Add channel to the list

            Channels is the identifier string corresponding to the channel on the national instruments analog output
            Examples may be 'ao0, or ao1'.

            :param channels: str
            :param kwargs: dict
            :return:
            """
            settings = {'terminal_config':'RSE'}
            if kwargs is not None:
                settings.update(kwargs)
            if channel in self._set_ai_channels:
                logging.warning("Channel already added")
                return
            with self._lock:
                self._set_ai_channels.append(channel)
                terminal_config = self._get_terminal_config(settings['terminal_config'])
                self._task.ai_channels.add_ai_voltage_chan('/' + self._device + '/' + channel,
                                                           terminal_config=terminal_config,
                                                           min_val=-volt_range, max_val=volt_range)

        def set_channel_voltage(self, channel: str, voltage: float):
            """
            Sets the voltage for a given channel
            :param voltage: float within -5 to 5 V or whatever the range for the nidaqmx device you are using is
            :param channel: analog output channel string ao0 or ao1 are common.
            :return:
            """
            assert channel in self._set_ao_channels
            # Set the DC amplitude
            idx = self._set_ao_channels.index(channel)
            self._set_ao_voltages[idx] = voltage

        def start_voltage(self):
            """
            When ready to apply to voltages, create a list (in the same order that channels were added to the task)
            of voltages ranging from current voltage to the set voltage. The ordered list used for channels should
            ensure that voltage output list matches the order channels were added to the task.

            :return:
            """
            write_channels = []
            with self._lock:
                self._ao_task.write(self._set_ao_voltages)

        def _get_terminal_config(self, terminal_config: str):
            """
            Returns the appropriate Terminal configuration constant for the analog input terminals.
            :param terminal_config:
            :return:
            """
            if terminal_config.upper() == "RSE":
                return TerminalConfiguration.RSE
            elif terminal_config.upper() == "DIFF":
                return TerminalConfiguration.DIFFERENTIAL
            elif terminal_config.upper() == 'PSUEDO':
                return TerminalConfiguration.PSEUDODIFFERENTIAL
            else:
                return TerminalConfiguration.DEFAULT

        def set_sampling_frequency(self, rate):
            """
            Sets the sampling frequency in Hz
            :param rate:
            :return:
            """
            with self._lock:
                self._rate = rate

        def _configure_timing(self, mode: str):
            """
            Configures the timing for the analog input task.
            National instruments requires that the samples be a multiple of 10 of the sampling rate.

            :return:
            """

            self._samples = int(self._rate / 10)
            if mode.lower() == 'finite':
                mode = nidaqmx.constants.AcquisitionType.FINITE
            else:
                # For continuous function we use a callback function
                mode = nidaqmx.constants.AcquisitionType.CONTINUOUS
                self._task.register_every_n_samples_acquired_into_buffer_event(self._samples, None)
                self._func = self._task.register_every_n_samples_acquired_into_buffer_event(self._samples, self._read_data)
            self._task.timing.cfg_samp_clk_timing(self._rate, samps_per_chan=self._samples, sample_mode=mode)

            return

        def start_measurement(self, mode='continuous'):
            """
            When ready to read the measurement, start the task.
            :return:
            """
            with self._lock:

                self._configure_timing(mode=mode)
                self._total_samples = 0
                self._task.start()

        def stop_measurement(self):
            """
            Call to stop a measurement
            :return:
            """
            self._task.stop()

        def _read_data(self, *args):
            """
            Read data from the device and start sending it to the callbacks
            :param args:
            :return:
            """

            try:
                samples = np.asarray(self._task.read(number_of_samples_per_channel=self._samples))
            except nidaqmx.errors.DaqError:
                logging.error('Nidaq did not read samples correctly')
                return 1
            with self._lock:
                self._total_samples += len(samples)
                self._send_data(samples, self._total_samples)
                return 0

        def stop_voltage(self):
            """ Sets the Voltage to Zero"""
            output = [0] * len(self.channels)
            self._ao_task.write(output)

        def add_do_channel(self, channel):
            """
            Add a digital output channel. Channel should be a string identifier for the digital output.
            For NI that inlcudes both the port and line numbers:

            port0/line5 is an appropriate channel id
            p0.5 is also an appropriate channel id for the same channel

            :param channel: string identifier for channel
            :return:
            """

            if channel in self._set_do_values.keys():
                logging.warning("Channel already added")
                return
            try:
                self._do_task.do_channels.add_do_chan('/' + self._device + '/' + channel)
            except:
                channel = self.interpret_do_channels(channel)
                self._do_task.do_channels.add_do_chan('/' + self._device + '/' + channel)
            self._set_do_values[channel]=False


        def set_do_channel(self, channel, value):
            """
            Change the desired value for digital output channel. This will not update the actual value until the update/write
            command is sent.
            :param channel:
            :param value:
            :return:
            """
            self._set_do_values[channel] = value

        def update_do_channels(self):
            """
            Updates the digital output channels with the desired set values
            :return:
            """
            self._do_task.write(list(self._set_do_values.values()), auto_start=True)


        @staticmethod
        def interpret_do_channels(channel):
            """
            Converts digital channel names from abbreviated form to
            long form that is required by nidaqmx software
            :param channel: abbreviated channel name (P0.0)
            :return:  long form channel name (port0\line0)
            """
            parts = channel.split('.')
            port = parts[0].upper().strip('P')
            line = parts[1]
            assert port.isnumeric() and line.isnumeric(), f"Digital channel names are incorrect form {channel}"
            return f"port{port}/line{line}"


if DIGILENT_LOAD: # Only create the class if the cdll module is downloaded
    class DigilentDaq(DaqAbstraction):
        """
        Analog input for a Digilent Analog Discovery II
        """

        def __init__(self, **kwargs):
            super().__init__()
            self._set_ao_channels = []
            self.set_ai_channels = []

            self._callbacks = []
            self._samples = 8192
            self._read_flag = threading.Event()
            self._dio_mask = ['0']*16 # Bit mask for digital inputs outputs enable
            self._set_do_channels = ['0']*16 # Bit mask for do channel values
            if DIGILENT_LOAD:
                load = self._init_device()
            else:
                logging.warning("Digilent DAQ cannot be loaded. Waveform SDK needs to be installed")
                return
            if not load:
                raise ValueError('Digilent Device Failed to Open')

            self.set_sampling_frequency(self._rate)

        def _init_device(self):
            """
            Load the Digilent Device if possible
            :return:
            """

            self.hdwf = c_int()
            self._sts = c_byte()
            self.hzAcq = c_double(200)
            self.nSamples = 1000
            self._rgdSamples = (c_double * self.nSamples)()
            self._cValid = c_int(0)

            version = create_string_buffer(16)
            dwf.FDwfGetVersion(version)
            dwf.FDwfDeviceOpen(c_int(-1), byref(self.hdwf))
            if self.hdwf.value == 0:
                szerr = create_string_buffer(512)
                dwf.FDwfGetLastErrorMsg(szerr)
                print(str(szerr.value))
                print("failed to open device")
                return None
            return True

        def add_analog_output(self, channel: int):
            """ Adds a analog output channel """
            channel = int(channel)
            assert channel in [0, 1]  # channel must be one of these two values, add to list of enabled channels
            self._set_ao_channels.append(channel)
            # Enable the channel
            dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(channel), dwfconstants.AnalogOutNodeCarrier, c_int(True))
            # Set the channel to output DC (hwdf, channel, node, function)
            dwf.FDwfAnalogOutNodeFunctionSet(self.hdwf, c_int(channel), c_int(0), c_int(0))  # sine

        def add_analog_input(self, channel: int, range=5):
            """
            Adds an analog input channel that should be read while reading the data
            :param channel:
            :param range:
            :return:
            """
            channel = int(channel)
            assert channel in [0, 1]
            self.set_ai_channels.append(channel)
            dwf.FDwfAnalogInChannelEnableSet(self.hdwf, c_int(channel), c_bool(True))
            # Set the range (you could increase this if needed, [hdwf, channel, range])
            dwf.FDwfAnalogInChannelRangeSet(self.hdwf, c_int(channel), c_double(range))
            # Discovery 2 samples at 100 Mhz, how will you downsample the data? (Decimate or Average)
            dwf.FDwfAnalogInChannelFilterSet(self.hdwf, c_int(-1), dwfconstants.filterAverage)

        def set_channel_voltage(self, voltage, channel):
            """
            Sets the voltage for a given channel
            :param voltage: float [-5 to 5 V]
            :param channel: int [0, 1]
            :return:
            """
            channel = int(channel)
            assert channel in self._set_ao_channels
            # Set the DC amplitude
            dwf.FDwfAnalogOutNodeOffsetSet(self.hdwf, c_int(channel), c_int(0), c_double(voltage))

        def set_sampling_frequency(self, frequency):
            """
            Sets the analog input sampling frequency (100 Mhz is max)
            :param frequency:
            :return:
            """
            dwf.FDwfAnalogInFrequencySet(self.hdwf, c_double(frequency))
            self._rate = frequency

        def start_voltage(self):
            """
            Sets the voltage to the correct value
            :return:
            """
            # Determine if the output channel is already running
            status = c_int()
            dwf.FDwfAnalogOutStatus(self.hdwf, c_int(0), byref(status))
            if status.value == 3:
                status = 3
            else:
                status = 1
            # Send command to start the channel output
            dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(0), c_int(status))

        def stop_voltage(self):
            """
            Stops the analog ouput
            :return:
            """
            dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(0), c_bool(False))

        def start_measurement(self):
            """
            Start the ADC and begin reading data from the Analog Discovery 2
            :return:
            """
            dwf.FDwfAnalogInAcquisitionModeSet(self.hdwf, c_int(1))  # acqmodeScanShift

            # Determine if the input channel is already running
            status = c_int()
            dwf.FDwfAnalogOutStatus(self.hdwf, c_int(0), byref(status))
            if status.value == 3:
                status = 3
            else:
                status = 1
            dwf.FDwfAnalogInConfigure(self.hdwf, c_int(1), c_int(status))
            # Reset the flag if needed and start a new thread
            if self._read_flag.is_set():
                self._read_flag.clear()
            if not self._read_thread.is_alive():
                self._read_thread = threading.Thread(target=self._read_data)
                self._read_thread.start()

        def stop_measurement(self):
            """
            Stop the thread that is reading information from the ADC
            :return:
            """
            self._read_flag.set()

        def _read_data(self):
            """
            I am worried we won't be able to add data fast enough by threading alone if the sampling rate is too high.
            To prevent that the sampling rate needs to be low enough so that no other blocking thread will prevent
            the data from being processed. Reading in the data once every second may be a save place to start.

            One interesting aspect to the Discovery 2 is that it downsamples the data for us. The ADC always aquires at
            100 Mhz but you have the option to decimate or average the data. Because we are averaging the data, we are
            likely getting a lot of the benefits of oversampling filtering.

            To get around that we could possibly pass the byteref for the hdwf to a new python process and read
            the data from there.
            :return:
            """
            # Create a buffer for each channel
            data_buffer = {}
            for chan in self.set_ai_channels:
                data_buffer[chan] = (c_double * self._samples)()

            # Declare the c_type variables in advance
            sts = c_byte()
            hzAcq = c_double(200)
            cValid = c_int(self._samples)
            buf_index = c_int(0)
            total_samples = 0

            # The read loop
            while not self._read_flag.is_set():
                old_index = buf_index.value
                dwf.FDwfAnalogInStatus(self.hdwf, c_int(1), byref(sts))
                dwf.FDwfAnalogInStatusIndexWrite(self.hdwf, byref(buf_index))  # get channel 1 data

                # If new index is lower than the last index, we need to record the data (#not perfect but good enough)
                if buf_index.value < old_index:
                    for chan, buffer in data_buffer.items():
                        dwf.FDwfAnalogInStatusData(self.hdwf, c_int(chan), byref(buffer), cValid)  # get channel 1 data
                    # Record the sample number the data was collected at
                    self._send_data(data_buffer, total_samples)
                    total_samples += self._samples + buf_index.value

        def add_do_channel(self, channel):
            """
            Add a digital output channel. Channel should be a string identifier for the digital output.
            For Digilent that should be an int indicating which pin it refers to.

            :param channel:
            :return:
            """
            channel = int(channel)
            assert type(channel) == int, "Channel must be an Integer"
            # Adjust the maskk and enable the pin
            self._dio_mask[channel]='1'
            mask = "".join(self._dio_mask)
            dwf.FDwfDigitalIOOutputEnableSet(self.hdwf, c_int(int(mask, base=2)))

        def set_do_channel(self, channel, value):
            """
            Change the desired value for digital output channel. This will not update the actual value until the update/write
            command is sent.
            :param channel:
            :param value:
            :return:
            """
            channel = int(channel)
            assert type(channel) == int, 'Channel must be an integer'

            if value:
                value = '1'
            else:
                value = '0'

            self._set_do_channels[channel]=value

        def update_do_channels(self):
            """
            Updates the digital output channels with the desired set values
            :return:
            """
            mask = "".join(self._set_do_channels)
            dwf.FDwfDigitalIOOutputSet(self.hdwf, c_int(int(mask, base=2)))

if __name__ == "__main__":
    import matplotlib.pyplot as plt


    def show_me_stuff(data, samples, channels, *args):
        print(samples)


    dq = DigilentDaq()
    dq.add_analog_output(0)
    dq.set_channel_voltage(1, 0)
    dq.start_voltage()
    dq.add_analog_input(0, 5)
    dq.set_sampling_frequency(100000)
    dq.add_callback(show_me_stuff, [0], 'RMS', ())
    dq.start_measurement()
