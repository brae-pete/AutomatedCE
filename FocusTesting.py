import datetime
import logging
import os
import time

import CESystems
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import Detection
from matplotlib import animation


class ZStackData:
    """
    Class for controlling the Z acquisition of images.
    Stores data into a data frame according to the columns

    Methods that would probably need to be changed for additional auxiliary function are:
    _record_data() -> depending on the information you want to capture. default is xy, obj_z, cap_z,
    img_folder, slide_movment, well_num.

    _move_hardware()-> should be connected to the hardware that is moving (either objective or capillary)

    Fields that may need to be changed are:
    temp_file -> CSV filename from the database


    """
    _columns = ['x', 'y', 'objective_z', 'capillary_z', 'img_folder', 'slide_movement',
                'well_num']
    _focus_dir = os.getcwd() + "\\focus_data"
    _temp_file = _focus_dir + "\\cap_data.csv"
    file_prefix = "Sample"
    def __init__(self, apparatus):
        self.apparatus = apparatus
        self.df = self._create_dataframe()
        self._load_temp()

    def start_acquisition(self, slide_movement=False, well_num=1):
        #self.apparatus.image_control.stop_video_feed()
        new_data = self._record_data(slide_movement)
        self._move_focus(new_data)
        self._save_temp()
        #self.apparatus.image_control.start_video_feed()
        return

    def _record_data(self, slide_movment, well_num=1):
        """
        Records data at the start of the acquisition. The capillary and objective should be in focus with each other.
        The objective should be 100 microns above the focal plane of the glass.

        :param slide_movment: Bool. True signifies slide was adjusted or moved between the last
         acquisition and now
        :param well_num: Which of the sample wells this image was taken from
        :return:
        """
        # Record new data of the in focus region
        new_data = [None] * len(self._columns)
        new_data[0:2] = self.apparatus.get_xy()
        new_data[2] = self.apparatus.get_objective()
        new_data[3] = self.apparatus.get_z()
        new_data[4] = self._create_sample_folder()
        new_data[5] = slide_movment
        new_data[6] = well_num

        # Create new Data frame and add it to our dataset
        numpy_data = np.reshape(np.asarray(new_data), (1, len(self._columns)))
        new_df = pd.DataFrame(data=numpy_data, columns=self._columns)
        self.df = self.df.append(new_df)
        return new_data

    def _create_sample_folder(self):
        sample_time = datetime.datetime.now()
        name = "\\{}_{}".format(self.file_prefix, sample_time.strftime("%Y-%m-%d_%H-%M-%S"))
        dir_name = self._focus_dir + name
        os.mkdir(dir_name)
        return dir_name

    def _move_focus(self, new_data):
        """ Moves the objective up and down from the focus position."""
        start_pos = new_data[2]
        save_dir = new_data[4]
        logging.info("Saving to {}".format(save_dir))
        # Move objective up
        self._loop_acquisition(start_pos, save_dir, 1)
        self._move_hardware(start_pos)
        time.sleep(1.5)
        # Move objective down
        self._loop_acquisition(start_pos, save_dir, -1)

    def _move_hardware(self, position):
        """ Moves the objective to the absolute position specified by position"""
        self.apparatus.set_objective(position)
        #self.apparatus.objective_control.wait_for_move()
        time.sleep(0.25)
    def _loop_acquisition(self, start_pos, save_dir, direction=1):
        """
        Moves the objective up and down from the focal plane. Acquires images according to the funciton
        set in the _move_function method

        :param start_pos: float, starting position of the objective
        :param save_dir: string, location to save the images
        :param direction: int, scalar to indicate up or down (+1 = up, -1 = down)
        :return:
        """
        move_x = 0
        while 100 > move_x > -100:
            self._move_hardware(move_x + start_pos)
            time.sleep(0.25)
            self.apparatus.get_image()
            filename = save_dir + "\\z_stack_{:+04.0f}.tiff".format(move_x)
            self.apparatus.save_raw_image(filename)
            move_x += direction * self._move_function(np.abs(move_x))
        self._move_hardware(start_pos)
        return

    @staticmethod
    def _move_function(x):
        """
        Helps control the spacing around a point of interest, more detail near zero, an less detail farther out.
        :param x: current absolute position from center
        :return y: distance to move
        """

        """y = 0.002 * (x ** 2.1) + 0.1 * x + 2"""

        if x < 10:
            y = 1
        elif x <25:
            y = 3
        elif x < 50:
            y = 5
        elif x < 100:
            y= 10

        return y

    def _save_temp(self):
        self.df.to_csv(self._temp_file)
        return

    def _load_temp(self):
        try:
            self.df = pd.read_csv(self._temp_file)
        except FileNotFoundError:
            logging.info("Creating new file...")
        return

    def save_as(self):
        return

    def _create_dataframe(self):
        df = pd.DataFrame(columns=self._columns)
        return df



class CapillaryFocusAuxillary(ZStackData):
    """
    Collects data on the relationship between the capillary position and objective position for
    points around the sample well. This is an auxillary class that should only be relavent for
    the barracuda system.

    Uses CE system class to control the barracuda apparatus. In particular the objective, xy stage,
    z stage, and camera are all used to gather data.

    Data is store in a Pandas dataframe and exported to a csv file.
    The data columns include:

    sample_num, x     , y    , objective_z, capillary_z, img_folder, slide_movement, well_num,
    int       | float| float  | float     |  float     |  string   |   bool        |    int   |
    """
    _columns = ['x', 'y', 'objective_z', 'capillary_z', 'img_folder', 'slide_movement',
                'well_num']
    _focus_dir = os.getcwd() + "\\focus_data"
    _temp_file = _focus_dir + "\\cap_data.csv"
    file_prefix = "Capillary"

    def _record_data(self, slide_movment, well_num=1):
        """
        Records data at the start of the acquisition. The capillary and objective should be in focus with each other.
        The objective should be 100 microns above the focal plane of the glass.

        :param slide_movment: Bool. True signifies slide was adjusted or moved between the last
         acquisition and now
        :param well_num: Which of the sample wells this image was taken from
        :return:
        """
        # Record new data of the in focus region
        new_data = [None] * len(self._columns)
        new_data[0:2] = self.apparatus.get_xy()
        new_data[2] = self.apparatus.get_objective()
        new_data[3] = self.apparatus.get_z()
        new_data[4] = self._create_sample_folder()
        new_data[5] = slide_movment
        new_data[6] = well_num

        # Create new Data frame and add it to our dataset
        numpy_data = np.reshape(np.asarray(new_data), (1, len(self._columns)))
        new_df = pd.DataFrame(data=numpy_data, columns=self._columns)
        self.df = self.df.append(new_df)
        return new_data

class CellFocusAuxillary(ZStackData):
    """
    Collects images at different focal planes of the cell.

    Records position of the xy, objective_height, img_folder into a pandas dataframe (exported to csv).

    Images are organized into folders based off of the time of acquisition.
    """

    _focus_dir = os.getcwd() + "\\focus_data"
    _temp_file =_focus_dir + "\\cell_data.csv"
    file_prefix = "Cell"


def get_images(fc, im):

    while True:
        fc.quickcheck()
        time.sleep(1.5)
        im.start_acquisition()

if __name__ == "__main__":
    CENTER = [3730, -1957]

    hd = CESystems.NikonEclipseTi()
    hd.start_system()
    det = Detection.CellDetector(hd)
    mov = Detection.Mover(CENTER)
    fc = Detection.FocusGetter(det, mov)