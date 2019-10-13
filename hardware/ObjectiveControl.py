import threading
from hardware import ArduinoBase
import pickle
import logging
import time

class ObjectiveControl:
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
        #threading.Thread(target=self.go_home()).start()
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
            self.pos = pos*self.inversion
            self.pos = self.pos + self.offset
        #if self.first_read:
            #self.load_history()
        #    self.first_read = False
        #else:
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
            go_to = self.inversion*(set_z-self.offset)
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
        self.pos=0
        self.offset=0
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



class MicroManagerObjective(ObjectiveControl):
    """Class to control Z-stage for capillary/optical train
    If switching controllers modify the function calls here
    Make sure that what you program matches the inputs and outputs
    This is called by the GUI and needs data types to match
    """
    inversion = -1

    def __init__(self, mmc=None, lock=-1):
        """com = Port, lock = threading.Lock, args = [home]
        com should specify the port where resources are located,
        lock is a threading.lock object that will prevent the resource from being
        read/written two at multiple times.
        """
        self.pos = 0
        self.mmc = mmc
        if lock == -1:
            lock = threading.Lock()
        self.lock = lock
        self.open()

        return

    def open(self):
        """User initializes whatever resources are required
         (open ports, create MMC + load config, etc...)
         """
        #Todo
        if self.mmc is None:
            self.mmc = MicroCommunicator.MicroCommunicator()

        self.mmc.open()
        return True

    def read_z(self, *args):
        """ returns float of current position in um
        User requests to get current position of stage, returned in um
        """
        # Lock the resources we are going to use
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
            rsp = str(self.mmc.read_response())
            if rsp != 'Ok':
                logging.warning("Could not set Z")
                return False
        return True

    def set_rel_z(self, rel_z):
        """
        Moves the objective up or down by the amount specified in rel_z
        :param rel_z: float, um
        :return: True/False if succesful
        """
        self.read_z()
        go_to = self.pos + rel_z
        self.set_z(go_to)
        return True

    def stop_z(self):
        """ Stops the objective motor where it is at. """
        self.stop()
        return True

    def stop(self):
        """Stop the Z-stage from moving"""
        self.set_rel_z(0)
        return True

    def reset(self):
        """Resets the resources for the stage"""
        if self.home:
            self.close()
            return
        self.close()
        self.open()

    def go_home(self):
        """
        Returns the objective to the home (zero) position
        :return:
        """
        with self.lock:
            self.mmc.send_command('obj,set_position,0\n')
            response = str(self.mmc.read_response())
        if response != 'Ok':
            logging.warning("Could not move to 0 um")
        return

    def close(self):
        """Closes the resources for the stage"""
        if self.home:
            return
        self.mmc.close()

