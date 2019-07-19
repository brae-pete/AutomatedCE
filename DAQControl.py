from nidaqmx.constants import Edge
import nidaqmx
import numpy as np
import logging
import time
import threading


class DAQBoard:
    freq = 4  # Sampling frequency for analog inputs
    output_freq = 1000  # Frequency for sending voltage levels to the Power supply (Can be much higher than analog in)
    clock_channel = 'ctr0'  # Sampling Clock channel (don't really need to change)
    sample_terminal = "Ctr0InternalOutput"  # Make sure this route is allowed via NIMAX
    mode = nidaqmx.constants.AcquisitionType.CONTINUOUS  # Sampling mode
    samples_per_chain = 4  # Samples per buffer channel / how often it will update is samples_per_chain/freq
    max_time = 60  # Total amount of time to wait before exiting.
    voltage_ramp = 10  # speed to ramp voltage in kV/s
    voltage = 0  # Current voltage in V to send to the  daq. (-10 to 10 max)
    voltage_conversion = 30 / 10  # kV/daqV conversion factor

    def __init__(self, dev='/Dev1/', stop=None):
        self.dev = dev
        self.data = {'ai3': [], 'ai2': [], 'ai1': []}
        if stop is None:
            stop = threading.Event()
        self.stop = stop

    def callback(self, *args):
        """Add data to the data variable every so many samples"""
        # logging.info(args)
        try:
            samples = self.task.read(number_of_samples_per_channel=self.samples_per_chain)
        except nidaqmx.errors.DaqError:
            return
        self.data['ai1'].extend([x*self.voltage_conversion for x in samples[0]])
        self.data['ai2'].extend([x*self.voltage_conversion for x in samples[1]])
        self.data['ai3'].extend([x*self.voltage_conversion for x in samples[2]])
        return 0

    def sample_config(self, task):
        """We time the voltage in with a sample clock, here we set that up
        """
        chan = self.dev + self.clock_channel
        task.co_channels.add_co_pulse_chan_freq(chan, freq=self.freq)
        task.timing.cfg_implicit_timing(samps_per_chan=self.samples_per_chain,
                                        sample_mode=self.mode)
        return task

    def analog_out_config(self, task, chan='ao1'):
        chan = self.dev + chan
        task.ao_channels.add_ao_voltage_chan(chan)
        task.timing.cfg_samp_clk_timing(self.output_freq)
        return task

    def change_voltage(self, voltage):
        """ voltage in kV, used to adjust analog output (divided voltage-conversion factor"""
        # Convert kV to daq V
        voltage = float(voltage) / self.voltage_conversion
        diff = float(voltage) - self.voltage
        if diff == 0:
            # self.output_task.write(0)
            self.voltage = voltage
            return
        # Get samples to send DAQ
        samples = self.get_voltage_ramp(voltage, diff)
        # Reset current voltage
        # self.output_task.write(samples)
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
        chan = self.dev + 'ai1'
        task.ai_channels.add_ai_voltage_chan(chan)
        chan = self.dev + 'ai2'
        task.ai_channels.add_ai_voltage_chan(chan)
        chan = self.dev + 'ai3'
        task.ai_channels.add_ai_voltage_chan(chan)

        s_terminal = self.dev + self.sample_terminal
        task.timing.cfg_samp_clk_timing(self.freq, source=s_terminal,
                                        active_edge=Edge.FALLING,
                                        samps_per_chan=self.samples_per_chain,
                                        sample_mode=self.mode)
        task.register_every_n_samples_acquired_into_buffer_event(
            self.samples_per_chain, self.callback)

        return task

    def start_read_task(self):
        """Starts thread to start the Reading Task"""
        if not self.stop.is_set():
            self.stop.set()
            time.sleep(0.2)
        self.data = {'ai1': [], 'ai2': [], 'ai3': []}
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
