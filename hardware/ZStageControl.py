import serial
import threading
import logging
import sys
import os
import pickle
import numpy as np
import time
try:
    from hardware import ArduinoBase
except ModuleNotFoundError:
    import ArduinoBase

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

    def __init__(self, com="COM3", lock=-1, home=False):
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
            lock = threading.RLock()
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
        self.stage = PowerStep(self.lock, self.com)

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

    def set_z(self, set_z=0, *args):
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

            set_z = set_z
            self.stage.set_z(set_z)

        return True

    def set_rel_z(self, set_z=0):
        with self.lock:
            if self.home:
                self.pos = set_z
                return True

            # check if stage is busy
            response = self.stage.get_z()
            if response == type(str):
                return False
            self.pos = response

            self.stage.set_z(self.pos + set_z)
        return True

    def set_speed(self, speed):
        """User requests to set speed in mm/s"""
        with self.lock:
            if self.home:
                return
            self.stage.set_speed(speed)

    def set_accel(self, accel):
        with self.lock:
            if self.home:
                return

            self.stage.set_accel(accel)
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
        self.stage.close()

    def go_home(self):
        self.stage.go_home()

    def wait_for_move(self):
        self.stage.wait_for_move()


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



class PowerStep:
    min_z = 0
    max_z = 24.5
    def __init__(self, lock, com = "COM3", arduino = -1, home=False, ):
        self.lock = lock
        self.home = home
        self.inversion = 1
        self.offset = 0
        self.com = "COM3"
        self.pos = 0
        self.have_arduino = True
        self.arduino = arduino
        if arduino == -1:
            self.check = False
            self.arduino = ArduinoBase.ArduinoBase(self.com,self.home)
        if lock == -1:
            lock = threading.RLock()
        self.lock = lock
        self.first_read = True
        self.go_home()

    def wait_for_move(self,clearance=0.0):
        """
        returns the final position of the motor after it has stopped moving.

        :return: current_pos, float in mm of where the stage is at
        """
        prev_pos = self.get_z()
        current_pos = prev_pos + 1
        # Update position while moving
        while np.abs(prev_pos-current_pos) > clearance:
            time.sleep(0.1)
            prev_pos = current_pos
            current_pos = self.get_z()
        return current_pos


    def open(self):
        """User initializes whatever resources are required
         (open ports, create MMC + load config, etc...)
         """
        self.arduino.open()

    def get_z(self, *args):
        """ returns float of current position
        User requests to get current position of stage, returned in mm
        """
        # Lock the resources we are going to use
        with self.lock:
            if self.home:
                if len(args) > 0:
                    self.pos = args[0]
                return self.pos
            pos, check_offset = self.arduino.read_outlet_z()
            if check_offset:
                self.offset = self.pos
            self.pos = pos*self.inversion
            self.pos = self.pos + self.offset
            """
            if self.first_read:
                self.load_history()
                self.first_read = False
            else:
                self.save_history()
        """
        return self.pos

    def save_history(self):
        with open("StageHistory.p", "wb") as fout:
            data = {'pos': self.pos, 'offset': self.offset}
            pickle.dump(data, fout)

    def load_history(self):
        try:
            self.dos2unix("StageHistory.p", "StageHistory.p")
            with open("StageHistory.p", "rb") as fin:
                logging.info(fin)
                data = pickle.load(fin)
                logging.info(data)
                # adjust for the new offset, and add the old offset that  may be present
                self.offset = (data['pos'] - self.pos) + self.offset
                self.pos = data['pos']
        except IOError:
            logging.warning("No Stage History found")

    def go_home(self):
        """ Moves up or down until the stage hits the mechanical stop that specifices the 25 mm mark

         """
        with self.lock:
            if self.home:
                self.pos = 0
                return
            self.arduino.go_home()
            self.wait_for_move()
            self.arduino.go_home()
            self.pos = self.wait_for_move()
            self.offset = 0
            logging.info("{} is pos 0, {} is stage 0".format(self.pos, self.arduino.pos))
            self.set_z(0.1)
            cz=self.wait_for_move()
            logging.info("{} is current z".format(cz))
            self.save_history()

    def set_z(self, set_z):
        """ set_z (absolute position in mm)
        returns False if unable to set_z, True if command went through
        """

        if self.home:
            self.pos = set_z
            return
        if not self.min_z < set_z < self.max_z:
            logging.warning("Z Stage cannot move this far {}".format(set_z))
            return
        else:
            logging.info("{} set z".format(set_z))


        go_to = self.inversion*(set_z-self.offset)
        self.arduino.set_outlet_z(go_to)
        return True

    def set_rel_z(self, set_z):
        pos = self.read_z()
        if self.home:
            self.pos = set_z
            return
        go_to = set_z - pos
        self.set_z(go_to)
        return True

    def set_speed(self, steps_per_sec):
        if self.home:
            return

        self.arduino.set_outlet_speed(steps_per_sec)
        return True
    def set_accel(self, steps_per_sec2):
        if self.home:
            return
        self.arduino.set_stepper_accel(steps_per_sec2)
        return True

    def stop_z(self):
        """ Stops the objective motor where it is at. """

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

    @staticmethod
    def dos2unix(in_file, out_file):
        outsize = 0
        with open(in_file, 'rb') as infile:
            content = infile.read()
            print(content)
        with open(out_file, 'wb') as output:
            for line in content.splitlines():
                outsize += len(line) + 1
                output.write(line + '\n'.encode())

        print("Done. Saved %s bytes." % (len(content) - outsize))

def threading_test():
    # import threading
    # lock = threading.Lock()
    print("We are Locked")
    # ser2 = ZStageControl()

if __name__ == "__main__":
    import time
    s = ZStageControl()




