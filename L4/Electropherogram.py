import numpy as np
from scipy.interpolate import interp1d


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
    return (peak_area-base_area) / max_t * length_to_detector


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
