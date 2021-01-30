import numpy as np
from scipy.interpolate import interp1d, UnivariateSpline
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import sem
from scipy.fftpack import fft
from scipy import signal
import os
import peakutils


def get_corrected_peak_area(time_data: np.ndarray, rfu_data: np.ndarray, peak_start, peak_stop, length_to_detector=1):
    """
    Returns the time_data corrected peak area for for a peak for a given electropherogram.
    Subtracts the baseline area of the peak using a linear approximation between the start and stop points
    Distance to the detector can be accounted for by adjusting the length_to_detector parameter.

    :param time_data: numpy array  of time_data data
    :param rfu_data: numpy array of rfu_data
    :param peak_start: time_data where peak starts
    :param peak_stop: time_data where peak should stop
    :return peak_area: corrected area of the peak
    """

    peak_start, peak_stop = get_rounded_time(peak_start, time_data), get_rounded_time(peak_stop, time_data)
    index_start, index_stop = np.where(time_data == peak_start)[0], np.where(time_data == peak_stop)[0]
    max_t = time_data[rfu_data[index_start:index_stop].argmax()]
    # Get the peak area
    peak_area = np.trapz(rfu_data[index_start:index_stop], time_data[index_start:index_stop])
    # Get the peak baseline area
    base_area = np.trapz(rfu_data[index_start, index_stop], [index_start, index_stop])
    return (peak_area - base_area) / max_t * length_to_detector


def get_rounded_time(x: float, time_data: np.ndarray):
    """
    Rounds the wanted time_data point to the same resolution that the time_data array is given in
    :param x: time_data point needed to be rounded
    :param time_data: array of evenly distributed time_data points
    :return: rounded x
    :rtype: float
    """
    scale = 1 / (time_data[1] - time_data[0])
    return float(round(x * scale) / scale)


class peakcalculations():
    """ Requires time, rfu arrays and the start and stop values for the peak

    Need to account for RFU Baseline!"""

    def __init__(self, time, RFU, value1, value2, distance2detector=20, poly=False, skip=0):
        self.time = time
        self.rfu = RFU

        # print(self.rfu[0], "Before correction", len(self.rfu))
        new_baseline = baseline(self.rfu)
        self.rfu = new_baseline.correctedrfu
        # print(self.rfu[0], "After Correction", len(self.rfu))
        if poly != False:
            self.rfu = np.array(self.rfu)
            self.baseline = new_baseline.peakutils_baseline(poly, skip)
            self.rfu = list(self.rfu - self.baseline)
        self.rnrfu, self.rntime = self.getindexes(value1, value2)
        self.distance2detector = distance2detector
        self.start = value1
        self.stop = value2
        # if len(self.rnrfu)<1:
        #   print(time, "Time \n" , RFU, "RFU\n", value1,value2)

    # print(self.rnrfu)
    def peakutil_baseline(self, polynomial=3):
        self.rfu = np.array(self.rfu)
        self.baseline = peakutils.baseline(self.rfu, polynomial)
        return self.baseline

    def getindexes(self, value1, value2):
        # retrieve indexes that correspond to where we selected widths on the graph
        startind, stopind = get_indices(self.time, value1, value2)
        self.stopind = stopind  # use this for resolution helps
        self.startind = startind
        return [self.rfu[startind:stopind], self.time[startind:stopind]]

    def get_starttime(self):
        return self.start

    def get_stoptime(self):
        return self.stop

    def get_area(self):
        # Calculate area using a trapazoid approximation
        area = np.trapz(self.rnrfu, self.rntime)
        return area

    def get_m1(self):
        # Get the First moment, or tr
        rn3 = np.multiply(self.rnrfu, self.rntime)
        m1 = sum(rn3) / sum(self.rnrfu)
        return m1

    def get_m2(self):
        # get the second moment
        m1 = self.get_m1()
        rn3 = np.multiply(((self.rntime - m1) ** 2), self.rnrfu)
        m2 = np.sum(rn3) / np.sum(self.rnrfu)
        return m2

    def get_m3(self):
        # get the third moment
        m1 = self.get_m1()
        rn3 = np.multiply(((self.rntime - m1) ** 3), self.rnrfu)
        m3 = np.sum(rn3) / np.sum(self.rnrfu)
        return m3

    def get_m4(self):
        # get the fourth moment
        m1 = self.get_m1()
        rn3 = np.multiply(((self.rntime - m1) ** 4), self.rnrfu)
        m4 = np.sum(rn3) / np.sum(self.rnrfu)
        return m4

    def get_max(self):
        return max(self.rnrfu)

    def get_maxtime(self):
        # get the tr at Max height
        tr = self.rntime[self.rnrfu.index(max(self.rnrfu))]
        return tr

    def get_fwhm(self):
        """uses a 3rd degree smoothing spline to model the peak. All half max is subtracted from
        all the rfu data. """
        maxrfu = max(self.rnrfu)
        halfmax = maxrfu / 2
        # create a spline of x and blue-np.max(blue)/2
        # print(len(self.rntime), len(self.rnrfu), len(np.subtract(self.rnrfu, halfmax)))
        spline = UnivariateSpline(np.asarray(self.rntime), np.subtract(self.rnrfu, halfmax), s=0)
        # find the roots
        roots = spline.roots()
        # if we don't have our peaks separated all the way and cant reach half max
        if len(roots) < 2:
            r2 = self.rntime[-1]
            r1 = self.rntime[0]
        else:
            r2 = roots[-1]
            r1 = roots[0]
            # print(r2, r1, "were r's", self.rntime[self.rnrfu.index(maxrfu)])
            if r2 < self.rntime[self.rnrfu.index(maxrfu)]:
                r2 = self.rntime[-1]
            if r1 > self.rntime[self.rnrfu.index(maxrfu)]:
                r1 = self.rntime[0]
        fwhm = np.abs(r2 - r1)
        # print(fwhm, " is the FWHM")
        self.spline = spline
        return fwhm

    def get_correctedarea(self):
        """ Area needs to be corrected or normalized for diffent mobilities
        CA = A * velocity
        CA = A * Ldetector / retention time or
        CA = A / retention time, this cant be compared between instruments
        """
        m1 = self.get_m1()
        area = self.get_area()
        correctedarea = area / m1
        # print(correctedarea, " is the CA")
        return correctedarea

    def get_snr(self, noise):
        """
        Max signal (baseline corrected) divided by the noise RMS of the chromatogram (portion defined by user)
        :param noise: float noise RMS value
        :return: float Signal to Noise ratio
        """
        sig = max(self.rnrfu)
        # return s/n calculation
        return sig / noise


