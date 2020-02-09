import threading
from hardware import ArduinoBase
import pickle
import logging
import time
from hardware import MicroControlClient
from hardware.ScopeControl import PriorController
import os

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
else:
    CONFIG_FOLDER = os.getcwd()


class ObjectiveControl:
    """Class to control Z-stage for capillary/optical train
       If switching controllers modify the function calls here
       Make sure that what you program matches the inputs and outputs
       This is called by the GUI and needs data types to match
       """
    inversion = -1
    pos = 0
    offset = 0

    def __init__(self):
        self.lock = threading.Lock()

    def open(self):
        """User initializes whatever resources are required
         (open ports, create MMC + load config, etc...)
         """
        pass

    def read_z(self, *args):
        """ returns float of current position
        User requests to get current position of stage, returned in um
        """
        # Lock the resources we are going to use
        return self.pos

    def save_history(self):
        with open("ObjectiveHistory.p", "wb") as fout:
            data = {'pos': self.pos, 'offset': self.offset}
            pickle.dump(data, fout)

    def load_history(self):
        try:
            self.dos2unix("ObjectiveHistory.p", "ObjectiveHistory.p")
            with open("ObjectiveHistory.p", "rb") as fin:
                logging.info(fin)
                data = pickle.load(fin)
                logging.info(data)
                # adjust for the new offset, and add the old offset that  may be present
                self.offset = (data['pos'] - self.pos) + self.offset
                self.pos = data['pos']
        except IOError:
            logging.warning("No Objective History found")

    def set_origin(self):
        """ sets the current position to home or zero pos, resets the offset """
        return

    def set_z(self, set_z):
        """ set_z (absolute position in um)
        returns False if unable to set_z, True if command went through
        """
        with self.lock:
            self.pos = set_z
        return

    def set_rel_z(self, set_z):
        """ Sets moves the objective up or down by the amount set_z """
        pos = self.read_z()
        go_to = pos + set_z
        self.set_z(go_to)
        return True

    def stop_z(self):
        """ Stops the objective motor where it is at. """
        self.stop()

    def stop(self):
        """Stop the Z-stage from moving"""
        self.set_rel_z(0)

    def reset(self):
        """Resets the resources for the stage"""
        self.close()
        self.open()

    def go_home(self):
        """ Moves to zero position"""
        self.set_z(0)
        return

    def close(self):
        """Closes the resources for the stage"""
        pass

    def wait_for_move(self):
        """
        returns the final position of the motor after it has stopped moving.

        :return: current_pos, float in mm of where the stage is at
        """
        prev_pos = self.read_z()
        current_pos = prev_pos + 1
        # Update position while moving
        while prev_pos != current_pos:
            time.sleep(0.25)
            prev_pos = current_pos
            current_pos = self.read_z()
        return current_pos

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


class PriorControl(ObjectiveControl, PriorController):
    def __init__(self, com="COM9", lock=threading.RLock(), home=True):
        """com = Port, lock = threading.Lock, args = [home]
        com should specify the port where resources are located,
        lock is a threading.lock object that will prevent the resource from being
        read/written two at multiple times.
        """
        self.home = home
        self.port = com
        self.pos = 0
        self.offset = 0
        self.open()
        self.lock = lock
        self.first_read = True
        return

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

            self.ser.write("PZ \r".encode())
            pos = self._read_line()
        self.pos = pos * self.inversion
        return self.pos

    def set_origin(self):
        """ sets the current position to home or zero pos, resets the offset """
        with self.lock:
            if self.home:
                self.pos = 0
                return
            self.arduino.set_objective_origin()
            self.pos = 0
            self.offset = 0

    def set_z(self, set_z):
        """ set_z (absolute position in mm)
        returns False if unable to set_z, True if command went through
        """
        with self.lock:
            if self.home:
                self.pos = set_z
                return
            go_to = self.inversion * set_z
            self.ser.write("GZ {} \r".format(go_to).encode())
            self._read_line()
        return True

    def stop_z(self):
        """ Stops the objective motor where it is at. """
        with self.lock:
            if self.home:
                return True
            self.ser.write('D 0 \r'.encode())
            self._read_line()
        return True

    def stop(self):
        """Stop the Z-stage from moving"""
        if self.home:
            return

    def go_home(self):
        if self.home:
            self.pos=0
            return
        with self.lock:
            self.ser.write('GZ 0 \r'.encode())
            self._read_line()
        return


