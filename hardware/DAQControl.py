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

    def __inti__(self, channels):
        self.voltages={}
        for i in channels:
            self.voltages[i]=[0,0]

    def set_voltage(self, chnl, voltage):
        self.voltages[chnl][1]=voltage

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
        self.data = np.append(self.data, np.random.rand(len(self.channels),100), axis=1)

    def stop(self):
        """
        Stop acquiring data.
        For our sample class this is not needed.
        :return:
        """
        return

class NI_ADC(ADC, NIDAQ_USB):
    """
    Basic Analog to Digital Converter. The user can specify the mode (continuous, finite).
    When Basic_ADC is initialized the user passes in the analog input channels they
    want to measure.

    Be sure that both the nidaqmx python library and the NIDaqMX Base is installed. NiDaqMX base (version 15.1 or higher)
    mustbe installed from national instruments website, it does not automatically install when the
    USB-6211 or other daq card is plugged in.

    >>>adc = Basic_ADC(channels = ['ai1', 'ai2'], mode = 'finite')
    >>>adc.start()
    >>> data = adc.read()
    """
    modes = {'continuous': nidaqmx.constants.AcquisitionType.CONTINUOUS,
             'finite': nidaqmx.constants.AcquisitionType.FINITE}

    def __init__(self, channels=['ai1', 'ai2', 'ai3'], mode='finite', sampling=5000, samples=5000, dev=0):

        # Create the task
        super().__init__(channels, mode, sampling, samples, dev)
        self.task = nidaqmx.Task()
        self.ni_tasks['adc'] = self.task


        # Add the channels
        for chan in channels:
            self.task.ai_channels.add_ai_voltage_chan('/' + self.devices[dev] + '/' + chan,
                                                      terminal_config=TerminalConfiguration.RSE)
        # Configure the Timing
        self.mode = self.modes[mode]
        self.task.timing.cfg_samp_clk_timing(sampling, samps_per_chan=samples, sample_mode=mode)

    def start(self):
        if self.mode == 'continuous':
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

    def __init__(self, channels=None, port="COM1"):  # Brae, what is COM4????
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
    cutoff = 4  # Cut off for digital filter
    output_freq = 1000  # Frequency for sending voltage levels to the Power supply (Can be much higher than analog in)
    clock_channel = 'ctr0'  # Sampling Clock channel (don't really need to change)
    sample_terminal = "Ctr0InternalOutput"  # Make sure this route is allowed via NIMAX
    mode = nidaqmx.constants.AcquisitionType.CONTINUOUS  # Sampling mode
    update_time = 1  # Time in seconds the DAQ should updat
    samples_per_chain = 50000  # Samples per buffer channel / how often it will update is samples_per_chain/freq
    max_time = 60  # Total amount of time to wait before exiting.
    voltage_ramp = 10  # speed to ramp voltage in kV/s
    voltage = 0  # Current voltage in V to send to the  daq. (-10 to 10 max)
    voltage_conversion = 30 / 10  # kV/daqV conversion factor
    current_conversion = 300 / 10
    rfu_conversion = 1
    temp_file = 'temp_data.csv'
    data_lock = threading.Lock()
    ba = (None, None)
    sos = None
    old_data = None
    middle_data = None
    downsampled_freq = 8

    # Laser States
    _pin3 = False  # Set to High to enable Laser
    _pin5 = True  # Set to Lo to enable laser

    def __init__(self, dev, voltage_read, current_read, rfu_read, voltage_control, stop=None, laser_fire=False):
        self.dev = dev
        self.voltage_control = voltage_control
        self.voltage_readout = voltage_read
        self.current_readout = current_read
        self.rfu_chan = rfu_read
        self._clear_data()
        self.filter_setup()

        # Set up laser (Could move to new class perhaps)
        if laser_fire:
            self.laser_task = nidaqmx.Task()
            self.start_laser_task()

        if stop is None:
            stop = threading.Event()
        self.stop = stop

    def _clear_data(self):
        with self.data_lock:
            self.data = {self.rfu_chan: [], self.current_readout: [],
                         self.voltage_readout: [], 'raw': [], 'avg': [],
                         'dt': []}  # RFU, Current and Voltage respectively
            try:
                os.remove(self.temp_file)
            except FileNotFoundError:
                pass
        return

    def close_tasks(self):
        self.laser_task.close()

    def callback(self, *args):
        """Add data to the data variable every so many samples
        Filter and decimate the data down to 5 Hz.
        Currently system uses PCI-6229 which has a SAR ADC.
        oversampling will increase the signal to noise by 10log(OSR) where
        OSR is the over sampling rate. It takes milliseconds to downsample,
        and if the computer is capable why not get the extra boost to your signal.
        The final sample rate will be between 2-10 Hz depending on the OSR frequency.
        Decimation dowsamples at a factor of 10.
        It is important that the final downsampled data is neither undersampling or oversampling
        the chromatogram (4-40 Hz, 10-20 points per smallest peak)
        To avoid rining we pad the data with the samples. We essentially keep track of
        samples from the last 2 call backs, the first 2 sampling periods will be a little off
        then the following samples will be good.
        Down sampling from 50kHz:
        data = samples(n-2), samples(n-1), samples (n)
        50,000 Hz sampling
        5,000 Hz (Decimate #1)
        500 Hz (Decimate #2)
        50 Hz (Decimate #3
        5 Hz (Decimate #4)
        return 5Hz_data (samples n-1)
        """
        # logging.info(args)
        try:
            samples = self.task.read(number_of_samples_per_channel=self.samples_per_chain)
        except nidaqmx.errors.DaqError:
            return
        with self.data_lock:
            # Filter and down sample the RFU data
            decimated = self.decimate_data(samples[2])
            self.downsampled_freq = len(decimated)
            self.data[self.rfu_chan].extend(decimated)  # RFU
            # Voltage and current don't matter as much so we will just average those
            self.data[self.voltage_readout].extend(
                self.average_data(samples[0], len(decimated), self.voltage_conversion))  # Voltage
            self.data[self.current_readout].extend(
                self.average_data(samples[1], len(decimated), self.current_conversion))  # Current

            # Get comparative chromatograms
            self.data['raw'].extend(self.raw_data(samples[2], len(decimated)))
            self.data['avg'].extend(self.average_data(samples[2], len(decimated)))
            self.old_data = self.middle_data
            self.middle_data = samples[2][:]

            # dt_step = len(decimate)
            # old_dt = self.data['dt'][-1] + (1 / dt_step)
            # self.data['dt'].extend(np.arange(old_dt, old_dt+1, 1/dt_step).tolist())
            with open(self.temp_file, 'a') as temp:
                [temp.write('{}\n'.format(x)) for x in self.average_data(samples[2], int(len(samples[2]) / 50))]

            # Apply butter filter to the data
            # self.data[self.rfu_chan] = self.filter_data(self.data[self.rfu_chan])
        return 0

    def sample_config(self, task):
        """We time the voltage in with a sample clock, here we set that up
        """
        chan = self.dev + self.clock_channel
        task.co_channels.add_co_pulse_chan_freq(chan, freq=self.freq)
        task.timing.cfg_implicit_timing(samps_per_chan=self.samples_per_chain,
                                        sample_mode=self.mode)
        return task

    def analog_out_config(self, task):
        voltage_chan = self.dev + self.voltage_control
        task.ao_channels.add_ao_voltage_chan(voltage_chan)
        task.timing.cfg_samp_clk_timing(self.output_freq)
        return task

    def analog_in_config(self, task, chan='ai3'):
        """Set up the analog read channels here"""
        chan = self.dev + self.voltage_readout
        task.ai_channels.add_ai_voltage_chan(chan)
        chan = self.dev + self.current_readout
        task.ai_channels.add_ai_voltage_chan(chan)
        chan = self.dev + self.rfu_chan
        task.ai_channels.add_ai_voltage_chan(chan)

        s_terminal = self.dev + self.sample_terminal
        task.timing.cfg_samp_clk_timing(self.freq, source=s_terminal,
                                        active_edge=Edge.FALLING,
                                        samps_per_chan=self.samples_per_chain,
                                        sample_mode=self.mode,
                                        )
        task.register_every_n_samples_acquired_into_buffer_event(
            self.samples_per_chain, self.callback)

        return task

    def start_read_task(self):
        """Starts thread to start the Reading Task"""
        if not self.stop.is_set():
            self.stop.set()
            time.sleep(0.2)
        self._clear_data()
        self.stop = threading.Event()
        threading.Thread(target=self.read_task, daemon=True).start()
        time.sleep(0.2)

    def read_task(self):
        """Create a new task, configure it, then run it. Consumes a thread
        should be target for thread"""
        # Set up the Clock
        sample_task = nidaqmx.Task()
        sample_task = self.sample_config(sample_task)

        # Set up the Analog Input Channels
        self.task = nidaqmx.Task()
        self.task = self.analog_in_config(self.task)

        # Set up the Analog Output Channels
        self.output_task = nidaqmx.Task()
        self.output_task = self.analog_out_config(self.output_task)

        # Prepare to start the run
        self.run = True
        start = time.time()
        # Run the task (Will Consume Thread, but releases resources on close)
        with self.task as task, sample_task as sk, self.output_task as outTask:
            task.start()
            outTask.start()
            sk.start()

            while time.time() - start < self.max_time and not self.stop.is_set():
                # Sleep our thread every 5 ms and check. Does not consume core during sleep
                time.sleep(0.005)

    def start_laser_task(self):
        self.laser_task.do_channels.add_do_chan('Dev1/port0/line0')  # pin3, Computer Control Channel
        self.laser_task.do_channels.add_do_chan('Dev1/port0/line1')  # pin 5, Laser OnOFf Channel
        self.laser_task.do_channels.add_do_chan('Dev1/port0/line5')  # Pulse Command Channel
        self.laser_task.write([False, True, False])

    def laser_fire(self):
        """
        This is a thread blocking task. Requires the laser to be in standby mode before firing. We set the pulse to
        50 ms.
        :return:
        """

        self.laser_task.write([True, True, True])  # Read the docs, good luck
        time.sleep(0.05)
        self.laser_task.write([False, True, False])

    def change_voltage(self, voltage):
        """ voltage in kV, used to adjust analog output (divided voltage-conversion factor"""
        # Convert kV to daq V
        voltage = float(voltage) / self.voltage_conversion
        diff = float(voltage) - self.voltage
        if diff == 0:
            self.output_task.write(0)
            self.voltage = voltage
            return
        # Get samples to send DAQ
        samples = self.get_voltage_ramp(voltage, diff)
        # Reset current voltage
        self.output_task.write(samples)
        self.voltage = voltage
        logging.info('Voltage set to {}'.format(voltage))

    def get_voltage_ramp(self, voltage, diff):
        """When changing voltages, ramp up the voltage output"""
        # Create a ramp from the current voltage to the set voltage

        ramp_time = abs(float(diff) / self.voltage_ramp)
        logging.info(ramp_time)
        samples = round(ramp_time * self.output_freq)
        logging.info(samples)
        self.samples = samples = np.linspace(self.voltage, voltage, samples)

        return samples

    def save_data(self, filename):
        with open(filename, 'w') as f_in:
            f_in.write('time, rfu, kV, uA, avg, raw\n')
            data = self.data
            for i in range(len(data[self.rfu_chan])):
                t_point = float(i * (1 / self.downsampled_freq))
                rfu = data[self.rfu_chan][i]
                ua = data[self.current_readout][i]
                kv = data[self.voltage_readout][i]
                avg = data['avg'][i]
                raw = data['raw'][i]
                try:
                    f_in.write('{:.3f},{},{:.3f},{:.3f},{},{}\n'.format(t_point, rfu, ua, kv, avg, raw))
                except TypeError:
                    f_in.write("{},{},{},{},{},{}\n".format(t_point, rfu, ua, kv, avg, raw))

        destination = filename[:-4] + '_raw_data.csv'
        try:
            shutil.move(self.temp_file, destination)
        except FileNotFoundError:
            logging.warning('Could not find {}'.format(self.temp_file))

    @staticmethod
    def raw_data(data, points):
        raws = []
        for i in range(points):
            idx = int(len(data) / points)
            raws.append(data[idx * i])
        return raws

    @staticmethod
    def average_data(data, points, conversion=1):
        avgs = []
        for i in range(points):
            idx = int(len(data) / points)
            avgs.append(np.mean(data[idx * i:idx * i + idx]) * conversion)
        return avgs

    def decimate_data(self, data):
        """ Decimates the data by applying a LP filter and then down sampling by a factor of 10
        FIR filter is used since it will be more stable if the user changes things up slightly
        returns data that has been downsampled
        """
        if self.old_data is None:
            self.old_data = data[:]
        elif self.middle_data is None:
            self.middle_data = data[:]
        else:
            self.middle_data.extend(data)
            self.old_data.extend(self.middle_data)
            data = self.old_data
        while len(data) > 30:
            try:
                data = signal.decimate(data, 10, 40, 'fir')
            except IndexError:
                self.stop.set()
                print(len(data))
                break

        data = data.tolist()
        data = data[int(len(data) / 3):-int(len(data) / 3)]
        return data

    def filter_data(self, data):
        """ Applies a digital butter filter to the data """
        logging.debug("FilterData")
        if len(data) < 10:
            return data
        if self.sos is None:
            # Apply filter forwards and backwards to remove ringing at start
            # Padlength must be less than the rows in our data
            pad = 3 * max(len(self.ba[0]), len(self.ba[1]))
            if pad >= len(data) - 1:
                pad = 0

            data = signal.filtfilt(self.ba[0], self.ba[1], data, padlen=pad).tolist()
        else:
            data = signal.sosfilt(self.sos, data).tolist()

        return data

    def filter_setup(self, poles=8, method='filtfilt'):
        """
        Sets up butter filter
        """

        def get_wn(desired, smpls):
            return desired / (smpls / 2)

        cutoff = self.cutoff
        sampling = self.freq
        if method == 'filtfilt':
            # Create a low pass filter without ringing
            b, a = signal.butter(poles, get_wn(cutoff, sampling), 'lp', analog=False)
            self.ba = (b, a)

        else:
            sos = signal.butter(poles, get_wn(cutoff, sampling), 'lp', analog=False, output='sos')
            self.sos = sos


if __name__ == "__main__":
    # adc = Basic_ADC(channels = ['ai1', 'ai2'], mode='continuous')
    # adc.start()
    # x = adc.read()
    dac = NI_DAC(channels=['ao0', 'ao1'])
    dac.set_voltage('ao0', 5.5)
    dac.load_changes()
