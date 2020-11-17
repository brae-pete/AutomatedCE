"""
This file contains all the functions/methods to write data from the System to a file object.

It also contains all functions to read in data from the System
"""
from L3.SystemsBuilder import CESystem
from scipy.interpolate import interp1d
import os
from pathlib import Path
import numpy as np

# Get the Home Directory Location
HOME = os.getcwd().split("AutomatedCE")[0] + "AutomatedCE"


def get_system_var(*var_names):
    """
    Get a variable from the system config file
    :param var_names: str
    :return:
    """
    # Get the Var file
    var_path = os.path.join(HOME, "config", "system_var.txt")
    with open(var_path) as fin:
        var_lines = fin.readlines()

    var_dict = {}

    for var_str in var_lines:
        var_list = var_str.split(',')
        var_dict[var_list[0]] = eval(var_list[1].replace('\n',''))

    response = []
    for var_name in var_names:
        assert var_name in var_dict.keys(), f"{var_name} is not a var in system_var.txt"
        response.append(var_dict[var_name])

    return response


def get_data_filename(name, file_dir, extension=".csv"):
    """
    Returns a unique filename by adding 0's to the end of the name (but before the file suffix).
    :param name: str
    :param file_dir: str
    :return file_name: str
    """
    # Check if directory exists and make it if not
    Path(file_dir).mkdir(parents=True, exist_ok=True)

    file_name = os.path.join(file_dir, name+extension)
    copy_number = 0
    while os.path.exists(file_name):
        new_name = name + f"_{copy_number:05d}" + extension
        file_name = os.path.join(file_dir, new_name)
        copy_number += 1
    return file_name

def get_data_folder(name, file_dir):
    """
    Returns a unique folder name by adding 0's to the end of the name
    :param name:
    :param file_dir:
    :return:
    """
    # Check if directory exists and make it if not
    Path(file_dir).mkdir(parents=True, exist_ok=True)

    folder = os.path.join(file_dir, name)
    copy_number = 0
    while os.path.isdir(folder):
        new_name = name + f"_{copy_number:05d}"
        folder = os.path.join(file_dir, new_name)
        copy_number += 1
    Path(folder).mkdir(parents=True, exist_ok=True)
    return folder

class OutputElectropherogram:
    """
    Writes electropherogram data from the system to the
    """
    def __init__(self, system: CESystem, filepath, header=""):
        """
        Get the data from the System and write it to the file specified
        :param system:
        :param filepath:
        """
        data = self.get_data(system)
        self.write_data(data, header, filepath)

    @staticmethod
    def write_data(data, header, filepath):
        """
        Writes the CE data file containing a time_data column, a RFU, a kV and a uA column.
        incoming data should be in that order (time_data, rfu, voltage, current)
        data = [list of lists or numpy arrays]
        filepath = filepath of location to save the object
        """
        time, rfu, voltage, current = data
        with open(filepath, 'w') as file_out:
            file_out.write(header)
            file_out.write('time_data,rfu,voltage,current\n')
            for t, r, v, c in zip(time, rfu, voltage, current):
                file_out.write(f"{t},{r},{v},{c}\n")

    @staticmethod
    def get_data(system):
        """
        Retrieves the data from a CE System
        :param system:
        :return:
        """
        detector_data = system.detector.get_data()
        power_data = system.high_voltage.get_data()
        power_time = power_data['time_data']
        detector_time = detector_data['time_data']
        # We need a power data to be as long as the detector data, so we add in one more time_data pair to be sure
        # thus replace the start and stop of the power time to match the detector time if the detector time has
        # more data points
        if power_time[-1] < detector_time[-1]:
            power_time[-1] = detector_time[-1]
        if power_time[0] > detector_time[0]:
            power_time[0] = detector_time[0]

        # We need to interpolate data values from the power supply (Power supply may not be sampled at the same rate)
        if len(power_time) > 0:
            for channel in ['voltage', 'current']:
                if len(power_data[channel])>3:
                    fx = interp1d(power_time, power_data[channel], kind='cubic')
                    power_data[channel] = fx(detector_time)

                else:
                    power_data[channel] = np.pad(power_data[channel], (0, len(detector_time)-len(power_data[channel])),
                                                 'edge')


        return [detector_time, detector_data['rfu'], power_data['voltage'], power_data['current']]