class baseline():
    """Corrected baseline stored as correctedRFU calculated from correct
    If a separate method for baseline is needed to be called you can change
    the correct function, or add another method/function. Just call the function
    in the GUI to call you function.

    Additionally you can use lower_median which takes a value from a specified portion of the
    all the numbers sorted as the baseline. This method also corrects for negative
    y values. Preferential for UV analysis"""

    def __init__(self, rfu):
        self.rfu = rfu
        self.correctedrfu = []
        self.correctedrfu = self.lower_median()

    def firstlast50(self, x=50):
        first = np.average(self.rfu[:x])
        last = np.average(self.rfu[-x:])
        self.linecalc(first, last)

    def lower_median(self, lower_value=0.2):
        try:
            sortedRfu = self.rfu[:]
            sortedRfu.sort()
            medianIndex = np.floor(len(sortedRfu) * lower_value)
            medianIndex = int(medianIndex)
            self.correctedrfu = [i - sortedRfu[medianIndex] for i in self.rfu]
            lowest_value = min(self.correctedrfu)

            # if lowest_value < 0:
            #    print("Correction")
            #    new_correctedrfu = [i - lowest_value for i in self.correctedrfu]
            # print("Finished", len(new_correctedrfu))
            # self.correctedrfu = new_correctedrfu
            return self.correctedrfu
        except Exception as e:
            print("Did not correct baseline")
            print(str(e))

    def peakutils_baseline(self, polynomial, skip=0):
        """Requires corrected RFU to be run first"""

        # If polynomial is too large GigaCE freezes, this is a catch to prevent freezing
        if polynomial > 10:
            print("Polynomial too large")
            return self.correctedrfu

        base = peakutils.baseline(np.array(self.correctedrfu[skip:]), polynomial)
        # print(base)
        # print(len(base))
        Xtotal = np.linspace(0, len(base) + skip, len(base) + skip)
        # print(len(Xtotal))
        # print(Xtotal)
        fit = np.polyfit(Xtotal[skip:], base, polynomial)
        # print(fit)
        p = np.poly1d(fit)
        base = p(Xtotal)
        baseline = list(base)
        return baseline

    def peakutils_indexes(self, thresh=3, min_dist=1):
        self.peak_indexes = peakutils.indexes(self.rfu, thresh, min_dist)
        return self.peak_indexes

    def linecalc(self, y1, y2):
        xt = len(self.rfu)
        self.m = (y2 - y1) / xt
        self.b = y1

    def subtract(self, x, y):
        y1 = self.m * x + self.b
        return y - y1

    def correct(self):
        correctedrfu = []
        for x, y in enumerate(self.rfu):
            correctedrfu.append(self.subtract(x, y))
        return correctedrfu


