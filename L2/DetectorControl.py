import threading
from abc import ABC, abstractmethod
from scipy import signal
from L2.Utility import UtilityControl, UtilityFactory
from L1.DAQControllers import DaqAbstraction
import numpy as np


# Filtering Functions
def butter_lowpass_filter(data, kwargs):
    """
    Apply a butterworth lowpass filter to the data set.
    Keyword arguments will be used in a dictionary of filter settings:
    'cutoff' - frequency cutoff, should be < 1/2 the sampling frequency (fs)
    'fs' - sampling frequncy, the frequency measurments are recorded at
    'order' - order of the butter filter
    'padlen' - how much to pad the beginning and end of the array (see scipy.signal.butter)
    'padtype' - how to pad the ends of the array (see scipy.signal.butter)

    :param data: 1D equally spaced array
    :param kwargs: dict,
    :return:
    """

    def butter_lowpass(cutoff, fs, order=5):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
        return b, a

    settings = {'cutoff': 3, 'fs': 10, 'order': 5, 'padlen': 24, 'padtype': 'constant'}
    settings.update(kwargs)
    if len(data) < settings['padlen']:
        return data
    b, a = butter_lowpass(settings['cutoff'], settings['fs'], order=settings['order'])
    y = signal.filtfilt(b, a, data, padlen=settings['padlen'], padtype=settings['padtype'])

    return y


def savgol_filter(data, kwargs):
    """
    Apply a Savitzky-Golay filter to smooth the data
    Keyword arguments will be used to set the filter settings:
    'window_length' = length of the filter window, or number of coefficients
    'poly_order' = polynomial order to fit the samples to
    'padtype' = Extension type to pad the signal. 'mirror', 'constant', 'wrap', or 'interp'
        (see scipy.signal.savgol_filter)

    :param data: 1-d array
    :param kwargs: see settings above
    :return:
    """

    settings = {'window_length': 25, 'poly_order': 3, 'mode': 'constant'}
    for key, value in kwargs.items():
        settings[key] = value

    return signal.savgol_filter(data, settings['window_length'], settings['polyorder'], mode=settings['mode'])


class DetectorAbstraction(ABC):
    """
    Utility class for handling data coming from a fluorsence detector

    get_raw_data : get the data without a filter applied to it
    get_data : get the filtered data
    add_data: adds incoming data to the data variable

    """

    def __init__(self, controller, role):
        self.daqcontroller = controller
        self.role = role
        self.rfu = np.asarray([])
        self.time = np.asarray([])
        self._lock = threading.RLock()
        self._sampling_f = 100000
        self._final_f = 10
        self._oversample = True
        self._oversample_buffer = np.asarray([])
        settings = {'cutoff': 1.5, 'fs': 10, 'order': 2, 'padlen': 24, 'padtype': 'constant'}
        self._filter_type = ['butter', settings]

    @abstractmethod
    def get_data(self):
        """
        Applies a filter (if any selected) and returns the filtered data
        :return:
        """
        pass

    @abstractmethod
    def set_sample_frequency(self, frequency):
        """
        Sets the sampling frequency for the detector
        :param frequency:
        :return:
        """

    @abstractmethod
    def set_oversample_frequency(self, sampling_frequency, final_frequency):
        """
        Sets the paramaters for an oversampling filter
        :param sampling_frequency:
        :param final_frequency:
        :return:
        """

    @abstractmethod
    def get_raw_data(self):
        """
        Returns the raw data without filter
        :return:
        """
        pass

    @abstractmethod
    def set_filter_type(self, type, **kwargs):
        """
        Sets the type of digital filter to apply
        :param type:
        :param kwargs:
        :return:
        """
        pass

    @abstractmethod
    def add_data(self, incoming_data, samples, *args):
        """
        Adds data to the data variable
        :param incoming_data:
        :param samples:
        :param args:
        :return:
        """
        pass

    @abstractmethod
    def start(self):
        """
        Starts measuring the detector signal
        :return:
        """
        pass

    @abstractmethod
    def stop(self):
        """
        Stops measuring the detector signal
        :return:
        """
        pass


