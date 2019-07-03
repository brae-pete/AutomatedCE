import serial
import threading
import logging


class ZStageControl():
    """Class to control Z-stage for capillary/optical train
    If switching controllers modify the function calls here
    Make sure that what you program matches the inputs and outputs
    This is called by the GUI and needs data types to match
    """

    def __init__(self, com="COM4", lock=-1, home=False, *args):
        """com = Port, lock = threading.Lock, args = [home]
        com should specify the port where resources are located,
        lock is a threading.lock object that will prevent the resource from being
        read/written two at multiple times.
        """
        self.home = False
        self.com = com
        self.stage = None
        self.pos = 0
        if lock == -1:
            lock = threading.Lock()
        self.lock = lock
        if home:
            self.home = home
            return

        self.open()

    def open(self, *args):
        """User initializes whatever resources are required
         (open ports, create MMC + load config, etc...)

         """
        if len(args) > 0:
            self.com = args[0]
            return
        self.stage = OpticsFocusZStage(self.com)

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

            z = self.stage.getZ()
        if type(z) == str:
            # Dont update position if the controller was busy
            pass
        else:
            self.pos = z

        return self.pos

    def setZ(self, setZ, *args):
        """ setZ (absolute position in mm)
        User requests in mmm absolute distance to go
        returns False if unable to setZ, True if command went through
        """
        print(args, setZ)
        with self.lock:
            print("Hey  There")
            if self.home:
                print("Hi")
                self.pos = setZ
                return True

            # check if stage is busy
            response = self.stage.getZ()
            if response == type(str):
                return False
            logging.info(type(setZ))
            logging.info(type(self.pos))
            setZ = setZ - self.pos
            self.stage.goZ(setZ)
        return True

    def setSpeed(self, speed, *args):
        """User requests to set speed in mm/s"""
        with self.lock:
            if self.home:
                return
            self.stage.setSpeed(speed)

    def stop(self):
        """Stop the Z-stage from moving"""
        if self.home:
            return
        self.stage.stop()

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
        self.stage.serial.close()

    def goHome(self):
        self.stage.goHome()


class OpticsFocusZStage():
    """Helper class for the OpticsFocus Z stage
    Called by the ZStageControl Class
    Don't change this unless you are changing how you talk to the OpticsFocusZ Stage
    IF switching controllers, create a new class or modify the ZStageControl above
    This is only called by the ZStageControl Class
    """

    def __init__(self, port):
        self.serial = serial.Serial()
        self.serial.timeout = 0.8
        self.serial.port = port
        self.serial.open()

    def mm2Steps(self, position):
        ""
        pulse_eq = 1.5 / (360 / 0.9 * 2)
        return int(round(position / pulse_eq))

    def steps2mm(self, steps):
        ""
        pulseEq = 1.5 / (360 / 0.9 * 2)
        return steps * pulseEq

    def getZ(self):
        self.serial.write("?X\r")
        response = self.serial.readlines()
        #logging.info("Z_STAGE RESPONSE {}".format(response))
        try:
            response = response[-1]
        except IndexError:
            return self.pos

        response = response.strip('\n')
        response = response.split('\r')[-1]

        if response == "ERR5":
            logging.info("Z Stage cant go lower")
            self.reset()
            return "Err5"
        elif response == "ERR2":
            self.reset()
            return "Err2"
        elif response == "ERR1":
            logging.info("Time out to Z Stage")
            self.reset()
            return "Err1"
        elif response == "":
            return self.pos
        else:
            #logging.info(response)
            try:
                position = self.steps2mm(int(response[1:]))
                self.pos = position
            #logging.info("{} POSITION {} RESPONSE".format(position,response[1:]))
            except ValueError:
                position = self.pos
        return position

    def goZ(self, mm_to_travel):
        steps = self.mm2Steps(mm_to_travel)
        self.serial.write("X{:+d}\r".format(steps))

    def goHome(self):
        self.serial.write("HX0\r")

    def stop(self):
        self.serial.write("S\r")

    def setSpeed(self, mm_per_sec):
        if mm_per_sec > 10:
            mm_per_sec = 255
        elif mm_per_sec < 0:
            mm_per_sec = 0
        speed = int(round(mm_per_sec / 10 * 255))
        self.serial.write("V{:d}\r".format(speed))
        return

    def reset(self):
        self.serial.close()
        self.serial.open()
        self.serial.write("?R\r")
        response = self.serial.readlines()
        logging.info(response)
def threadingTest():
    import threading
    lock = threading.Lock()
    print("We are Locked")
    ser2 = ZStageControl()
