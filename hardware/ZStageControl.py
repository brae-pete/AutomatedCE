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
    from hardware.ScopeControl import PriorController
except ModuleNotFoundError:
    import ArduinoBase
    from ScopeControl import PriorController


try:
    import clr
    import time
    from System import String
    from System import Decimal
    from System.Collections import *

    # Constants
    sys.path.append(r'C:\Program Files\Thorlabs\Kinesis')

    # Add the .net reference and import so python can see it
    clr.AddReference("Thorlabs.MotionControl.Controls")
    import Thorlabs.MotionControl.Controls

    clr.AddReference("Thorlabs.MotionControl.DeviceManagerCLI")
    clr.AddReference("Thorlabs.MotionControl.GenericMotorCLI")
    clr.AddReference("Thorlabs.MotionControl.IntegratedStepperMotorsCLI")
    from Thorlabs.MotionControl.DeviceManagerCLI import *
    from Thorlabs.MotionControl.GenericMotorCLI import *
    from Thorlabs.MotionControl.IntegratedStepperMotorsCLI import *

except Exception as e:
    logging.warning("Could not load thorlabs")

class ZStageControl:
    """Class to control Z-stage for capillary/optical train
    If switching controllers modify the function calls here
    Make sure that what you program matches the inputs and outputs
    This is called by the GUI and needs data types to match
    """
    default_pos = 24.5

    def __init__(self, com="COM3", lock=-1, home=False,invt=1):
        """com = Port, lock = threading.Lock, args = [home]
        com should specify the port where resources are located,
        lock is a threading.lock object that will prevent the resource from being
        read/written two at multiple times.
        """
        self.home = False
        self.com = com
        self.stage = None
        self.pos = 0
        self.invert = invt
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
        pass

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
            self.get_z()
        return self.pos

    def get_z(self):
        return self.pos

    def set_z(self, set_z=0, *args):
        """ set_z (absolute position in mm)
        returns False if unable to set_z, True if command went through
        """

        with self.lock:
            if self.home:
                self.pos = set_z
                return True
        return True

    def set_rel_z(self, set_z=0):
        with self.lock:
            if self.home:
                self.pos = set_z
                return True
        return True

    def set_speed(self, speed):
        """User requests to set speed in mm/s"""
        with self.lock:
            if self.home:
                return

    def set_accel(self, accel):
        with self.lock:
            if self.home:
                return

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

    def jog(self, distance):
        """ Jog move """
        self.set_rel_z(distance)
        return

    def close(self):
        """Closes the resources for the stage"""
        if self.home:
            return

    def go_home(self):
        return

    def wait_for_move(self,clearance=0.0):
        """
        returns the final position of the motor after it has stopped moving.

        :return: current_pos, float in mm of where the stage is at
        """
        prev_pos = self.read_z()
        current_pos = prev_pos + 1
        # Update position while moving
        while np.abs(prev_pos-current_pos) > clearance:
            time.sleep(0.25)
            prev_pos = current_pos
            current_pos = self.read_z()
            print(current_pos)
        return current_pos



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