class PhotomultiplierDetector(DetectorAbstraction, UtilityControl):
    """
    This is a class to control data coming from a single channel photomultiplier typically using a daqcontroller.

    Inputs should include the analog input channel that needs to be read.
    config examples digilent:
    utility,daq1,detector,detector,pmt,1

    config example national instruments
    utility,daq1,detector,detector,pmt,ai5

    Inclues oversampling and sampling
    """

    def __init__(self, controller: DaqAbstraction,role,  channel):
        super().__init__(controller, role)
        self.daqcontroller.add_analog_input(channel, terminal_config="DIFF")
        self.daqcontroller.add_callback(self.add_data, [channel], 'waveform', [])
        self.set_oversample_frequency(80000,8)

    def set_oversample_frequency(self, sampling_frequency, final_frequency):
        """
        Enables and sets the oversampling filter.
        :param frequency:
        :return:
        """
        self._final_f = final_frequency
        self._sampling_f = sampling_frequency
        self._oversample = True
        self.daqcontroller.set_sampling_frequency(sampling_frequency)

    def set_sample_frequency(self, frequency):
        """
        Sets the sampling frequency for the device.
        :param frequency:
        :return:
        """
        self._sampling_f = frequency
        self._oversample = False
        self.daqcontroller.set_sampling_frequency(frequency)

    def set_filter_type(self, type, **kwargs):
        """
        Sets up the settings for a digital filter.
        :param type:
        :param kwargs:
        :return:
        """
        self._filter_type = [type, kwargs]

    def get_raw_data(self):
        """
        Returns a copy of the raw data
        :return:
        """
        with self._lock:
            return {'time_data': self.time.copy(), 'rfu': self.rfu.copy()}

    def get_data(self):
        """
        Returns a filtered copy of the data
        :return:
        """
        filter_type, kwargs = self._filter_type
        locked = self._lock.acquire(timeout=0.2)
        if not locked:
            return None

        if filter_type == 'butter':
            filtered = butter_lowpass_filter(self.rfu.copy(), kwargs)
        elif filter_type == 'savgol':
            filtered = savgol_filter(self.rfu.copy(), kwargs)
        else:
            filtered = self.rfu.copy()
        self._lock.release()

        return {'time_data': self.time.copy(), 'rfu': filtered}

    def add_data(self, incoming_data, time_elapsed, *args):
        """
        Adds incoming data and oversample filters it as necessary
        :param time_elapsed:
        :param incoming_data: should be a list of numpy arrays
        :param args:
        :return:
        """
        with self._lock:
            if self._oversample:
                self._add_oversampled_data(incoming_data[0], self._sampling_f / self._final_f)
            else:
                self.rfu = np.append(self.rfu, incoming_data[0])
                self.time = np.linspace(0, len(self.rfu)/self._sampling_f, num=len(self.rfu), endpoint=False)

    def _add_oversampled_data(self, data, sample_n):
        """
        Adds oversampled data to the RFU array.

        Uses a data buffer, and adds data to the buffer until the buffer length is long enough to average a new
        data value at the final sampling frequency.

        :param data: 1-d array
        :param samples_n: number of samples, or the oversampling frequency divided by the final frequency
        :return:
        """
        self._oversample_buffer = np.append(self._oversample_buffer, data)
        sample_n = int(sample_n)
        while len(self._oversample_buffer) >= sample_n:
            self.rfu = np.append(self.rfu, np.mean(self._oversample_buffer[0:sample_n]))
            self._oversample_buffer = np.delete(self._oversample_buffer, np.s_[0:sample_n])
        self.time = np.linspace(0,len(self.rfu)/self._final_f, num=len(self.rfu), endpoint=False)

    def start(self):
        """
        Starts the daqcontroller measurement process
        :return:
        """
        with self._lock:
            self.rfu = np.asarray([])
            self.time = np.asarray([])
            self._oversample_buffer = np.asarray([])
        self.daqcontroller.start_measurement()

    def stop(self):
        """
        Stops the daq controller  measurement process
        :return:
        """
        self._copy_data=self.get_data()
        self.daqcontroller.stop_measurement()

    def startup(self):
        """
        Do nothing special on startup
        :return:
        """
        pass

    def shutdown(self):
        """
        Stop measurement collection on shutdown
        :return:
        """
        self.daqcontroller.stop_measurement()

    def get_status(self):
        """
        Returns the filtered data set
        :return:
        """
        with self._lock:
            return self.get_data()


class DetectorFactory(UtilityFactory):
    """ Determines the type of detector utility object to return according to the controller id"""

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
            if settings[4]=='pmt':
                return PhotomultiplierDetector(controller, role, settings[5])
            else:
                return None
        else:
            return None