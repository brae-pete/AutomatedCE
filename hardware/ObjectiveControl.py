import threading
import sys
import pickle
import logging
import time
import os

try:
    from hardware import ArduinoBase
except ModuleNotFoundError:
    import ArduinoBase

if r"C:\Program Files\Micro-Manager-2.0gamma" not in sys.path:
    sys.path.append(r"C:\Program Files\Micro-Manager-2.0gamma")
prev_dir = os.getcwd()
os.chdir(r"C:\Program Files\Micro-Manager-2.0gamma")
MMCOREPY_FATAL = False
os.chdir(prev_dir)
try:
    import MMCorePy
except ImportError:
    logging.error('Can not import MMCorePy.')
    if MMCOREPY_FATAL:
        sys.exit()
else:
    logging.info('MMCorePy successfully imported.')


# Locate the directory of config files
cwd = os.getcwd()
contents = os.listdir(cwd)
SETUP = 'ostrich'
if "config" in contents:
    CONFIG_FOLDER = os.path.join(cwd, "config")

elif "CEGraphic" in contents:
    contents = os.listdir(os.path.join(cwd, "CEGraphic"))
    if "config" in contents:
        os.chdir(os.path.join(cwd, "CEGraphic"))
        CONFIG_FOLDER = os.path.join(os.getcwd(), "config")
    else:
        CONFIG_FOLDER = os.getcwd()
elif "XYControl.py" in contents or "OstrichTesting.py" in contents:
    CONFIG_FOLDER=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))
else:  # fixme prompt for program folder if it is not the cwd or within the cwd.
    CONFIG_FOLDER = os.getcwd()

class ObjectiveControl:
    """Class to control Z-stage for capillary/optical train
       If switching controllers modify the function calls here
       Make sure that what you program matches the inputs and outputs
       This is called by the GUI and needs data types to match
       """
    inversion = 1

    def __init__(self, com="COM9", arduino=-1, lock=-1, home=True):
        """com = Port, lock = threading.Lock, args = [home]
        com should specify the port where resources are located,
        lock is a threading.lock object that will prevent the resource from being
        read/written two at multiple times.
        """

        pass

    def open(self):
        """User initializes whatever resources are required
         (open ports, create MMC + load config, etc...)
         """
        pass

    def read_z(self, *args):
        """ returns float of current position
        User requests to get current position of stage, returned in mm
        """
        pass


    def save_history(self):
        pass

    def load_history(self):
        pass

    def set_origin(self):
        """ sets the current position to home or zero pos, resets the offset """
        pass

    def set_z(self, set_z):
        """ set_z (absolute position in mm)
        returns False if unable to set_z, True if command went through
        """
        pass

    def set_rel_z(self, set_z):
        pass

    def stop_z(self):
        pass

    def stop(self):
        """Stop the Z-stage from moving"""
        pass

    def reset(self):
        """Resets the resources for the stage"""
        pass

    def go_home(self):
        pass


    def close(self):
        """Closes the resources for the stage"""
        pass

    def wait_for_move(self):
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


class OstrichObjective(ObjectiveControl):
    """Class to control Z-stage for capillary/optical train
       If switching controllers modify the function calls here
       Make sure that what you program matches the inputs and outputs
       This is called by the GUI and needs data types to match
       """
    inversion = 1

    def __init__(self, config_file='NikonTi.cfg', lock=threading.Lock(), home=True):
        """com = Port, lock = threading.Lock, args = [home]
        com should specify the port where resources are located,
        lock is a threading.lock object that will prevent the resource from being
        read/written two at multiple times.
        """
        self.home=home
        if self.home==True:
            config_file = 'DemoCam.cfg'
        self.config_file = os.path.join(CONFIG_FOLDER, config_file)

        self.lock=lock

        self.mmc = MMCorePy.CMMCore()
        self.open()
        self.go_home()
        pass

    def open(self):
        """User initializes whatever resources are required
         (open ports, create MMC + load config, etc...)
         """
        with self.lock:
            self.mmc.loadSystemConfiguration(self.config_file)
            self.objectiveID = self.mmc.getFocusDevice()

    def read_z(self, *args):
        """ returns float of current position
        User requests to get current position of stage, returned in um
        """
        with self.lock:
            self.pos=self.mmc.getPosition()
        return self.pos

    def save_history(self):
        pass

    def load_history(self):
        pass

    def set_origin(self):
        """ sets the current position to home or zero pos, resets the offset """
        logging.warning("TIZ Drive cannot set origin, only return to zero")
        return True

    def set_z(self, set_z):
        """ set_z (absolute position in um)
        returns False if unable to set_z, True if command went through
        """
        with self.lock:
            self.mmc.setPosition(set_z)
        return True

    def set_rel_z(self, set_z):
        """ set relative position (in um) """
        z = self.read_z()
        self.set_z(z+set_z)
        return

    def stop_z(self):
        self.mmc.stop()

    def stop(self):
        """Stop the Z-stage from moving"""
        self.mmc.stop()

    def reset(self):
        """Resets the resources for the stage"""
        self.mmc.reset()

    def go_home(self):
        self.mmc.setPosition(0)

    def close(self):
        """Closes the resources for the stage"""
        self.mmc.unloadAllDevices()

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

class BarracudaObjective(ObjectiveControl):
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
        threading.Thread(target=self.go_home()).start()
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

if __name__=="__main__":
    obj = OstrichObjective(home=False, lock = threading.Lock())
