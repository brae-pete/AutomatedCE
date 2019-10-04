from nidaqmx.constants import Edge
import nidaqmx
import numpy as np
import logging
import time
import threading
from scipy import signal
import shutil
import os
import matplotlib.pyplot as plt

DEV = "/Dev1/"
CURRENT_OUT = "ai2"
VOLTAGE_IN = "ai1"
VOLTAGE_OUT = 'ao1'
RFU = "ai3"

class DAQBoard:
    freq = 50000 # Sampling frequency for analog inputs
    cutoff=4 # Cut off for digital filter
    output_freq = 1000  # Frequency for sending voltage levels to the Power supply (Can be much higher than analog in)
    clock_channel = 'ctr0'  # Sampling Clock channel (don't really need to change)
    sample_terminal = "Ctr0InternalOutput"  # Make sure this route is allowed via NIMAX
    mode = nidaqmx.constants.AcquisitionType.CONTINUOUS  # Sampling mode
    update_time = 1 # Time in seconds the DAQ should updat
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
    old_data=None
    middle_data=None
    downsampled_freq=8

    def __init__(self, dev, voltage_read, current_read, rfu_read, voltage_control, stop=None):
        self.dev = dev
        self.voltage_control = voltage_control
        self.voltage_readout = voltage_read
        self.current_readout = current_read
        self.rfu_chan = rfu_read
        self._clear_data()
        self.filter_setup()

        if stop is None:

            stop = threading.Event()
        self.stop = stop

    def _clear_data(self):
        with self.data_lock:
            self.data = {self.rfu_chan: [], self.current_readout: [],
                         self.voltage_readout: [], 'raw':[], 'avg':[], 'dt':[]}  # RFU, Current and Voltage respectively
            try:
                os.remove(self.temp_file)
            except FileNotFoundError:
                pass
        return

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
            self.downsampled_freq=len(decimated)
            self.data[self.rfu_chan].extend(decimated)  # RFU
            # Voltage and current don't matter as much so we will just average those
            self.data[self.voltage_readout].extend(self.average_data(samples[0], len(decimated), self.voltage_conversion))  # Voltage
            self.data[self.current_readout].extend(self.average_data(samples[1], len(decimated), self.current_conversion)) # Current

            #Get comparative chromatograms
            self.data['raw'].extend(self.raw_data(samples[2],len(decimated)))
            self.data['avg'].extend(self.average_data(samples[2], len(decimated)))
            self.old_data = self.middle_data
            self.middle_data = samples[2][:]

            #dt_step = len(decimate)
            #old_dt = self.data['dt'][-1] + (1 / dt_step)
            #self.data['dt'].extend(np.arange(old_dt, old_dt+1, 1/dt_step).tolist())
            with open(self.temp_file,'a') as temp:
                [temp.write('{}\n'.format(x)) for x in self.average_data(samples[2], int(len(samples[2])/50))]


            # Apply butter filter to the data
            #self.data[self.rfu_chan] = self.filter_data(self.data[self.rfu_chan])
        return 0
    @staticmethod
    def raw_data(data, points):
        raws = []
        for i in range(points):
            idx = int(len(data)/points)
            raws.append(data[idx*i])
        return raws
    @staticmethod
    def average_data(data, points,conversion=1):
        avgs = []
        for i in range(points):
            idx = int(len(data)/points)
            avgs.append(np.mean(data[idx*i:idx*i+idx])*conversion)
        return avgs

    def decimate_data(self,data):
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


        data=data.tolist()
        data=data[int(len(data)/3):-int(len(data)/3)]
        return data


    def filter_data(self,data):
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




    def sample_config(self, task):
        """We time the voltage in with a sample clock, here we set that up
        """
        chan = self.dev + self.clock_channel
        task.co_channels.add_co_pulse_chan_freq(chan, freq=self.freq)
        task.timing.cfg_implicit_timing(samps_per_chan=self.samples_per_chain,
                                        sample_mode=self.mode)
        return task

    def analog_out_config(self, task):
        chan = self.dev + self.voltage_control
        task.ao_channels.add_ao_voltage_chan(chan)
        task.timing.cfg_samp_clk_timing(self.output_freq)
        return task

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

    def save_data(self, filename):
        with open(filename, 'w') as f_in:
            f_in.write('time, rfu, kV, uA, avg, raw\n')
            data = self.data
            for i in range(len(data['ai3'])):
                t_point = float(i * (1 / self.downsampled_freq))
                rfu = data['ai3'][i]
                ua = data['ai2'][i]
                kv = data['ai1'][i]
                avg = data['avg'][i]
                raw = data['raw'][i]
                try:
                    f_in.write('{:.3f},{},{:.3f},{:.3f},{},{}\n'.format(t_point, rfu, ua, kv, avg, raw))
                except TypeError:
                    f_in.write("{},{},{},{},{},{}\n".format(t_point, rfu, ua, kv,avg,raw))

        destination = filename[:-4] + '_raw_data.csv'
        try:
            shutil.move(self.temp_file, destination)
        except FileNotFoundError:
            logging.warning('Could not find {}'.format(self.temp_file))



if __name__ == "__main__":
    dq=DAQBoard(DEV,VOLTAGE_IN,CURRENT_OUT,RFU,VOLTAGE_OUT)
    dq.start_read_task()
