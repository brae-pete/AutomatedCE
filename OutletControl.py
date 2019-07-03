import threading
import ArduinoBase

class OutletControl():
    """Class to control Z-stage for capillary/optical train
    If switching controllers modify the function calls here
    Make sure that what you program matches the inputs and outputs
    This is called by the GUI and needs data types to match
    """

    def __init__(self, com="COM9", arduino=-1, lock=-1, home=True, *args):
        """com = Port, lock = threading.Lock, args = [home]
        com should specify the port where resources are located,
        lock is a threading.lock object that will prevent the resource from being
        read/written two at multiple times.
        """
        self.home = home
        self.com = com
        self.pos = 0
        self.have_arduino = True
        self.arduino = arduino
        if arduino == -1:
            self.check = False
            self.arduino = ArduinoBase.ArduinoBase(self.com, self.home)
        if lock == -1:
            lock = threading.Lock()
        self.lock = lock
        return

    def open(self, *args):
        """User initializes whatever resources are required
         (open ports, create MMC + load config, etc...)
         """
        self.arduino.open()

    def readZ(self, *args):
        """ returns float of current position
        User requests to get current position of stage, returned in mm
        """
        # Lock the resources we are going to use
        with self.lock:
            if self.home:
                if len(args) > 0:
                    self.pos = args[0]
                return self.pos
            self.pos = -self.arduino.read_outlet_z()
        return self.pos

    def setZ(self, setZ, *args):
        """ setZ (absolute position in mm)
        User requests in mmm absolute distance to go
        returns False if unable to setZ, True if command went through
        """
        with self.lock:
            if self.home:
                self.pos = setZ
                return
            self.arduino.set_outlet_z(-setZ)
        return True

    def setSpeed(self, speed, *args):
        """User requests to set speed in mm/s"""
        with self.lock:
            if self.home:
                return
        self.arduino.set_outlet_speed(speed)

    def stop(self):
        """Stop the Z-stage from moving"""
        if self.home:
            return

    def reset(self):
        """Resets the resources for the stage"""
        if self.home:
            self.close()
            return
        self.close()
        self.open()

    def close(self):
        """Closes the resources for the stage"""
        if self.home:
            return
        self.arduino.close()