class ArduinoControl(ObjectiveControl):
    """Class to control Z-stage for capillary/optical train
    If switching controllers modify the function calls here
    Make sure that what you program matches the inputs and outputs
    This is called by the GUI and needs data types to match
    """
    inversion = -1

    def __init__(self, com="COM9", arduino=-1, lock=-1, home=True):
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
        time.sleep(0.1)
        # threading.Thread(target=self.go_home()).start()
        return

    def open(self):
        """User initializes whatever resources are required
         (open ports, create MMC + load config, etc...)
         """
        self.arduino.open()

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
            pos, check_offset = self.arduino.read_objective_z()
            if check_offset:
                self.offset = self.pos
            self.pos = pos * self.inversion
            self.pos = self.pos + self.offset
        # if self.first_read:
        # self.load_history()
        #    self.first_read = False
        # else:
        #    self.save_history()
        return self.pos

    def save_history(self):
        with open("ObjectiveHistory.p", "wb") as fout:
            data = {'pos': self.pos, 'offset': self.offset}
            pickle.dump(data, fout)

    def load_history(self):
        try:
            self.dos2unix("ObjectiveHistory.p", "ObjectiveHistory.p")
            with open("ObjectiveHistory.p", "rb") as fin:
                logging.info(fin)
                data = pickle.load(fin)
                logging.info(data)
                # adjust for the new offset, and add the old offset that  may be present
                self.offset = (data['pos'] - self.pos) + self.offset
                self.pos = data['pos']
        except IOError:
            logging.warning("No Objective History found")

    def set_origin(self):
        """ sets the current position to home or zero pos, resets the offset """
        with self.lock:
            if self.home:
                self.pos = 0
                return
            self.arduino.set_objective_origin()
            self.pos = 0
            self.offset = 0

    def set_z(self, set_z):
        """ set_z (absolute position in mm)
        returns False if unable to set_z, True if command went through
        """
        with self.lock:
            if self.home:
                self.pos = set_z
                return
            go_to = self.inversion * (set_z - self.offset)
            self.arduino.set_objective_z(go_to)
        return True

    def set_rel_z(self, set_z):
        pos = self.read_z()

        with self.lock:
            if self.home:
                self.pos = set_z
                return
            go_to = self.inversion * (set_z - self.offset + pos)
            self.arduino.set_objective_z(go_to)
        return True

    def stop_z(self):
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

    def go_home(self):
        if self.home:
            return
        self.arduino.go_home_objective()
        self.wait_for_move()
        self.arduino.go_home_objective()
        self.wait_for_move()
        self.set_origin()
        self.pos = 0
        self.offset = 0
        time.sleep(1)
        self.set_z(5);
        self.wait_for_move()
        self.read_z()

        return

    def close(self):
        """Closes the resources for the stage"""
        if self.home:
            return
        self.arduino.close()

    def wait_for_move(self):
        """
        returns the final position of the motor after it has stopped moving.

        :return: current_pos, float in mm of where the stage is at
        """
        prev_pos = self.read_z()
        current_pos = prev_pos + 1
        # Update position while moving
        while prev_pos != current_pos:
            time.sleep(0.1)
            prev_pos = current_pos
            current_pos = self.read_z()
        return current_pos


class MicroControl(ObjectiveControl):
    """Class to control Z-stage for capillary/optical train
    If switching controllers modify the function calls here
    Make sure that what you program matches the inputs and outputs
    This is called by the GUI and needs data types to match
    """
    inversion = -1

    def __init__(self, mmc=None, port = 5511, config_file='PIckleNuts-NoLight.cfg', lock=threading.Lock()):
        """com = Port, lock = threading.Lock, args = [home]
        com should specify the port where resources are located,
        lock is a threading.lock object that will prevent the resource from being
        read/written two at multiple times.
        """
        self.pos = 0
        self.lock = lock

        if mmc is None:
            self.config = os.path.join(CONFIG_FOLDER, config_file)
            print("OBjective opening:{}".format(mmc))
            self._open_client(port)
            self.open()
        self.mmc = mmc

        return

    def _open_client(self,port):
        """ Creates a new Micromanager communicator if mmc is None. Runs the MMC.open command. MMC.open
        checks if it is already running and opens the client if it is not.
         """
        if self.mmc is None:
            self.mmc = MicroControlClient.MicroControlClient(port)
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
            msg = "Could not open Objective"
            state = self.mmc.ok_check(response, msg)
        return state

    def read_z(self, *args):
        """ returns float of current position in um
        User requests to get current position of stage, returned in um
        """
        with self.lock:
            self.mmc.send_command('obj,get_position\n')
            um = self.mmc.read_response()
        if type(um) is not float and type(um) is not int:
            logging.warning("Did not read objective position")
        else:
            self.pos = um
        return self.pos

    def set_z(self, set_z):
        """ set_z (absolute position in mm)
        returns False if unable to set_z, True if command went through
        """
        with self.lock:
            self.mmc.send_command('obj,set_position,{}\n'.format(set_z))
            rsp = self.mmc.read_response()
        msg = "Could not Set Z"
        return self.mmc.ok_check(rsp, msg)

    def go_home(self):
        """
        Returns the objective to the home (zero) position
        :return:
        """
        with self.lock:
            self.mmc.send_command('obj,set_position,0\n')
            response = self.mmc.read_response()
        msg = "Could not set Objective to 0 um"
        return self.mmc.ok_check(response, msg)


def main():
    oc = MicroControl()
    return oc


