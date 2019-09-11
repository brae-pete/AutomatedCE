# Standard library modules
import threading
import logging
import time
import ctypes

# Custom Hardware Modules  fixme do a dynamic import so only those modules necessary are imported.
from hardware import DAQControl
from hardware import ImageControl
from hardware import OutletControl
from hardware import XYControl
from hardware import ZStageControl
from hardware import ObjectiveControl
from hardware import LaserControl
from hardware import PressureControl

# Network Module
import CENetworks

HOME = False


class BaseSystem:
    """Interface controllers will interact with to control the different hardware systems."""
    system_id = None

    # Supported hardware checks for the program controllers
    hasCameraControl = False
    hasXYControl = False
    hasInletControl = False
    hasOutletControl = False
    hasVoltageControl = False
    hasPressureControl = False
    hasObjectiveControl = False
    hasLaserControl = False

    def __init__(self):
        self.laser_max_time = None

    def calibrate_system(self, permissions_gui):
        """Calibrates the system."""
        logging.error('calibrate_system not implemented in hardware class.')

    def start_system(self):
        """Puts the system into its functional state."""
        logging.error('start_system not implemented in hardware class.')

    def close_system(self):
        """Takes system out of its functional state."""
        logging.error('close_system not implemented in hardware class.')

    def close_xy(self):
        """Removes immediate functionality of XY stage."""
        logging.error('close_xy not implemented in hardware class.')

    def set_xy(self, xy=None, rel_xy=None):
        """Sets the position of the XY Stage. 'xy' is absolute, 'rel_xy' is relative to current."""
        logging.error('set_xy not implemented in hardware class.')

    def get_xy(self):
        """Gets the current position of the XY stage."""
        logging.error('get_xy not implemented in hardware class.')

    def stop_xy(self):
        """Stops current movement of the XY stage."""
        logging.error('stop_xy not implemented in hardware class.')

    def set_xy_home(self):
        """Sets the current position of XY stage as home. Return False if device has no 'home' capability."""
        logging.error('set_xy_home not implemented in hardware class.')

    def home_xy(self):
        """Goes to current position marked as home. Return False if device has no 'home' capability."""
        logging.error('home_xy not implemented in hardware class.')

    def close_z(self):
        """Removes immediate functionality of Z stage/motor."""
        logging.error('close_z not implemented in hardware class.')

    def set_z(self, z=None, rel_z=None):
        """Sets the position of the Z stage/motor. 'z' is absolute, 'rel_z' is relative to current."""
        logging.error('set_z not implemented in hardware class.')

    def get_z(self):
        """Gets the current position of the Z stage/motor."""
        logging.error('get_z not implemented in hardware class.')

    def stop_z(self):
        """Stops current movement of the Z stage/motor."""
        logging.error('stop_z not implemented in hardware class.')

    def set_z_home(self):
        """Sets the current position of the Z stage/motor as home. Return False if device has no 'home' capability."""
        logging.error('set_z_home not implemented in hardware class.')

    def home_z(self):
        """Goes to current position marked as home. Return False if device has no 'home' capability."""
        logging.error('home_z not implemented in hardware class.')

    def wait_z(self):
        """ Waits until the z-stage has finished its move before releasing the lock"""
        logging.error("wait_z not implemented in hardware class")

    def close_outlet(self):
        """Removes immediate functionality of the outlet stage/motor."""
        logging.error('close_outlet not implemented in hardware class.')

    def set_outlet(self, h=None, rel_h=None):
        """Sets the position of the outlet stage/motor. 'h' is absolute, 'rel_h' is relative to current."""
        logging.error('set_outlet not implemented in hardware class.')

    def get_outlet(self):
        """Gets the current position of the outlet stage/motor."""
        logging.error('get_outlet not implemented in hardware class.')

    def stop_outlet(self):
        """Stops current movement of the outlet stage/motor."""
        logging.error('stop_outlet not implemented in hardware class.')

    def set_outlet_home(self):
        """Sets the current position of the outlet stage/motor as home. Return False if device is not capable."""
        logging.error('set_outlet_home not implemented in hardware class.')

    def home_outlet(self):
        """Goes to the current position marked as home. Return False if device has no 'home' capability."""
        logging.error('home_outlet not implemented in hardware class.')

    def close_objective(self):
        """Removes immediate functionality of the objective stage/motor."""
        logging.error('close_objective not implemented in hardware class.')

    def set_objective(self, h=None, rel_h=None):
        """Sets the position of the objective stage/motor. 'h' is absolute, 'rel_h' is relative to current."""
        logging.error('set_objective not implemented in hardware class.')

    def get_objective(self):
        """Gets the current position of the objective stage/motor."""
        logging.error('get_objective not implemented in hardware class.')

    def stop_objective(self):
        """Stops the current movement of the objective stage/motor."""
        logging.error('stop_objective not implemented in hardware class.')

    def set_objective_home(self):
        """Sets the current position of the objective stage/motor as home. Return False if device is not capable."""
        logging.error('set_objective_home not implemented in hardware class.')

    def home_objective(self):
        """Goes to the current position marked as home. Return False if device has no 'home' capability."""
        logging.error('home_objective not implemented in hardware class.')

    def close_voltage(self):
        """Removes immediate functionality of the voltage source."""
        logging.error('close_voltage not implemented in hardware class.')

    def set_voltage(self, v=None):
        """Sets the current voltage of the voltage source."""
        logging.error('set_voltage not implemented in hardware class.')

    def get_voltage(self):
        """Gets the current voltage of the voltage source."""
        logging.error('get_voltage not implemented in hardware class.')

    def get_voltage_data(self):
        """Gets a list of the voltages over time."""
        logging.error('get_voltage_data not implemented in hardware class.')

    def get_current_data(self):
        """Gets a list of the current over time."""
        logging.error('get_current_data not implemented in hardware class.')

    def get_rfu_data(self):
        """Gets a list of the RFU over time."""
        logging.error('get_rfu_data not implemented in hardware class.')

    def close_image(self):
        """Removes the immediate functionality of the camera."""
        logging.error('close_image not implemented in hardware class.')

    def start_feed(self):
        """Sets camera to start gathering images. Does not return images."""
        logging.error('start_feed not implemented in hardware class.')

    def stop_feed(self):
        """Stops camera from gathering images."""
        # Only fill out stop_feed if you can fill out start_feed.
        logging.error('stop_feed not implemented in hardware class.')

    def get_image(self):
        """Returns the most recent image from the camera."""
        logging.error('get_image not implemented in hardware class.')

    def set_laser_parameters(self, pfn=None, att=None, energy=None, mode=None, burst=None):
        """Sets the parameters of the laser device."""
        logging.error('set_laser_parameters not implemented in hardware class.')

    def laser_standby(self):
        """Puts laser in a standby 'fire-ready' mode."""
        logging.error('laser_standby not implemented in hardware class.')

    def laser_fire(self):
        """Fires the laser."""
        logging.error('laser_fire not implemented in hardware class.')

    def laser_stop(self):
        """Stops current firing of the laser."""
        logging.error('laser_stop not implemented in hardware class.')

    def laser_close(self):
        """Removes immediate functionality of the laser."""
        logging.error('laser_close not implemented in hardware class.')

    def laser_check(self):
        """Logs status of laser system."""
        logging.error('laser_check not implemented in hardware class.')

    def pressure_close(self):
        """Removes immediate functionality of the pressure system."""
        logging.error('pressure_close not implemented in hardware class.')

    def pressure_rinse_start(self):
        """Starts rinsing pressure.."""
        logging.error('pressure_rinse_start not implemented in hardware class.')

    def pressure_rinse_stop(self):
        """Stops rinsing pressure."""
        logging.error('pressure_rinse_stop not implemented in hardware class.')

    def pressure_valve_open(self):
        """Opens pressure valve."""
        logging.error('pressure_valve_open not implemented in hardware class.')

    def pressure_valve_close(self):
        """Closes pressure valve."""
        logging.error('pressure_valve_close not implemented in hardware class.')


