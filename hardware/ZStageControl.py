import serial
import threading
import logging
import sys
import os

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

class ZStageControl:
    """Class to control Z-stage for capillary/optical train
    If switching controllers modify the function calls here
    Make sure that what you program matches the inputs and outputs
    This is called by the GUI and needs data types to match
    """

    def __init__(self, com="COM4", lock=-1, home=False):
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

    def read_z(self, *args):
        """ returns float of current position
        User requests to get current position of stage, returned in mm
        """
        # Lock the resources we are going to use
        with self.lock:
            if self.home:
                if len(args) > 0:
                    self.pos = args[0]
                return self.pos

            z = self.stage.get_z()
        if type(z) == str:
            # Don't update position if the controller was busy
            pass
        else:
            self.pos = z

        return self.pos

    def set_z(self, set_z, *args):
        """ set_z (absolute position in mm)
        returns False if unable to set_z, True if command went through
        """

        with self.lock:
            if self.home:
                self.pos = set_z
                return True

            # Get Current position and check if stage is busy/moving
            response = self.stage.get_z()
            if response == type(str):
                return False
            else:
                self.pos = response

            #Convert from absolute to relative position (optics_focus cant handle absolute)
            set_z = set_z - self.pos
            self.stage.go_z(set_z)
        return True

    def set_rel_z(self, set_z):
        with self.lock:
            if self.home:
                self.pos = set_z
                return True

            # check if stage is busy
            response = self.stage.get_z()
            if response == type(str):
                return False

            self.stage.go_z(set_z)
        return True

    def set_speed(self, speed):
        """User requests to set speed in mm/s"""
        with self.lock:
            if self.home:
                return
            self.stage.set_speed(speed)

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

    def go_home(self):
        self.stage.go_home()


class OpticsFocusZStage:
    """Helper class for the OpticsFocus Z stage
    Called by the ZStageControl Class
    Don't change this unless you are changing how you talk to the OpticsFocusZ Stage
    IF switching controllers, create a new class or modify the ZStageControl above
    This is only called by the ZStageControl Class
    """
    max_steps = 13000
    min_steps = 5
    def __init__(self, port):
        self.serial = serial.Serial()
        self.serial.timeout = 0.8
        self.serial.port = port
        self.pos = None

        self.serial.open()

    @staticmethod
    def mm_to_steps(position):
        pulse_eq = 1.5 / (360 / 0.9 * 2)
        return int(round(position / pulse_eq))

    @ staticmethod
    def steps_to_mm(steps):
        pulse_eq = 1.5 / (360 / 0.9 * 2)
        return steps * pulse_eq

    def get_z(self):
        self.serial.write("?X\r".encode())
        response = self.serial.readlines()
        # logging.info("Z_STAGE RESPONSE {}".format(response))
        try:
            response = response[-1]
        except IndexError:
            return self.pos

        response = response.strip('\n'.encode())
        response = response.split('\r'.encode())[-1]

        if response == b"ERR5":
            logging.info("Z Stage cant go lower")
            self.reset()
            return "Err5"
        elif response == b"ERR2":
            self.reset()
            return "Err2"
        elif response == b"ERR1":
            logging.info("Time out to Z Stage")
            self.reset()
            return "Err1"
        elif response == b"":
            return self.pos
        else:
            # logging.info(response)
            try:
                position = self.steps_to_mm(int(response[1:]))
                self.pos = position
                # logging.info("{} POSITION {} RESPONSE".format(position, response[1:]))
            except ValueError:
                position = self.pos
        return position

    def go_z(self, mm_to_travel):
        #This helps keep the stage in ran
        steps = self.mm_to_steps(mm_to_travel)
        pos_steps = self.mm_to_steps(self.pos)

        if pos_steps+steps > self.max_steps:
            steps = self.max_steps - pos_steps
        elif pos_steps+steps < self.min_steps:
            steps = self.min_steps - pos_steps
        logging.info("{:+d} STteps to move ,{} pos_steps, {} Pos, {} mm_to_travel".format(steps,pos_steps, self.pos, mm_to_travel))
        self.serial.write("X{:+d}\r".format(steps).encode())

    def go_home(self):
        self.serial.write("HX0\r".encode())

    def stop(self):
        self.serial.write("S\r".encode())

    def set_speed(self, mm_per_sec):
        if mm_per_sec > 10:
            mm_per_sec = 255
        elif mm_per_sec < 0:
            mm_per_sec = 0
        speed = int(round(mm_per_sec / 10 * 255))
        self.serial.write("V{:d}\r".format(speed).encode())
        return

    def reset(self):
        self.serial.close()
        self.serial.open()
        self.serial.write("?R\r".encode())
        response = self.serial.readlines()
        logging.info(response)


class NikonZStage:
    def __init__(self, lock, stage=None, config_file=None, home=False, loaded=False):
        self.lock = lock
        self.stage_id = stage
        self.config_file = config_file
        self.home = home

        self.mmc = MMCorePy.CMMCore()
        if not home and not loaded:
            self.load_config()

    def load_config(self):
        if not self.home:
            with self.lock:
                self.mmc.loadSystemConfiguration(self.config_file)
                self.stage_id = self.mmc.getZStageDevice()

    def close(self):
        if not self.home:
            with self.lock:
                self.mmc.reset()

    def reset(self):
        self.close()
        if not self.home:
            with self.lock:
                self.mmc.loadSystemConfiguration(self.config_file)

    def set_z(self, z):
        if not self.home:
            with self.lock:
                self.mmc.setZPosition(self.stage_id, z)

    def set_rel_z(self, rel_z):
        if not self.home:
            with self.lock:
                self.mmc.setRelativeZPosition(self.stage_id, rel_z)

    def read_z(self):
        if not self.home:
            with self.lock:
                pos = self.mmc.getZPosition(self.stage_id)
                return pos

    def stop(self):
        if not self.home:
            with self.lock:
                self.mmc.stop(self.stage_id)


def threading_test():
    # import threading
    # lock = threading.Lock()
    print("We are Locked")
    # ser2 = ZStageControl()
