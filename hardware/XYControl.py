import sys
import os
import logging
import threading
import random

if r"C:\Program Files\Micro-Manager-2.0gamma" not in sys.path:
    sys.path.append(r"C:\Program Files\Micro-Manager-2.0gamma")
prev_dir = os.getcwd()
os.chdir(r"C:\Program Files\Micro-Manager-2.0gamma")

MMCOREPY_FATAL = False

try:
    import MMCorePy
except ImportError:
    logging.error('Can not import MMCorePy.')
    if MMCOREPY_FATAL:
        sys.exit()
else:
    logging.info('MMCorePy successfully imported.')

os.chdir(prev_dir)

# Locate the directory of config files
cwd = os.getcwd()
contents = os.listdir(cwd)

if "config" in contents:
    CONFIG_FOLDER = os.path.join(cwd, "config")
elif "CEGraphic" in contents:
    contents = os.listdir(os.path.join(cwd, "CEGraphic"))
    if "config" in contents:
        os.chdir(os.path.join(cwd, "CEGraphic"))
        CONFIG_FOLDER = os.path.join(os.getcwd(), "config")
    else:
        CONFIG_FOLDER = os.getcwd()
else:  # fixme prompt for program folder if it is not the cwd or within the cwd.
    CONFIG_FOLDER = os.getcwd()

CONFIG_FILE = os.path.join(CONFIG_FOLDER, "PriorXY.cfg")

logging.basicConfig(level=logging.DEBUG)

total_width = 160
total_height = 110
travel_width = 112
travel_height = 70


class XYControl:
    """ Basic XY Control class. If you switch hardware so that it no longer uses MMC. You only need
    to maintain the outputs for each method."""
    scale = 1
    x_inversion = 1
    y_inversion = 1

    def __init__(self, home=True, lock=-1, stage='XYStage', config_file = "PriorXY.cfg", loaded=False):
        logging.info("{} IS LOCK {} IS HOME".format(lock, home))

        if lock == -1:
            lock = threading.Lock()
        self.lock = lock
        self.home = home
        self.stageID = stage
        self.config_file = os.path.join(CONFIG_FOLDER, config_file)
        self.position = [0, 0]

        if not home:
            self.mmc = MMCorePy.CMMCore()
            self.load_config()

    def load_config(self):
        """ starts MMC object, [config file] [home]
        config file is mmc config file created by micro manager for the stage
        home is a flag that allows the core functionality of XY control to be tested
        without connecting to MMC. Good for testing GUI/debugging at home"""
        if self.home:
            logging.info("Non MMC XY Control-Testing Only")
            return self.home
        logging.info("{} is lock".format(type(self.lock)))
        with self.lock:
            self.mmc.loadSystemConfiguration(self.config_file)
            self.stageID = self.mmc.getXYStageDevice()

    def read_xy(self):
        """ Reads the current XY position of the stage, sets XYControl.position and returns list [X, Y]  """
        if self.home:
            return [float(random.randint(0, 110000)), float(random.randint(-6000, 6000))]

        # Get XY from Stage
        with self.lock:
            pos = [0, 0]

            # For some reason the getXYPosition() in mmc isn't working.
            pos[0] = self.mmc.getXPosition(self.stageID)
            pos[1] = self.mmc.getYPosition(self.stageID)

            pos = [x / self.scale for x in pos]
            pos[0] *= self.x_inversion
            pos[1] *= self.y_inversion

        return pos

    def set_xy(self, xy):
        """Moves stage to position defined by pos (x,y). Returns nothing
        pos must be defined in microns """
        if self.home:
            self.position = xy
            return
        pos = xy[:]
        pos[0] *= self.x_inversion
        pos[1] *= self.y_inversion
        pos = [x * self.scale for x in pos]
        logging.info("{} is XY MOVE".format(pos))

        with self.lock:
            self.mmc.setXYPosition(self.stageID, pos[0], pos[1])

    def set_x(self, x):
        if self.home:
            self.position = [0, 0]
            return
        x = x*self.scale
        pos = self.read_xy()
        with self.lock:
            self.mmc.setXYPosition(self.stageID, x, pos[1]*self.scale)

    def set_y(self, y):
        if self.home:
            self.position = [0, 0]
            return
        y = y*self.scale
        pos = self.read_xy()
        with self.lock:
            self.mmc.setXYPosition(self.stageID, pos[0]*self.scale, y)

    def set_rel_xy(self, xy):
        # setRelativeXYPosition()
        if self.home:
            self.position = xy
            return
        pos = xy[:]
        pos[0] *= self.x_inversion
        pos[1] *= self.y_inversion
        pos = [x * self.scale for x in pos]

        with self.lock:
            self.mmc.setRelativeXYPosition(self.stageID, pos[0], pos[1])

    def set_rel_x(self, x):
        if self.home:
            self.position = [0, 0]
            return
        x = x * self.scale
        with self.lock:
            self.mmc.setRelativeXYPosition(self.stageID, x, 0)

    def set_rel_y(self, y):
        if self.home:
            self.position = [0, 0]
            return
        y = y * self.scale
        with self.lock:
            self.mmc.setRelativeXYPosition(self.stageID, 0, y)

    def set_origin(self):
        """Redefines current position as Origin. Calls XYControl.read_xy after reset"""
        logging.info("Home is {}".format(self.home))
        if self.home:
            logging.info("Set Origin as 0,0")
            self.position = [0, 0]
            self.read_xy()
            return
        with self.lock:
            self.mmc.setOriginXY(self.stageID)
        self.read_xy()

    def origin(self):
        logging.info("Returning to origin.")
        if self.home:
            logging.info("At Home")
            return
        with self.lock:
            self.mmc.home(self.stageID)

    def close(self):
        """Releases any communication ports that may be used"""
        if self.home:
            logging.info('XY Stage Released')
            return
        with self.lock:
            self.mmc.reset()

    def reset(self):
        """ Resets the device in case of a communication error elsewhere """
        self.close()
        if self.home:
            logging.info("Device Re-Loaded")
            return
        with self.lock:
            self.mmc.loadSystemConfiguration(CONFIG_FILE)

    def stop(self):
        if self.home:
            logging.info("Stopping Device")
            return
        with self.lock:
            self.mmc.stop(self.stageID)


if __name__ == '__main__':
    xyc = XYControl()