class BarracudaSystem(BaseSystem):
    system_id = 'BARRACUDA'
    _z_stage_com = "COM4"
    _outlet_com = "COM7"
    _objective_com = "COM8"
    _laser_com = "COM6"
    _pressure_com = "COM7"
    _daq_dev = "/Dev1/"
    _daq_current_readout = "ai2"
    _daq_voltage_readout = "ai1"
    _daq_voltage_control = 'ao1'
    _daq_rfu = "ai3"

    _z_stage_lock = threading.RLock() # Same thread can access the lock at multiple points, but not multiple threads
    _outlet_lock = threading.Lock()
    _objective_lock = threading.Lock()
    _xy_stage_lock = threading.Lock()
    _pressure_lock = threading.Lock()
    _camera_lock = threading.Lock()
    _laser_lock = threading.Lock()
    _laser_poll_flag = threading.Event()
    _laser_rem_time = 0

    image_size = (512, 384)
    objective_focus = 0
    xy_stage_size = [112792, 64340]  # Rough size in mm
    xy_stage_upper_left = [0, 0]  # Reading on stage controller when all the way to left and up (towards wall)
    xy_stage_inversion = [-1, -1]

    _focus_network = CENetworks.BarracudaFocusClassifier()
    _find_network = CENetworks.BarracudaCellDetector()

    def __init__(self):
        super(BarracudaSystem, self).__init__()
        self.laser_max_time = 600

        self.hasCameraControl = True
        self.hasInletControl = True
        self.hasLaserControl = True
        self.hasObjectiveControl = True
        self.hasOutletControl = True
        self.hasVoltageControl = True
        self.hasPressureControl = True
        self.hasXYControl = True

    def _start_daq(self):
        self.daq_board_control.max_time = 600000
        self.daq_board_control.start_read_task()

    def _poll_laser(self, start_time):
        while True:
            if self._laser_poll_flag.is_set():
                self._laser_rem_time = self.laser_max_time - (time.time() - start_time)
                if self._laser_rem_time > 0:
                    self.laser_control.poll_status()
                    time.sleep(1)
                else:
                    self._laser_poll_flag.clear()
            else:
                logging.info('{:.0f}s have passed. turning off laser.'.format(self.laser_max_time))
                self.laser_close()
                self._laser_rem_time = 0
                return True

    def calibrate_system(self, permissions_gui):
        """Calibrates the system."""
        pass

    def start_system(self):
        self.z_stage_control = ZStageControl.ZStageControl(com=self._z_stage_com, lock=self._z_stage_lock, home=HOME)
        self.outlet_control = OutletControl.OutletControl(com=self._outlet_com, lock=self._outlet_lock, home=HOME)
        self.objective_control = ObjectiveControl.ObjectiveControl(com=self._objective_com, lock=self._objective_lock, home=HOME)
        self.image_control = ImageControl.ImageControl(home=HOME)
        self.xy_stage_control = XYControl.XYControl(lock=self._xy_stage_lock, stage='XYStage', config_file='PriorXY.cfg', home=HOME)
        self.daq_board_control = DAQControl.DAQBoard(dev=self._daq_dev, voltage_read=self._daq_voltage_readout,
                                                     current_read=self._daq_current_readout, rfu_read=self._daq_rfu,
                                                     voltage_control=self._daq_voltage_control)
        #
        self.laser_control = LaserControl.Laser(com=self._laser_com, lock=self._laser_lock, home=HOME)
        self.pressure_control = PressureControl.PressureControl(com=self._pressure_com, lock=self._pressure_lock, arduino=self.outlet_control.arduino, home=HOME)

        self._start_daq()
        pass

    def close_system(self):
        self.close_image()
        self.close_objective()
        self.close_outlet()
        self.close_voltage()
        self.close_xy()
        self.close_z()
        return True

    def prepare_networks(self):
        self._focus_network.prepare_model()
        self._find_network.prepare_model()

    def get_focus(self, image=None):
        return self._focus_network.get_focus(image)

    def get_cells(self, image=None):
        return self._find_network.get_cells(image)

    def get_network_status(self):
        return self._focus_network.loaded and self._find_network.loaded

    def record_image(self, filename):
        with self._camera_lock:
            self.image_control.record_recent_image(filename)

    def get_image(self):
        with self._camera_lock:
            image = self.image_control.get_recent_image(size=self.image_size)

            if image is None:
                return None
            if not HOME:

                self.image_control.save_image(image, "recentImg.png")

        return image

    def close_image(self):
        self.image_control.close()
        return True

    def start_feed(self):
        self.image_control.start_video_feed()
        return True

    def stop_feed(self):
        self.image_control.stop_video_feed()
        return True

    def close_xy(self):
        self.xy_stage_control.close()
        return True

    def set_xy(self, xy=None, rel_xy=None):
        """Move the XY Stage"""
        if xy:
            self.xy_stage_control.set_xy(xy)
        elif rel_xy:
            self.xy_stage_control.set_rel_xy(rel_xy)

        return True

    def get_xy(self):
        return self.xy_stage_control.read_xy()

    def stop_xy(self):
        self.xy_stage_control.stop()
        return True

    def set_xy_home(self):
        """Sets the current position of XY stage as home. Return False if device has no 'home' capability."""
        self.xy_stage_control.set_origin()
        return True

    def home_xy(self):
        """Goes to current position marked as home. Return False if device has no 'home' capability."""
        self.xy_stage_control.origin()
        return True

    def close_z(self):
        self.z_stage_control.close()
        return True

    def set_z(self, z=None, rel_z=None):
        if z:
            self.z_stage_control.set_z(z)
            return True

        elif rel_z:
            self.z_stage_control.set_rel_z(rel_z)
            return True

        return False

    def get_z(self):
        return self.z_stage_control.read_z()

    def stop_z(self):
        self.z_stage_control.stop()
        return True

    def set_z_home(self):
        """Sets the current position of the Z stage as home. Return False if device has no 'home' capability."""
        return False

    def wait_z(self):
        self.z_stage_control.wait_for_move()

    def home_z(self):
        """Goes to current position marked as home. Return False if device has no 'home' capability."""
        self.z_stage_control.go_home()
        return True

    def close_outlet(self):
        self.outlet_control.close()
        return True

    def set_outlet(self, h=None, rel_h=None):
        if h:
            self.outlet_control.set_z(h)
            return True

        elif rel_h:
            self.outlet_control.set_rel_z(rel_h)
            return True

        return False

    def get_outlet(self):
        return self.outlet_control.read_z()

    def stop_outlet(self):
        self.outlet_control.stop()
        return True

    def set_outlet_home(self):
        """Sets the current position of the outlet stage/motor as home. Return False if device is not capable."""
        return False  # fixme, add a history like objectivehistory.p?

    def home_outlet(self):
        """Goes to the current position marked as home. Return False if device has no 'home' capability."""
        return False

    def close_objective(self):
        self.objective_control.close()
        return True

    def set_objective(self, h=None, rel_h=None):
        if h:
            self.objective_control.set_z(h)
            return True

        elif rel_h:
            self.objective_control.set_rel_z(rel_h)
            return True

        return False

    def get_objective(self):
        return self.objective_control.read_z()

    def stop_objective(self):
        self.objective_control.stop()
        return True

    def set_objective_home(self):
        """Sets the current position of the objective stage/motor as home. Return False if device is not capable."""
        self.objective_control.set_origin()
        return True

    def home_objective(self):
        """Goes to the current position marked as home. Return False if device has no 'home' capability."""
        self.objective_control.go_home()
        return True

    def close_voltage(self):
        self.daq_board_control.change_voltage(0)

    def set_voltage(self, v=None):
        self._start_daq()
        self.daq_board_control.change_voltage(v)
        return True

    def get_voltage(self):
        return self.daq_board_control.voltage

    def get_voltage_data(self):
        return self.daq_board_control.data['ai1']

    def get_current_data(self):
        return self.daq_board_control.data['ai2']

    def get_rfu_data(self):
        return self.daq_board_control.data['ai3']

    def set_laser_parameters(self, pfn=None, att=None, energy=None, mode=None, burst=None):
        if pfn:
            self.laser_control.set_pfn('{:03d}'.format(int(pfn)))

        if att:
            self.laser_control.set_attenuation('{:03d}'.format(int(att)))

        if energy:
            logging.info('Cannot set energy of laser currently.')

        if mode:
            logging.info('Cannot set mode of laser currently.')

        if burst:
            self.laser_control.set_burst('{:04d}'.format(int(burst)))

        return True

    def laser_standby(self):
        executed = self.laser_control.start()
        if executed:
            self._laser_poll_flag.set()

            start_time = time.time()
            threading.Thread(target=self._poll_laser, args=(start_time,), daemon=True).start()
            logging.info('Laser on standby for {}s'.format(self.laser_max_time))

            return True

    def laser_fire(self):
        self.laser_control.fire()
        return True

    def laser_stop(self):
        self.laser_control.stop()
        return True

    def laser_close(self):
        self.laser_control.off()
        return True

    def laser_check(self):
        self.laser_control.check_status()
        self.laser_control.check_parameters()
        return True

    def pressure_close(self):
        self.pressure_control.close()
        return True

    def pressure_rinse_start(self):
        self.pressure_control.apply_rinse_pressure()
        return True

    def pressure_rinse_stop(self):
        self.pressure_control.stop_rinse_pressure()
        return True

    def pressure_valve_open(self):
        self.pressure_control.open_valve()
        return True

    def pressure_valve_close(self):
        self.pressure_control.close_valve()
        return True