def get_indices(time, value1, value2):
    """ returns the incices from two coordinate values from the time array"""
    dt = time[1] - time[0]
    startind = time.index(round(value1 / dt) * dt)
    stopind = time.index(round(value2 / dt) * dt)
    return [startind, stopind]


CUTOFF = 2
ORDER = 3
FS = 8


# General Filter call
def filter_data(data):
    "Put whatever filter you want to use here, should return the filtered data "
    return butter_lowpass_filter(data, CUTOFF, FS, ORDER)


# Filtering Functions
def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
    return b, a


def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = signal.filtfilt(b, a, data, padlen=24, padtype='constant')
    return y


def savgol_filter(data):
    window_length = 25  # length of the filter window (number of coefficients)
    polyorder = 3
    mode = 'constant'
    return signal.savgol_filter(data, window_length, polyorder, mode=mode)


def filter_butter(separation, cutoff: float, order: int):
    """
    Butterworth digital filter, applies the filter forwards and backwards so the end result
    won't have a phase shift. Order will be multiplied by 2 (once for each pass of the filter).

    :param separation: Separation to filter
    :param cutoff: Digital filter cutoff
    :param order: Order for the single pass of the filter
    :return: filtered RFu
    """

    # Filtering Functions
    # noinspection PyTupleAssignmentBalance
    def butter_lowpass():
        nyq = 0.5 * dt
        normal_cutoff = cutoff / nyq
        b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
        return b, a

    dt = 1 / np.median(np.diff(separation.time_data))
    b, a = butter_lowpass()
    rfu_filtered = signal.filtfilt(b, a, separation.rfu, padlen=24, padtype='constant')

    return rfu_filtered


def filter_savgol(separation, window_size: int, poly_order: int):
    """
    Performs a savintsky-golay filter of the dataset, applying a gaussian window of the specified size across
    the dataset.

    :param separation:
    :param window_size: must be odd number, size of window
    :param poly_order:  Polynomial to apply for fit
    :return:
    """

    mode = 'mirror'
    return signal.savgol_filter(separation.rfu, window_size, poly_order, mode=mode)


# Auto analyze your data

def find_noise(Y, width=50, skip=5):
    noise = np.nan
    background = np.nan
    for i in range(skip, len(Y) - width - skip):
        new_noise = np.std(Y[i:i + width])

        if new_noise < noise or np.isnan(noise):
            noise = new_noise
            background = np.median(Y)
            # print(noise, background)
    return noise, background


def get_auto_peak_data(pk, properties, rfu, time, background, noise):
    data = {'max': [], 'SNR': [], 'noise': [], "background": [], "retention_time": []}
    data['max'].append(rfu[pk] - background)
    data['SNR'].append((rfu[pk] - background) / noise)
    data['noise'].append(noise)
    data['background'].append(background)
    data['retention_time'].append(time[pk])


def get_m1(pk_rfu, pk_time):
    # Get the First moment, or tr
    rn3 = np.multiply(pk_rfu, pk_time)
    m1 = sum(rn3) / sum(pk_rfu)
    return m1


def get_corrected_area(pk_rfu, pk_time, m1):
    """ Area needs to be corrected or normalized for diffent mobilities
    CA = A * velocity
    CA = A * Ldetector / retention time or
    CA = A / retention time, this cant be compared between instruments
    """
    area = get_area(pk_rfu, pk_time)
    correctedarea = area / m1
    return correctedarea


def get_area(pk_rfu, pk_time):
    # Calculate area using a trapazoid approximation
    area = np.trapz(pk_rfu, pk_time)
    return area