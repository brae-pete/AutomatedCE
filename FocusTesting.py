import datetime
import logging
import os
import time

import CESystems
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import animation


class CapillaryFocusAuxillary:
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

    def __init__(self, apparatus):
        self.apparatus = apparatus
        self.df = self._create_dataframe()

    def start_acquisition(self, slide_movement=False, well_num=1):
        new_data = self._record_data(slide_movement)
        self._move_focus(new_data)
        self._save_temp()
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
        numpy_data = np.reshape(np.asarray(new_data),(1,len(self._columns)))
        new_df = pd.DataFrame(data=numpy_data, columns=self._columns)
        self.df = self.df.append(new_df)
        return new_data

    def _create_sample_folder(self):
        sample_time = datetime.datetime.now()
        name = "\\Sample_{}".format(sample_time.strftime("%Y-%m-%d_%H-%M-%S"))
        dir_name = self._focus_dir + name
        os.mkdir(dir_name)
        return dir_name

    def _move_focus(self, new_data):
        """ Moves the objective up and down from the focus position."""
        start_pos = new_data[2]
        save_dir = new_data[4]
        # Move objective up
        self._loop_acquisition(start_pos, save_dir, 1)
        # Move objective down
        self._loop_acquisition(start_pos, save_dir, -1)

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
            self.apparatus.set_objective(move_x + start_pos)
            self.apparatus.objective_control.wait_for_move()
            time.sleep(0.5)
            filename = save_dir + "\\obj_{:+04.0f}.png".format(move_x)
            self.apparatus.image_control.record_recent_image(filename)
            move_x += direction * self._move_function(np.abs(move_x))
        return

    @staticmethod
    def _move_function(x):
        """
        Helps control the spacing around a point of interest, more detail near zero, an less detail farther out.
        :param x: current absolute position from center
        :return y: distance to move
        """

        y = 0.002 * (x ** 2.1) + 0.1 * x + 2
        return y

    def _save_temp(self):
        return

    def save_as(self):
        return

    def _create_dataframe(self):
        df = pd.DataFrame(columns=self._columns)
        return df



def init():
    pass


def animate(i):
    frame = hd.get_image()
    try:
        im.set_data(frame)
    except TypeError:
        logging.warning("Could not load image")
    return im


if __name__ == "__main__":
    hd = CESystems.BarracudaSystem()
    hd.start_system()
    hd.start_feed()
    time.sleep(2)
    hd.home_z()
    hd.home_objective()
    frame = hd.get_image()

    fig = plt.figure()
    im = plt.imshow(frame, cmap='gist_gray')
    anim = animation.FuncAnimation(fig, animate, init_func=init, interval=50)