class ThorLabs(ZStageControl):
    """ Class for controlling a ThorLabs Labjack usingn the Kinesis Library
    You will need to adjust the Kinesis file reference if you installed it outside of the default location

    This uses .NET programming, we load in DLL's using pythonnet package (clr and data types)
    There are more options available to use beyond what has been set here, and you can check the Kinesis documentation
    and examples to see how.
    """
    min_z = 0
    max_z = 50
    offset = 0
    def __init__(self, lock=threading.RLock() , serial =  '49125264'):
        self.lock = lock
        self.inversion = 1
        self.com = "COM3"
        self.pos = 0
        self.serial = serial
        self.lock = lock
        self.first_read = True
        self.open()


    @staticmethod
    def initialize_device(serial):
        """ Loads the thorlabs lab jackD
        Requires to first build a list of devices,
        then create a device using the Labjack serial numbe
        In general, this order cannot be changed
        """
        device_list_result = DeviceManagerCLI.BuildDeviceList()
        device = Thorlabs.MotionControl.IntegratedStepperMotorsCLI.LabJack.CreateLabJack(serial)
        device.Connect(serial)
        device.WaitForSettingsInitialized(5000)
        #motorSettings = device.GetMotorConfiguration()
        # print(motorSettings)
        deviceInfo = device.GetDeviceInfo()
        logging.info(deviceInfo.Name, '  ', deviceInfo.SerialNumber)
        return device

    def open(self):
        """User initializes whatever resources are required
         (open ports, create MMC + load config, etc...)
         """

        self.device = self.initialize_device(self.serial)
        time.sleep(1)
        self.device.LoadMotorConfiguration(self.serial)
        self.settings = self.device.MotorDeviceSettings
        self.device.EnableDevice()
        self.device.StartPolling(250)

        #Set the speed to 5 mm/s
        vel_prms = self.device.GetVelocityParams()
        vel_prms.set_MaxVelocity(Decimal(3.5))
        self.device.SetVelocityParams(vel_prms)



    def  get_z(self, *args):
        """ returns float of current position
        User requests to get current position of stage, returned in mm
        """
        # Lock the resources we are going to use
        pos = float(str(self.device.DevicePosition))
        self.pos =self.inversion *( pos + self.offset)
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
        threading.Thread(target = self.device.Home, args = (60000,)).start()
        #self.device.Home(60000)

    def set_z(self, set_z):
        """ set_z (absolute position in mm)
        returns False if unable to set_z, True if command went through
        """
        if not self.min_z < set_z < self.max_z:
            logging.warning("Z Stage cannot move this far {}".format(set_z))
            return
        else:
            logging.info("{} set z".format(set_z))

        # Check if moving
        status = self.device.get_Status()
        while status.get_IsInMotion():
            time.sleep(0.5)
            status = self.device.get_Status()
        if self.home_check():
            go_to = self.inversion * (set_z - self.offset)
            threading.Thread(target = self.device.MoveTo,args=(Decimal(go_to),60000,)).start()

            #self.device.MoveTo(Decimal(go_to),60000)
        return True

    def home_check(self):
        home = self.device.NeedsHoming
        if home:
            logging.warning("Please Home Z Stage")
            return False
        return True

    def set_rel_z(self, set_z):
        pos = self.get_z()
        go_to =  pos + set_z
        self.set_z(go_to)
        return True

    def jog(self, distance):
        """

        :param distance: float, distance to travel
        :return:
        """

        dist_up = self.inversion*distance
        if dist_up < 0:
            direction = MotorDirection.Backward
        else:
            direction = MotorDirection.Forward
        logging.info("{} ".format(distance))
        distance = Decimal(float(np.abs(distance)))

        status = self.device.get_Status()

        # Try this then maybe timeout reset?

        if status.get_IsInMotion():
            self.device.Stop(1000)
        jog_prms = self.device.GetJogParams()
        if distance != jog_prms.get_StepSize():
            jog_prms.set_StepSize(distance)
            logging.error("{} distance, {} status".format(distance, status.get_IsInMotion()))
            self.device.SetJogParams(jog_prms)

        if self.home_check():
            threading.Thread(target=self.device.MoveJog, args=(direction,60000,)).start()
            #self.device.MoveJog(direction,10000)

    def stop_z(self):
        """ Stops the objective motor where it is at. """
        self.jack.StopImmediate()
        return True

    def stop(self):
        """Stop the Z-stage from moving"""
        self.stop_z()

    def reset(self):
        """Resets the resources for the stage"""
        self.close()
        self.open()

    def close(self):
        """Closes the resources for the stage"""
        self.device.Disconnect()

    @staticmethod
    def dos2unix(in_file, out_file):
        outsize = 0
        with open(in_file, 'rb') as infile:
            content = infile.read()
        with open(out_file, 'wb') as output:
            for line in content.splitlines():
                outsize += len(line) + 1
                output.write(line + '\n'.encode())

    def wai2t_for_move(self, clearance=0.0):
        """
        returns the final position of the motor after it has stopped moving.

        :return: current_pos, float in mm of where the stage is at
        """
        time.sleep(0.25)
        status = self.device.get_Status()

        while status.get_IsInMotion():
            logging.info("Zstage is moving")
            time.sleep(0.1)
            status = self.device.get_Status()

        return self.get_z()


class PowerStep(ZStageControl):
    min_z = 0
    max_z = 26
    offset = 25
    def __init__(self, com = "COM3", arduino = -1, home=False,invt=1, home_dir = False,lock=threading.RLock()):
        self.lock = lock
        self.home = home
        self.inversion = invt
        self.invert = invt
        self.com = com
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
        self.home_dir=home_dir
        self.go_home()


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
            self.arduino.go_home(self.home_dir)
            self.max_z+=25
            self.set_z(50)
            self.wait_for_move()
            self.set_rel_z(0.1)
            self.pos = self.wait_for_move()
            self.max_z-=25
            self.set_z(self.default_pos)

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

        with self.lock:
            go_to = self.inversion*(set_z-self.offset)
            self.arduino.set_outlet_z(go_to)
        return True

    def set_rel_z(self, set_z):
        pos = self.get_z()
        go_to = pos+set_z
        self.set_z(go_to)
        return True

    def set_speed(self, steps_per_sec):
        if self.home:
            return
        with self.lock:
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

def test():
    ctl= PowerStep(com="COM4", invt=-1)
    #ctl.set_z(-2)
    return ctl
if __name__ == "__main__":
    import time
    ctl=test()