# NEEDS:
# A motor for the outlet (don't really need encoder), and a z stage for the inlet and a
# pressure control device (preferably the same one used on the Barracuda system)
class OstrichSystem(BaseSystem):
    system_id = 'OSTRICH'

    _daq_dev = "/Dev1/"  # fixme not sure what to put here ("/Dev1/" is from Barracuda)
    _daq_voltage_control = 'ao1'
    _daq_current_readout = 'ai0'
    _daq_voltage_readout = 'ai1'
    _daq_rfu = 'ai3'
    _xy_stage_id = 'TIXYDrive'
    _z_stage_id = 'TIZDrive'

    _z_stage_lock = threading.Lock()
    _outlet_lock = threading.Lock()
    _objective_lock = threading.Lock()
    _xy_stage_lock = threading.Lock()
    _pressure_lock = threading.Lock()
    _camera_lock = threading.Lock()

    _laser_pfn = 255
    image_size = (512, 512)

    def __init__(self):
        super(OstrichSystem, self).__init__()

    def _start_daq(self):
        self.daq_board_control.max_time = 600000
        self.daq_board_control.start_read_task()

    def start_system(self):
        """Puts the system into its functional state."""
        self.xy_stage_control = XYControl.XYControl(lock=self._xy_stage_lock, stage=self._xy_stage_id,
                                                    config_file='sysConfig.cfg', home=HOME, loaded=False)

        self.objective_control = ZStageControl.NikonZStage(lock=self._objective_lock, stage=self._z_stage_id,
                                                           config_file='sysConfig.cfg', home=HOME, loaded=False)

        self.daq_board_control = DAQControl.DAQBoard(dev=self._daq_dev, voltage_read=self._daq_voltage_readout,
                                                     current_read=self._daq_current_readout, rfu_read=self._daq_rfu,
                                                     voltage_control=self._daq_voltage_control)

        self.laser_control = True  # No need to define a new class when we only have one command

        self.image_control = ImageControl.ImageControl(home=HOME)
        return True

    def close_system(self):
        """Takes system out of its functional state."""
        self.close_z()
        self.close_xy()
        self.close_voltage()
        self.close_outlet()
        self.close_objective()
        self.close_image()
        return True

    def close_xy(self):
        """Removes immediate functionality of XY stage."""
        self.xy_stage_control.close()

    def set_xy(self, xy=None, rel_xy=None):
        """Sets the position of the XY Stage. 'xy' is absolute, 'rel_xy' is relative to current."""
        if xy:
            self.xy_stage_control.set_xy(xy)
        elif rel_xy:
            self.xy_stage_control.set_rel_xy(rel_xy)

        return True

    def get_xy(self):
        """Gets the current position of the XY stage."""
        return self.xy_stage_control.read_xy()

    def stop_xy(self):
        """Stops current movement of the XY stage."""
        self.xy_stage_control.stop()
        return True

    def close_z(self):
        """Removes immediate functionality of Z stage/motor."""
        pass

    def set_z(self, z=None, rel_z=None):
        """Sets the position of the Z stage/motor. 'z' is absolute, 'rel_z' is relative to current."""
        pass

    def get_z(self):
        """Gets the current position of the Z stage/motor."""
        pass

    def stop_z(self):
        """Stops current movement of the Z stage/motor."""
        pass

    def close_outlet(self):
        """Removes immediate functionality of the outlet stage/motor."""
        pass

    def set_outlet(self, h=None, rel_h=None):
        """Sets the position of the outlet stage/motor. 'h' is absolute, 'rel_h' is relative to current."""
        pass

    def get_outlet(self):
        """Gets the current position of the outlet stage/motor."""
        pass

    def stop_outlet(self):
        """Stops current movement of the outlet stage/motor."""
        pass

    def close_objective(self):
        """Removes immediate functionality of the objective stage/motor."""
        self.z_stage_control.close()
        return True

    def set_objective(self, h=None, rel_h=None):
        """Sets the position of the objective stage/motor. 'h' is absolute, 'rel_h' is relative to current."""
        if h:
            self.objective_control.set_z(h)
        elif rel_h:
            self.objective_control.set_rel_z(rel_h)

        return True

    def get_objective(self):
        """Gets the current position of the objective stage/motor."""
        return self.objective_control.read_z()

    def stop_objective(self):
        """Stops the current movement of the objective stage/motor."""
        self.objective_control.stop()
        return True

    def close_voltage(self):
        """Removes immediate functionality of the voltage source."""
        pass

    def set_voltage(self, v=None):
        """Sets the current voltage of the voltage source."""
        self._start_daq()
        self.daq_board_control.change_voltage(v)
        return True

    def get_voltage(self):
        """Gets the current voltage of the voltage source."""
        return self.daq_board_control.voltage

    def get_voltage_data(self):
        """Gets a list of the voltages over time."""
        return self.daq_board_control.data[self._daq_voltage_readout]

    def get_current_data(self):
        """Gets a list of the current over time."""
        return self.daq_board_control.data[self._daq_current_readout]

    def get_rfu_data(self):
        """Gets a list of the RFU over time."""
        return self.daq_board_control.data[self._daq_rfu]

    def close_image(self):
        """Removes the immediate functionality of the camera."""
        self.image_control.close()
        return True

    def start_feed(self):
        """Sets camera to start gathering images. Does not return images."""
        self.image_control.start_video_feed()
        return True

    def stop_feed(self):
        """Stops camera from gathering images."""
        # Only fill out stop_feed if you can fill out start_feed.
        self.image_control.stop_video_feed()
        return True

    def get_image(self):
        """Returns the most recent image from the camera."""
        with self._camera_lock:
            image = self.image_control.get_recent_image(size=self.image_size)

            if image is None:
                return None

            if not HOME:
                image.save("recentImg.png")

        return image

    def set_laser_parameters(self, pfn=None, att=None, energy=None, mode=None, burst=None):
        """Sets the parameters of the laser device."""
        if pfn:
            if 0 < pfn < 256:  # fixme, not sure if this is the actual limit, but all I've seen is 255 and 0. Only 2?
                self._laser_pfn = pfn
            else:
                logging.error('Invalid PFN, must be an integer between 0 and 255.')
        else:
            logging.warning('Cannot set this parameter on the current laser for Ostrich.')
        return True

    def laser_standby(self):
        """Puts laser in a standby 'fire-ready' mode."""
        logging.warning('Laser can not be put in standby from computer.')
        return True

    def laser_fire(self):
        """Fires the laser."""
        ctypes.windll.inpout32.Out32(0x378, self._laser_pfn)
        time.sleep(0.1)
        ctypes.windll.inpout32.Out32(0x378, 0)
        return True

    def laser_stop(self):
        """Stops current firing of the laser."""
        ctypes.windll.inpout32.Out32(0x378, 0)
        return True

    def laser_close(self):
        """Removes immediate functionality of the laser."""
        ctypes.windll.inpout32.Out32(0x378, 0)
        return True

    def laser_check(self):
        """Logs status of laser system."""
        # fixme, see if an exception comes up when setting laser power to 0 and the laser is not properly connected. If
        # fixme an exception occurs we can use that to log whether the system is on or not.
        logging.warning('Laser system status can not be checked from computer.')
        return True

    def pressure_close(self):
        """Removes immediate functionality of the pressure system."""
        pass

    def pressure_rinse_start(self):
        """Starts rinsing pressure.."""
        pass

    def pressure_rinse_stop(self):
        """Stops rinsing pressure."""
        pass

    def pressure_valve_open(self):
        """Opens pressure valve."""
        pass

    def pressure_valve_close(self):
        """Closes pressure valve."""
        pass