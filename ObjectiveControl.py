import threading
import ArduinoBase
import pickle
import logging

class ObjectiveControl():
    """Class to control Z-stage for capillary/optical train
    If switching controllers modify the function calls here
    Make sure that what you program matches the inputs and outputs
    This is called by the GUI and needs data types to match
    """
    inversion = -1

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
        self.offset = 0
        if arduino == -1:
            self.check = False
            self.arduino = ArduinoBase.ArduinoBase(self.com, self.home)
        if lock == -1:
            lock = threading.Lock()
        self.lock = lock
        self.first_read = True
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
            pos, check_offset = self.arduino.read_objective_z()
            if check_offset:
                self.offset = self.pos
            self.pos = pos*self.inversion
            self.pos = self.pos + self.offset
        if self.first_read:
            self.loadHistory()
            self.first_read=False
        else:
            self.saveHistory()
        return self.pos

    def saveHistory(self,*args):
        fout= open("ObjectiveHistory.p","w")
        data={'pos':self.pos, 'offset':self.offset}
        pickle.dump(data,fout)
        fout.close()

    def loadHistory(self,*args):
        try:
            fin= open("ObjectiveHistory.p","r")
            data = pickle.load(fin)
            fin.close()
            # adjust for the new offset, and add the old offset that  may be present
            self.offset = (data['pos'] - self.pos) + self.offset
            self.pos = data['pos']
        except IOError:
            logging.warning("No Objective History found")

    def setOrigin(self,*args):
        """ sets the current position to home or zero pos, resets the offset """
        with self.lock:
            if self.home:
                self.pos = 0
                return
            self.arduino.set_objective_origin()
            self.pos = 0
            self.offset = 0

    def setZ(self, setZ, *args):
        """ setZ (absolute position in mm)
        User requests in mmm absolute distance to go
        returns False if unable to setZ, True if command went through
        """
        with self.lock:
            if self.home:
                self.pos = setZ
                return
            go_to = self.inversion*(setZ-self.offset)
            self.arduino.set_objective_z(go_to)
            logging.warning("Setz:{} offset:{}  pos:{}".format(setZ,self.offset,self.pos))
            logging.warning(self.inversion*(setZ-self.offset))

        return True

    def stopZ(self):
        """ Stops the objective motor where it is at. """
        with self.lock:
            if self.home:
                return True
        self.arduino.stop_objective_z()
        return True

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
