import sys
import os
import logging
import threading
import random
import serial
from numpy import abs
import time
import sys
try:

    from hardware import MicroControlClient
    from hardware.ScopeControl import PriorController
except ModuleNotFoundError:
    sys.path.append(os.path.relpath('..'))
    from hardware import MicroControlClient
    from hardware.ScopeControl import PriorController
# Locate the directory of config files
cwd = os.getcwd()
contents = os.listdir(cwd)

if "config" in contents:
    CONFIG_FOLDER = os.path.join(cwd, "config")
elif "XYControl.py" in contents:
    CONFIG_FOLDER = os.path.relpath('../config')
elif "CEGraphic" in contents:
    contents = os.listdir(os.path.join(cwd, "CEGraphic"))
    if "config" in contents:
        os.chdir(os.path.join(cwd, "CEGraphic"))
        CONFIG_FOLDER = os.path.join(os.getcwd(), "config")
    else:
        CONFIG_FOLDER = os.getcwd()
else:  # fixme prompt for program folder if it is not the cwd or within the cwd.
    CONFIG_FOLDER = os.getcwd()


logging.basicConfig(level=logging.DEBUG)

total_width = 160
total_height = 110
travel_width = 112
travel_height = 70


class XYControl:
    """ Basic XY stage Control class. All future classes must define these methods to work with CESystems"""
    scale = 1  # scalar value to multiply to get microns
    x_inversion = 1  # -1 to invert the x-axis
    y_inversion = 1  # -1 to invert the y-axis

    def __init__(self):
        self.pos = [0,0]
        self._raw_pos=[0,0]

    def open(self):
        """ Opens all the hardware resources that will be needed (ie open serial ports, micromanager config, etc..,.

         """
        return True

    def read_xy(self):
        """ Reads the current XY position of the stage, and returns list [X, Y] in microns """

        um = [x / self.scale for x in self._raw_pos]
        um[0] *= self.x_inversion
        um[1] *= self.y_inversion
        self.pos = um
        return um

    def set_xy(self, xy):
        """Moves stage to position defined by pos (x,y). Returns nothing
        pos must be defined in microns """

        xy[0]*= self.x_inversion
        xy[1]*= self.y_inversion
        xy = [x * self.scale for x in xy]
        self._raw_pos = xy
        return True

    def set_x(self, x):
        """ Sets absolute position for X in microngs"""
        xy = self.read_xy()
        xy[0]=x
        return self.set_xy(xy)

    def set_y(self, y):
        """ Sts absolute position for Y in microns"""
        xy = self.read_xy()
        xy[1] = y
        return self.set_xy(xy)

    def set_rel_xy(self, xy):
        """ Moves x and y by values specified in list 'xy' given in microns"""
        xy[0] *= self.x_inversion
        xy[1] *= self.y_inversion
        xy = [x * self.scale for x in xy]
        um = self.read_xy()
        self.set_xy([xy[0]+um[0], xy[1]+um[1]])
        return True

    def set_rel_x(self, x):
        """ Moves x axis by value specified by x in microns"""
        return self.set_rel_xy([x, 0])

    def set_rel_y(self, y):
        """ Moves y axis b value specified by y in microns"""
        return self.set_rel_xy([y, 0])

    def set_origin(self):
        """Redefines current position as Origin. """
        self._raw_pos=[0,0]
        return True

    def origin(self):
        """ Moves to the origin position"""
        return self.set_xy([0, 0])

    def close(self):
        """Releases any communication ports that may be used"""
        pass

    def reset(self):
        """ Resets the device in case of a communication error elsewhere """
        self.close()
        self.open()

    def stop(self):
        """ Stops movement of the stage """
        xy = self.read_xy()
        self.set_xy(xy)

    def wait_for_move(self,tolerance=100):
        """ Waits for the stage to stop moving"""
        time.sleep(0.15)
        prev_pos = self.read_xy()
        current_pos = [prev_pos[0]+1,prev_pos[1]]
        # Update position while moving
        while abs(prev_pos[0]-current_pos[0])>tolerance or abs(prev_pos[1]- current_pos[1])>tolerance:
            time.sleep(0.05)
            prev_pos = current_pos
            current_pos = self.read_xy()

        return current_pos


