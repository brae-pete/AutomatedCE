import MMCorePy
import logging
import threading
import random

logging.basicConfig(level=logging.DEBUG)
logging.debug("This will be logged")

total_width = 160
total_height = 110
travel_width = 112
travel_height = 70

class XYControl:
    """ Basic XY Control class. If you switch hardware so that it no longer uses MMC. You only need
    to maintain the outputs for each method."""
    scale = 1000
    x_inversion = 1
    y_inversion = -1

    def __init__(self,parent = None,  home=True, lock=-1, *args):
        logging.info("{} IS LOCK {} IS HOME".format(lock, home))
        #Properties
        if lock == -1:
            lock = threading.Lock()
        self.lock = lock
        self.mmc = MMCorePy.CMMCore()
        self.home = home
        self.stageID = 'XYStage'
        self.configFile = r'C:\Users\Barracuda\KivyBarracuda\ConfigFiles\PriorXY.cfg'
        self.position = [0, 0]
        #Run Config
        self.loadConfig()

    def loadConfig(self, *args):
        """ starts MMC object, [config file] [home]
        config file is mmc config file created by micro manager for the stage
        home is a flag that allows the core functionality of XY control to be tested
        without connecting to MMC. Good for testing GUI/debugging at home"""
        if self.home:
            logging.info("Non MMC XY Control-Testing Only")
            return self.home
        logging.info("{} is lock".format(type(self.lock)))
        with self.lock:
            self.mmc.loadSystemConfiguration(self.configFile)
            self.stageID = self.mmc.getXYStageDevice()

    def readXY(self,*args):
        """ Reads the current XY position of the stage, sets XYControl.position and returns list [X, Y]  """
        if self.home:
            return [float(random.randint(0, 110000)), float(random.randint(0, 60000))]

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

    def setXY(self, xy):
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

    def setX(self,x):
        if self.home:
            self.position = [0,0]
            return
        x = x*self.scale
        pos = self.readXY()
        with self.lock:
            self.mmc.setXYPosition(self.stageID, x, pos[1]*self.scale)

    def setY(self,y):
        if self.home:
            self.position = [0,0]
            return
        y=y*self.scale
        pos = self.readXY()
        with self.lock:
            self.mmc.setXYPosition(self.stageID,pos[0]*self.scale,y)

    def setOrigin(self):
        """Redefines current position as Origin. Calls XYControl.readXY after reset"""
        print("Home is ", self.home)
        if self.home:
            print("Set Origin as 0,0")
            self.position = [0, 0]
            self.readXY()
            return
        with self.lock:
            self.mmc.setOriginXY(self.stageID)
        self.readXY()

    def close(self):
        """Releases any communication ports that may be used"""
        if self.home:
            print('XY Stage Released')
            return
        with self.lock:
            self.mmc.reset()

    def reset(self):
        """ Resets the device in case of a communication error elsewhere """
        self.close()
        if self.home:
            print("Device Re-Loaded")
            return
        with self.lock:
            self.mmc.loadSystemConfiguration(self.configFile)

if __name__ == '__main__':
    xyc = XYControl()