class MicroControl(XYControl):
    """ Subclass of the XYControl class. Uses the MicroCommunicator to send commands to a python 2
    process.
    """
    device_name = 'TIXYDrive'  # This does not update and will need to change for different stage

    def __init__(self, mmc=None, config_file='NikonEclipseTi-NoLight.cfg', lock = threading.Lock()):
        """
        :param mmc: micromanager communicator object
        """
        self.mmc = mmc
        self.lock = lock
        self.config = os.path.join(CONFIG_FOLDER, config_file)
        self._open_client()
        self.open()
        return

    def _open_client(self):
        """ Creates a new Micromanager communicator if mmc is None. Runs the MMC.open command. MMC.open
        checks if it is already running and opens the client if it is not.
         """
        if self.mmc is None:
            self.mmc = MicroControlClient.MicroControlClient()
        self.mmc.open()

    def _close_client(self):
        """ Closes the client resources, called when program exits"""
        self.mmc.close()

    def open(self):
        """ Opens the stage and Nikon Resources"""
        # Load the Config
        with self.lock:
            self.mmc.send_command('core,load_config,{}'.format(self.config))
            response = self.mmc.read_response()
        msg = "Could not open XYStage"
        state = self.mmc.ok_check(response, msg)
        return state

    def read_xy(self):
        """ Reads the current XY position of the stage, and returns list [X, Y] in microns """
        with self.lock:
            self.mmc.send_command('xy,get_position\n')
            um = self.mmc.read_response()
        if type(um) is not list:
            return None
        if type(um[0]) is not float and type(um[0]) is not int:
            logging.warning("Did not read XY Stage position: {}".format(um))
        um = [x / self.scale for x in um]
        um[0] *= self.x_inversion
        um[1] *= self.y_inversion
        self.pos = um
        return um

    def set_xy(self, xy):
        """Moves stage to position defined by pos (x,y). Returns nothing
        pos must be defined in microns """

        xy[0] *= self.x_inversion
        xy[1] *= self.y_inversion
        xy = [x * self.scale for x in xy]
        with self.lock:
            self.mmc.send_command('xy,set_position,{},{},{}'.format(self.device_name, xy[0], xy[1]))
            response = self.mmc.read_response()
        msg = "Did not set XY Stage"
        return self.mmc.ok_check(response, msg)

    def set_rel_xy(self, xy):
        """ Moves x and y by values specified in list 'xy' given in microns"""

        xy[0] *= self.x_inversion
        xy[1] *= self.y_inversion
        xy = [x * self.scale for x in xy]
        with self.lock:
            self.mmc.send_command('xy,rel_position,{},{},{}\n'.format(self.device_name, xy[0], xy[1]))
            response = self.mmc.read_response()
        msg = "Did not set XY Stage"
        return self.mmc.ok_check(response, msg)

    def set_origin(self):
        """Redefines current position as Origin in micromanager software """
        with self.lock:
            self.mmc.send_command('xy,set_origin,{}\n'.format(self.device_name))
            response = self.mmc.read_response()
        msg = "Could not set XY Software Origin"
        return self.mmc.ok_check(response, msg)


class PriorControl(XYControl, PriorController):
    """ Basic XY Control class. If you switch hardware so that it no longer uses MMC. You only need
    to maintain the outputs for each method.

    This uses the proscan controller III from prior.
    see commands at https://www.prior.com/wp-content/uploads/2017/06/ProScanIII-v1.12.pdf

    """
    scale = 1
    x_inversion = 1
    y_inversion = 1

    def __init__(self, com="COM5", lock=threading.RLock()):
        self.lock = lock
        self.port = com
        self.open()

    def _read_lines(self):
        """
        Reads entire buffer and returns response as a list
        :return:
        """
        lines = []
        while self.ser.in_waiting > 0:
            lines.append(self._read_line())
        return lines

    def _read_line(self):
        """
        reads one line, using \r as the terminator
        returns decoded response as a string
        :return: string response
        """
        return self.ser.read_until('\r'.encode()).decode()

    def read_xy(self):
        """ Reads the current XY position of the stage, sets XYControl.position and returns list [X, Y]  """
        # Get XY from Stage
        with self.lock:
            pos = [0, 0]
            self.ser.write("P \r".encode())
            resp = self._read_line().split(',')
            pos[0] = eval(resp[0])
            pos[1] = eval(resp[1])
            pos = [x / self.scale for x in pos]
            pos[0] *= self.x_inversion
            pos[1] *= self.y_inversion

        return pos

    def set_xy(self, xy):
        """Moves stage to position defined by pos (x,y). Returns nothing
        pos must be defined in microns """
        pos = xy[:]
        pos[0] *= self.x_inversion
        pos[1] *= self.y_inversion
        pos = [x * self.scale for x in pos]
        logging.info("{} is XY MOVE".format(pos))

        with self.lock:
            self.ser.write("G {},{} \r".format(pos[0], pos[1]).encode())
            self._read_line()

    def set_x(self, x):
        x = x * self.scale * self.x_inversion
        with self.lock:
            self.ser.write("GX {} \r".format(x).encode())
            self._read_line()

    def set_y(self, y):
        y = y * self.scale * self.y_inversion
        with self.lock:
            self.ser.write("GY {} \r".format(y).encode())
            self._read_line()

    def set_rel_xy(self, xy):
        pos = xy[:]
        pos[0] *= self.x_inversion
        pos[1] *= self.y_inversion
        pos = [x * self.scale for x in pos]

        with self.lock:
            self.ser.write("GR {},{} \r".format(pos[0], pos[1]).encode())
            self._read_line()

    def set_rel_x(self, x):
        self.set_rel_xy([x, 0])

    def set_rel_y(self, y):
        self.set_rel_xy([0, y])

    def set_origin(self):
        """Redefines current position as 0,0. Calls XYControl.read_xy after reset"""
        with self.lock:
            self.ser.write("Z \r".encode())
            self._read_line()
        self.read_xy()

    def origin(self):
        " Return to 0,0 "
        self.set_rel_xy((-160000, +160000))
        self.set_origin()


    def stop(self):
        """
        Stops the stage immediately, can lose position
        :return:
        """
        with self.lock:
            self.ser.write('K\r'.encode())
            self._read_line()


def main():
    mc = MicroControl()
    return mc


if __name__ == '__main__':
    mc = main()
