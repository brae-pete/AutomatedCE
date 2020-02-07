# Standard library modules
import threading
import logging
import time
import ctypes
import numpy as np

# Custom Hardware Modules  fixme do a dynamic import so only those modules necessary are imported.
import traceback

from hardware import DAQControl
from hardware import ImageControl
from hardware import OutletControl
from hardware import XYControl
from hardware import ZStageControl
from hardware import ObjectiveControl
from hardware import LaserControl
from hardware import PressureControl
from hardware import LightControl
from hardware import ScopeControl
from hardware import PowerSupplyControl
from hardware import MicroControlClient

# Network Module
import CENetworks

HOME = False


class BaseSystem:
    """Interface controllers will interact with to control the different hardware systems."""
    system_id = None

    # Supported hardware checks for the program controllers
    """Artifacts of old system prior to example base classes"""
    hasCameraControl = True
    hasXYControl = True
    hasInletControl = True
    hasOutletControl = True
    hasVoltageControl = True
    hasPressureControl = True
    hasObjectiveControl = True
    hasLaserControl = True
    hasLEDControl = True

    image_size = 0.5
    objective_focus = 0
    xy_stage_size = [112792, 64340]  # Rough size in mm
    xy_stage_offset = [0, 0]  # Reading on stage controller when all the way to left and up (towards wall)
    xy_stage_inversion = [1, 1]

    def __init__(self):
        # Laser Variables
        self.laser_max_time = None
        self._laser_poll_flag = threading.Event()
        self.laser_start_time = time.time()

        # Hardware Class Objects: These are all (and should remain) the base classes
        self.xy_stage_control = XYControl.XYControl()
        self.z_stage_control = ZStageControl.ZStageControl()
        self.outlet_control = OutletControl.OutletControl()
        self.objective_control = ObjectiveControl.ObjectiveControl()
        self.power_supply_control = PowerSupplyControl.PowerSupply()
        self.adc_control = DAQControl.ADC()
        self.daq_board_control = self.adc_control
        self.data_filter_control = DAQControl.Filter()
        self.image_control = ImageControl.ImageControl()
        self.laser_control = LaserControl.Laser()
        self.pressure_control = PressureControl.PressureControl()
        self.led_control = LightControl.LED()
        self.shutter_control = ScopeControl.ShutterControl()
        self.filter_control = ScopeControl.FilterWheelControl()

        # Start the processes needed
        self.adc_control.start()

    def calibrate_system(self, permissions_gui):
        """Calibrates the system."""
        logging.error('calibrate_system not implemented in hardware class.')

    def start_system(self):
        """Puts the system into its functional state."""
        logging.error('start_system not implemented in hardware class.')

    def close_xy(self):
        """Removes immediate functionality of XY stage."""
        self.xy_stage_control.close()

    def set_xy(self, xy=None, rel_xy=None):
        """Sets the position of the XY Stage. 'xy' is absolute, 'rel_xy' is relative to current."""
        if xy is not None:
            self.xy_stage_control.set_xy(xy)
        elif rel_xy is not None:
            self.xy_stage_control.set_rel_xy(rel_xy)

    def get_xy(self):
        """Gets the current position of the XY stage."""
        return self.xy_stage_control.read_xy()

    def stop_xy(self):
        """Stops current movement of the XY stage."""
        self.xy_stage_control.stop()

    def set_xy_home(self):
        """Sets the current position of XY stage as home. Return False if device has no 'home' capability."""
        self.xy_stage_control.set_origin()

    def wait_xy(self):
        """ Waits for the stage to stop moving (blocking)"""
        self.xy_stage_control.wait_for_move()

    def home_xy(self):
        """Goes to current position marked as home. Return False if device has no 'home' capability."""
        self.xy_stage_control.origin()

    def close_z(self):
        """Removes immediate functionality of Z stage/motor."""
        self.z_stage_control.close()

    def set_z(self, z=None, rel_z=None):
        """Sets the position of the Z stage/motor. 'z' is absolute, 'rel_z' is relative to current."""
        if z is not None:
            self.z_stage_control.set_z(z)
        elif rel_z is not None:
            self.z_stage_control.jog(z)
        else:
            return False
        return True

    def get_z(self):
        """Gets the current position of the Z stage/motor."""
        return self.z_stage_control.read_z()

    def stop_z(self):
        """Stops current movement of the Z stage/motor."""
        self.z_stage_control.stop()

    def jog_z(self, distance):
        """Jogs the Z axis"""
        self.z_stage_control.jog(distance)
        logging.info("Jog and Rel_z are equivalent")

    def set_z_home(self):
        """Sets the current position of the Z stage/motor as home. Return False if device has no 'home' capability."""
        self.z_stage_control.go_home()

    def home_z(self):
        """Goes to current position marked as home. Return False if device has no 'home' capability."""
        self.z_stage_control.go_home()

    def wait_z(self):
        """ Waits until the z-stage has finished its move before releasing the lock"""
        self.z_stage_control.wait_for_move()

    def close_outlet(self):
        """Removes immediate functionality of the outlet stage/motor."""
        self.outlet_control.close()

    def set_outlet(self, h=None, rel_h=None):
        """Sets the position of the outlet stage/motor. 'h' is absolute, 'rel_h' is relative to current."""
        if h is not None:
            self.outlet_control.set_z(h)
        elif rel_h is not None:
            self.outlet_control.set_rel_z(rel_h)
        else:
            return False
        return True

    def get_outlet(self):
        """Gets the current position of the outlet stage/motor."""
        return self.outlet_control.read_z()

    def stop_outlet(self):
        """Stops current movement of the outlet stage/motor."""
        return self.outlet_control.stop()

    def wait_outlet(self):
        """
        Waits for the outlet to stop moving, return final height
        :return:
        """
        return self.outlet_control.wait_for_move()

    def set_outlet_home(self):
        """Sets the current position of the outlet stage/motor as home. Return False if device is not capable."""
        return False

    def home_outlet(self):
        """Goes to the current position marked as home. Return False if device has no 'home' capability."""
        self.outlet_control.go_home()
        return True

    def close_objective(self):
        """Removes immediate functionality of the objective stage/motor."""
        self.objective_control.close()

    def set_objective(self, h=None, rel_h=None):
        """Sets the position of the objective stage/motor. 'h' is absolute, 'rel_h' is relative to current."""
        if h is not None:
            self.objective_control.set_z(h)
        elif rel_h is not None:
            self.objective_control.set_rel_z(rel_h)
        else:
            return False
        return True

    def get_objective(self):
        """Gets the current position of the objective stage/motor."""
        return self.objective_control.read_z()

    def stop_objective(self):
        """Stops the current movement of the objective stage/motor."""
        self.objective_control.stop()

    def set_objective_home(self):
        """Sets the current position of the objective stage/motor as home. Return False if device is not capable."""
        return False

    def wait_objective(self):
        """ Waits till the objective has stopped moving"""
        self.objective_control.wait_for_move()

    def home_objective(self):
        """Goes to the current position marked as home. Return False if device has no 'home' capability."""
        self.objective_control.go_home()
        return True

    def close_voltage(self):
        """Removes immediate functionality of the voltage source."""
        self.power_supply_control.stop_voltage()

    def stop_voltage(self):
        """ Sets the voltage to Zero"""
        self.power_supply_control.stop_voltage()

    def set_voltage(self, v=None, chnl=0):
        """Sets the current voltage of the voltage source."""
        chnl = self.power_supply_control.channels[chnl]
        self.power_supply_control.set_electrode_voltage(chnl, v)
        self.power_supply_control.apply_changes()

    def get_voltage_setting(self, chnl=0):
        """ Returns the voltage setting for the DAC"""
        chnl = self.power_supply_control.channels[chnl]
        return self.power_supply_control.get_electrode_setting(chnl)

    def get_voltage(self):
        """Gets the current voltage of the voltage source."""
        return self.adc_control.data[-1, 0]

    def get_voltage_data(self):
        """Gets a list of the voltages over time."""
        return self.adc_control.data[0, :]

    def get_current_data(self):
        """Gets a list of the current over time."""
        return self.adc_control.data[1, :]

    def get_rfu_data(self):
        """Gets a list of the RFU over time."""
        data = self.adc_control.data[2, :]
        if len(data) > 100:
            data = self.data_filter_control.filter_data(data)
        return data

    def get_data(self):
        """ Returns the data """
        with self.adc_control.data_lock:
            rfu = self.get_rfu_data()
            volts = self.get_voltage_data()
            current = self.get_current_data()
        time_points = np.linspace(0, len(rfu)/self.adc_control.downsampled_freq, len(rfu))
        return {'rfu': rfu, 'volts': volts, 'current': current, 'time':time_points}

    def close_image(self):
        """Removes the immediate functionality of the camera."""
        self.image_control.close()

    def open_image(self):
        """Opens the camera Resources """
        self.image_control.open()

    def camera_state(self):
        """ Checks if camera resources are available"""
        return self.image_control.camera_state()

    def start_live_feed(self):
        """ Starts a live feed in a separate window"""
        self.image_control.live_view()

    def start_feed(self):
        """Sets camera to start gathering images. Does not return images."""
        if self.camera_state():
            try:
                self.image_control.start_video_feed()
            except Exception as e:
                logging.info("{}".format(e))
                traceback.print_last()
        return True

    def stop_feed(self):
        """Stops camera from gathering images."""
        # Only fill out stop_feed if you can fill out start_feed.
        self.image_control.stop_video_feed()

    def save_buffer(self, folder, name, fps=5):
        """
        Saves the camera buffer to the folder as .avi file. Also copies sequence of images as reference.
        :param folder: folder to store data
        :param name: video file to save to, will overwrite existing files
        :param fps: frames per second to store the video at, defaults to 5 fps irregardless of camera frame rate
        :return:
        """
        self.image_control.save_capture_sequence(folder, name, fps)
        return True

    def get_image(self):
        """Returns the most recent image from the camera."""
        image = self.image_control.get_recent_image()
        if image is None:
            return None
        if not HOME:
            self.image_control.save_image(image, "recentImg.png")
        return image

    def get_raw_image(self):
        """ Get a raw image (no processing) from the image class"""
        with self.image_control.lock:
            img = self.image_control.raw_img.copy()
            img = self.image_control.rotate_raw_img(img, 270)
        return img

    def snap_image(self, filename=None):
        """ Snap and return an image from the camera. Save file if requested"""
        img = self.image_control.get_single_image()
        if filename is not None:
            self.image_control.save_raw_image(filename)
        self.image_control.save_image(img, "recentImg.png")
        return img

    def save_raw_image(self, filename):
        """ Save a raw image from teh image class """
        self.image_control.save_raw_image(filename)

    def set_exposure(self, exp):
        """
        Set the camera exposure
        """
        self.image_control.set_exposure(exp)
        return

    def get_exposure(self):
        """
        get the camera exposure
        :return:
        """
        return self.image_control.get_exposure()

    def set_laser_parameters(self, pfn=None, att=None, energy=None, mode=None, burst=None):
        """Sets the parameters of the laser device."""
        self.laser_control.set_laser_parameters(pfn=pfn, att=att, energy=energy, mode=mode, burst=burst)

    def laser_standby(self):
        """Puts laser in a standby 'fire-ready' mode."""
        self.laser_control.laser_standby()

    def laser_fire(self):
        """Fires the laser."""
        self.laser_control.laser_fire()

    def laser_stop(self):
        """Stops current firing of the laser."""
        self.laser_control.laser_stop()

    def laser_close(self):
        """Removes immediate functionality of the laser."""
        self.laser_control.close()

    def laser_check(self):
        """Logs status of laser system."""
        self.laser_control.laser_check()

    def restart_laser_run_time(self):
        """ Restarts the clock for the laser run time or restarts the laser
        This is needed for the NewWave laser
        """

        if self._laser_poll_flag.is_set():
            self.laser_start_time = time.time()
            return True
        else:
            self.laser_standby()
            return False

    def pressure_close(self):
        """Closes the pressure resources """
        self.pressure_control.close()

    def pressure_rinse_start(self):
        """Starts rinsing pressure.."""
        self.pressure_control.apply_rinse_pressure()

    def vacuum_rinse_start(self):
        """ Starts vacuum pressure..."""
        self.pressure_control.apply_vacuum()

    def pressure_rinse_stop(self):
        """Stops rinsing pressure."""
        self.pressure_control.stop_rinse_pressure()

    def pressure_valve_open(self):
        """Opens pressure valve."""
        self.pressure_control.open_valve()

    def pressure_valve_close(self):
        """Closes pressure valve."""
        self.pressure_control.close_valve()

    def turn_on_led(self, channel='R'):
        """ Turns on the LED with the corresponding channel"""
        self.led_control.start_led(channel)

    def turn_off_led(self, channel='R'):
        """ Turns off LED with corresponding channel"""
        self.led_control.stop_led(channel)

    def turn_on_dance(self):
        """ Flashes RGB lights on and off """
        self.led_control.dance_party()

    def turn_off_dance(self):
        """ Turns off the flashing RGB """
        self.led_control.dance_stop.set()

    def shutter_open(self):
        """ Opens the shutter"""
        self.shutter_control.open_shutter()

    def shutter_close(self):
        """ Closes the shutter"""
        self.shutter_control.close_shutter()

    def shutter_get(self):
        """ Gets shutter state """
        self.shutter_control.get_shutter()

    def filter_set(self, channel):
        """ Sets the filter cube channel"""
        self.filter_control.set_state(channel)

    def filter_get(self):
        """ Returns the current filter channel"""
        return self.filter_control.get_state()

    def get_fl_image(self, exp, chnl, filepath=None):
        """ Returns brightfield and fluorescent images"""
        # Turn off the LED
        old_leds = self.led_control.channel_states.copy()
        for led in old_leds:
            if old_leds[led]:
                self.turn_off_led(led)
        # Stop continuous image
        self.stop_feed()
        time.sleep(0.2)
        # Adjust Exposure
        old_exp = self.get_exposure()
        self.set_exposure(exp)
        # Adjust Filter
        old_chnl = self.filter_get()
        self.filter_set(chnl)
        logging.info("Filter Set")
        time.sleep(1)
        # Adjust Shutter
        self.shutter_open()
        # Snap
        time.sleep((exp / 1000) + 0.5)
        # st = time.time()
        img = self.snap_image()
        if filepath:
            self.save_raw_image(filepath)
        # Close Shutter
        self.shutter_close()
        # Adjust Filter
        self.filter_set(old_chnl)
        # Start LED
        for led in old_leds:
            if old_leds[led]:
                self.turn_on_led(led)
        # Adjust Exposure
        self.set_exposure(old_exp)
        # Restart Live Feed
        self.start_feed()
        return self.get_raw_image()

    def get_bf_and_fl_images(self):
        """ Returns brightfield and fluorescent images"""
        logging.error("get bf and fl images is not supported in hardware class")

    def close_system(self):
        """ Closese all the associated objects"""
        try:
            self.close_image()
        except:
            logging.warning("Did not shut down Z")

        try:
            self.close_objective()
        except:
            logging.warning("Did not shut down Z")
        try:
            self.shutdown_shutter()
        except:
            logging.warning("Did not close shutter")
        try:
            self.close_outlet()
        except:
            logging.warning("Did not shut down Z")
        try:
            self.close_voltage()
        except:
            logging.warning("Did not shut down Z")
        try:
            self.close_z()
        except:
            logging.warning("Did not shut down Z")

        try:
            self.close_daq()
        except:
            logging.warning("Did not close DAQ tasks")
        return True


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

    _z_stage_lock = threading.RLock()  # Same thread can access the lock at multiple points, but not multiple threads
    _outlet_lock = threading.RLock()
    _objective_lock = threading.Lock()
    _xy_stage_lock = threading.Lock()
    _pressure_lock = threading.Lock()
    _camera_lock = threading.RLock()
    _laser_lock = threading.Lock()
    _laser_poll_flag = threading.Event()
    _led_lock = _outlet_lock
    _laser_rem_time = 0
    laser_start_time = time.time()

    image_size = 0.5
    objective_focus = 0
    xy_stage_size = [112792, 64340]  # Rough size in mm
    xy_stage_offset = [112739, 0]  # Reading on stage controller when all the way to left and up (towards wall)
    xy_stage_inversion = [1, -1]

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
        self.hasLEDControl = True

    def _start_daq(self):
        self.daq_board_control.max_time = 600000
        self.daq_board_control.start_read_task()

    def _poll_laser(self):
        while True:
            if self._laser_poll_flag.is_set():
                self._laser_rem_time = self.laser_max_time - (time.time() - self.laser_start_time)
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
        # Initialize all the motors independently
        zstage = threading.Thread(target=self._start_zstage)
        zstage.start()
        outlet = threading.Thread(target=self._start_outlet)
        outlet.start()
        objective = threading.Thread(target=self._start_objective)
        objective.start()
        # Wait for motors to finish homing
        zstage.join()
        outlet.join()
        objective.join()
        self.image_control = ImageControl.PVCamImageControl(lock=self._camera_lock)
        self.xy_stage_control = XYControl.PriorControl(lock=self._xy_stage_lock)
        self.daq_board_control = DAQControl.DAQBoard(dev=self._daq_dev, voltage_read=self._daq_voltage_readout,
                                                     current_read=self._daq_current_readout, rfu_read=self._daq_rfu,
                                                     voltage_control=self._daq_voltage_control)
        self.laser_control = LaserControl.Laser(com=self._laser_com, lock=self._laser_lock, home=HOME)

        self.led_control = LightControl.CapillaryLED(com='COM9', arduino=self.outlet_control.arduino,
                                                     lock=self._led_lock)
        self._start_daq()

        self.pressure_control = PressureControl.PressureControl(com=self._pressure_com, lock=self._pressure_lock,
                                                                arduino=self.outlet_control.arduino, home=HOME)

        pass

    def _start_outlet(self):
        self.outlet_control = OutletControl.OutletControl(com=self._outlet_com, lock=self._outlet_lock, home=HOME)

    def _start_zstage(self):
        self.z_stage_control = ZStageControl.ZStageControl(com=self._z_stage_com, lock=self._z_stage_lock, home=HOME)

    def _start_objective(self):
        self.objective_control = ObjectiveControl.ObjectiveControl(com=self._objective_com, lock=self._objective_lock,
                                                                   home=HOME)

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
        with self.image_control.lock:
            self.image_control.close()
        return True

    def open_image(self):
        self.image_control.open()
        return True

    def start_feed(self):
        if self.camera_state():
            self.image_control.start_video_feed()
        return True

    def stop_feed(self):
        self.image_control.stop_video_feed()
        return True

    def save_buffer(self, folder, name, fps=5):
        """
        Saves the camera buffer to the folder as .avi file. Also copies sequence of images as reference.
        :param folder: folder to store data
        :param name: video file to save to, will overwrite existing files
        :param fps: frames per second to store the video at, defaults to 5 fps irregardless of camera frame rate
        :return: True
        """
        self.image_control.save_capture_sequence(folder, name, fps)
        return True

    def camera_state(self):
        """ Checks if camera resources are available"""
        return self.image_control.camera_state()

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

    def save_data(self, filepath):
        try:
            self.daq_board_control.save_data(filepath)
        except FileNotFoundError:
            logging.info('File not selected')

        return True

    def get_voltage(self):
        return self.daq_board_control.voltage

    def get_voltage_data(self):
        return self.daq_board_control.data['ai1']

    def get_current_data(self):
        return self.daq_board_control.data['ai2']

    def get_rfu_data(self):
        return self.daq_board_control.data['ai3']

    def get_data(self):
        with self.daq_board_control.data_lock:
            rfu = self.daq_board_control.data['avg']
            volts = self.daq_board_control.data[self._daq_voltage_readout]
            current = self.daq_board_control.data[self._daq_current_readout]
        return {'rfu': rfu, 'volts': volts, 'current': current}

    def stop_voltage(self):
        self.daq_board_control.change_voltage(0)

    def set_laser_parameters(self, pfn=None, att=None, energy=None, mode=None, burst=None):
        if pfn:
            self.laser_control.set_pfn('{:03d}'.format(int(pfn)))

        if att:
            self.laser_control.set_attenuation('{:03d}'.format(int(att)))

        if energy:
            logging.info('Cannot set energy of laser currently.')

        if mode:
            self.laser_control.set_mode('0')
            self.laser_control.set_rep_rate('010')

        if burst:
            self.laser_control.set_burst('{:04d}'.format(int(burst)))

        return True

    def laser_standby(self):
        executed = self.laser_control.start()
        if executed:
            self._laser_poll_flag.set()

            self.laser_start_time = time.time()
            threading.Thread(target=self._poll_laser, daemon=True).start()
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

    def restart_laser_run_time(self):
        """ Restarts the clock for the laser run time or restarts the laser"""

        if self._laser_poll_flag.is_set():
            self.laser_start_time = time.time()
            return True
        else:
            self.laser_standby()
            return False

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

    def turn_on_led(self, channel='R'):
        self.led_control.start_led(channel)

    def turn_off_led(self, channel='R'):
        self.led_control.stop_led(channel)

    def turn_on_dance(self):
        threading.Thread(target=self.led_control.dance_party).start()

    def turn_off_dance(self):
        self.led_control.dance_stop.set()


class NikonEclipseTi(BaseSystem):
    system_id = 'ECLIPSETI'
    _z_stage_com = 'COM3'
    _outlet_com = 'COM4'
    _pressure_com = 'COM4'

    _daq_dev = "/Dev1/"  # fixme not sure what to put here ("/Dev1/" is from Barracuda)
    _daq_current_readout = "ai5"
    _daq_voltage_readout = "ai1"
    _daq_voltage_control = 'ao1'
    _daq_rfu = "ai3"

    _z_stage_lock = threading.RLock()
    _outlet_lock = threading.RLock()
    _scope_lock = threading.Lock()
    _camera_lock = threading.RLock()
    _led_lock = _outlet_lock

    xy_stage_inversion = [1, -1]
    xy_stage_size = [50000, 50000]
    xy_stage_offset = [0, 0]

    def __init__(self):
        super(NikonEclipseTi, self).__init__()
        self.laser_max_time = 600

        self.hasCameraControl = True
        self.hasInletControl = True
        self.hasLaserControl = True
        self.hasObjectiveControl = True
        self.hasOutletControl = True
        self.hasVoltageControl = True
        self.hasPressureControl = True
        self.hasXYControl = True
        self.hasLEDControl = True
        self.hasShutterControl = True
        self.hasFilterControl = True

    def _start_daq(self):
        self.daq_board_control.max_time = 600000
        self.daq_board_control.start_read_task()

    def start_system(self):
        # Initialize all the motors independently
        zstage = threading.Thread(target=self._start_zstage)
        zstage.start()
        outlet = threading.Thread(target=self._start_outlet)
        outlet.start()
        # Wait for motors to finish homing
        zstage.join()
        outlet.join()

        # Image Control uses separate MMC
        self.image_control = ImageControl.MicroControl(port=7813, lock=self._camera_lock)

        # Nikon Scope shares a MMC
        self.objective_control = ObjectiveControl.MicroControl(port=7812, lock=self._scope_lock)  # Use Presets
        self.xy_stage_control = XYControl.MicroControl(mmc=self.objective_control.mmc, lock=self._scope_lock)
        self.filter_control = ScopeControl.FilterMicroControl(mmc=self.objective_control.mmc,
                                                              lock=self._scope_lock)
        # Shutter is on its own MMC
        self.shutter_control = ScopeControl.ShutterMicroControl(port=7811,
                                                                lock=self._scope_lock)
        # Set up and start DAQ
        self.daq_board_control = DAQControl.DAQBoard(dev=self._daq_dev, voltage_read=self._daq_voltage_readout,
                                                     current_read=self._daq_current_readout, rfu_read=self._daq_rfu,
                                                     voltage_control=self._daq_voltage_control, laser_fire=True)
        # No Laser Control Will  need to be on DAQ
        self._start_daq()

        # Pressure Runs on Outlet ARduino
        self.led_control = LightControl.CapillaryLED(arduino=self.outlet_control.arduino, lock=self._led_lock)
        self.pressure_control = PressureControl.PressureControl(com=self._pressure_com, lock=self._outlet_lock,
                                                                arduino=self.outlet_control.arduino, home=HOME)

        pass

    def _start_outlet(self):
        self.outlet_control = OutletControl.OutletControl(com=self._outlet_com, lock=self._outlet_lock, home=HOME,
                                                          invt=1)

    def _start_zstage(self):
        self.z_stage_control = ZStageControl.PowerStep(com=self._z_stage_com, lock=self._z_stage_lock, home=HOME,
                                                       invt=-1)

    def close_system(self):
        try:
            self.close_image()
            self.image_control._close_client()
        except:
            logging.warning("Did not shut down Z")

        try:
            self.close_objective()
        except:
            logging.warning("Did not shut down Z")
        try:
            self.shutdown_shutter()
        except:
            logging.warning("Did not close shutter")
        try:
            self.close_outlet()
        except:
            logging.warning("Did not shut down Z")
        try:
            self.close_voltage()
        except:
            logging.warning("Did not shut down Z")
        try:
            self.close_z()
        except:
            logging.warning("Did not shut down Z")

        try:
            self.close_daq()
        except:
            logging.warning("Did not close DAQ tasks")
        return True

    def record_image(self, filename):
        img = self.get_image()
        self.image_control.save_image(img, filename)
        return

    def _close_client(self):
        self.image_control._close_client()

    def set_xy(self, xy=None, rel_xy=None):
        """Move the XY Stage"""
        if xy is not None:
            if type(xy[0]) is not float:
                logging.warning(" XY is not a valid position {}".format(xy))
                return False

        elif rel_xy is not None:
            if type(rel_xy[0]) is not float or type(rel_xy[0]) is not int:
                logging.warning("XY is not valid position".format(rel_xy))

        if xy:
            self.xy_stage_control.set_xy(xy)
        elif rel_xy:
            self.xy_stage_control.set_rel_xy(rel_xy)
        return True

    def wait_xy(self):
        """ Waits for the stage to stop moving (blocking)"""
        self.xy_stage_control.wait_for_move()

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
        return self.z_stage_control.get_z()

    def stop_z(self):
        self.z_stage_control.stop()
        return True

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

    def wait_outlet(self):
        return self.outlet_control.wait_for_move()

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
        self.objective_control._close_client()
        return True

    def set_objective(self, h=None, rel_h=None):
        if h:
            self.objective_control.set_z(h)
            return True

        elif rel_h:
            self.objective_control.set_rel_z(rel_h)
            return True

        return False

    def wait_objective(self):
        """ Waits till the objective has stopped moving"""
        self.objective_control.wait_for_move()
        return True

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

    def save_data(self, filepath):
        try:
            self.daq_board_control.save_data(filepath)
        except FileNotFoundError:
            logging.info('File not selected')

        return True

    def get_voltage(self):
        return self.daq_board_control.voltage

    def get_voltage_data(self):
        return self.daq_board_control.data['ai1']

    def get_current_data(self):
        return self.daq_board_control.data['ai2']

    def get_rfu_data(self):
        return self.daq_board_control.data['ai3']

    def get_data(self):
        with self.daq_board_control.data_lock:
            rfu = self.daq_board_control.data['avg']
            volts = self.daq_board_control.data[self._daq_voltage_readout]
            current = self.daq_board_control.data[self._daq_current_readout]
        return {'rfu': rfu, 'volts': volts, 'current': current}

    def stop_voltage(self):
        self.daq_board_control.change_voltage(0)

    def close_daq(self):
        try:
            self.stop_voltage()
        except Exception as e:
            logging.error("Could not close voltage: {}".format(e))

        try:
            self.laser_close()
        except Exception as e:
            logging.error("Could not close laser: {}".format(e))

    def pressure_close(self):
        self.pressure_control.close()
        return True

    def pressure_rinse_start(self):
        self.pressure_control.apply_rinse_pressure()
        return True

    def pressure_rinse_stop(self):
        self.pressure_control.stop_rinse_pressure()
        return True

    def vacuum_rinse_start(self):
        """ Starts vacuum pressure..."""
        self.pressure_control.apply_vacuum()
        return True

    def pressure_valve_open(self):
        self.pressure_control.open_valve()
        return True

    def pressure_valve_close(self):
        self.pressure_control.close_valve()
        return True

    def turn_on_led(self, channel='R'):
        self.led_control.start_led(channel)

    def turn_off_led(self, channel='R'):
        self.led_control.stop_led(channel)

    def turn_on_dance(self):
        threading.Thread(target=self.led_control.dance_party).start()

    def turn_off_dance(self):
        self.led_control.dance_stop.set()

    def laser_standby(self):
        """Puts laser in a standby 'fire-ready' mode."""
        self.daq_board_control.laser_standby()

    def laser_fire(self):
        """Fires the laser."""
        threading.Thread(target=self.daq_board_control.laser_fire).start()

    def laser_stop(self):
        """Stops current firing of the laser."""
        self.daq_board_control.laser_shutdown()

    def laser_close(self):
        """Removes immediate functionality of the laser."""
        self.laser_stop()

    def shutter_open(self):
        """ Opens the shutter"""
        self.shutter_control.open_shutter()

    def shutter_close(self):
        """ Closes the shutter"""
        self.shutter_control.close_shutter()

    def shutter_get(self):
        """ Gets shutter state """
        return self.shutter_control.get_shutter()

    def shutdown_shutter(self):
        """ Shutsdown the Shutter client and mmc"""
        self.shutter_control.close()
        self.shutter_control._close_client()

    def filter_set(self, channel):
        """ Sets the filter cube channel"""
        self.filter_control.set_state(channel)

    def filter_get(self):
        """ Returns the current filter channel"""
        return self.filter_control.get_state()

    def get_fl_image(self, exp, chnl, filepath=None):
        """ Returns brightfield and fluorescent images"""
        # Turn off the LED
        old_leds = self.led_control.channel_states.copy()
        for led in old_leds:
            if old_leds[led]:
                self.turn_off_led(led)
        # Stop continuous image
        self.stop_feed()
        time.sleep(0.2)
        # Adjust Exposure
        old_exp = self.get_exposure()
        self.set_exposure(exp)
        # Adjust Filter
        old_chnl = self.filter_get()
        self.filter_set(chnl)
        logging.info("Filter Set")
        time.sleep(1)
        # Adjust Shutter
        self.shutter_open()
        # Snap
        time.sleep((exp / 1000) + 0.5)
        # st = time.time()
        img = self.snap_image()
        if filepath:
            self.save_raw_image(filepath)
        # Close Shutter
        self.shutter_close()
        # Adjust Filter
        self.filter_set(old_chnl)
        # Start LED
        for led in old_leds:
            if old_leds[led]:
                self.turn_on_led(led)
        # Adjust Exposure
        self.set_exposure(old_exp)
        # Restart Live Feed
        self.start_feed()
        return self.get_raw_image()


class NikonTE3000(BaseSystem):
    system_id = 'NikonTE3000'
    _z_stage_com = "COM4"
    _outlet_com = "COM5"
    _objective_com = "COM3"
    _laser_com = "COM6"
    _pressure_com = "COM5"
    _daq_dev = "/Dev2/"
    _daq_current_readout = "ai0"
    _daq_voltage_readout = "ai1"
    _daq_voltage_control = 'ao1'
    _daq_rfu = "ai3"

    _z_stage_lock = threading.RLock()  # Same thread can access the lock at multiple points, but not multiple threads
    _outlet_lock = threading.RLock()
    _objective_lock = threading.Lock()
    _xy_stage_lock = threading.Lock()
    _pressure_lock = _outlet_lock
    _camera_lock = threading.RLock()
    _laser_lock = threading.Lock()
    _laser_poll_flag = threading.Event()
    _led_lock = _outlet_lock
    _laser_rem_time = 0
    laser_start_time = time.time()

    image_size = 0.5
    objective_focus = 0
    xy_stage_size = [112792, 64340]  # Rough size in mm
    xy_stage_offset = [0, 0]  # Reading on stage controller when all the way to left and up (towards wall)
    xy_stage_inversion = [1, 1]

    _focus_network = CENetworks.BarracudaFocusClassifier()
    _find_network = CENetworks.BarracudaCellDetector()

    def __init__(self):
        super(NikonTE3000, self).__init__()
        self.laser_max_time = 600

        self.hasCameraControl = True
        self.hasInletControl = True
        self.hasLaserControl = True
        self.hasObjectiveControl = True
        self.hasOutletControl = True
        self.hasVoltageControl = True
        self.hasPressureControl = True
        self.hasXYControl = True
        self.hasLEDControl = True

    def _start_daq(self):
        self.daq_board_control.max_time = 600000
        self.daq_board_control.start_read_task()

    def _poll_laser(self):
        while True:
            if self._laser_poll_flag.is_set():
                self._laser_rem_time = self.laser_max_time - (time.time() - self.laser_start_time)
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
        # Initialize all the motors independently
        zstage_thread = threading.Thread(target=self._start_zstage).start()
        outlet = threading.Thread(target=self._start_outlet)
        outlet.start()
        objective = threading.Thread(target=self._start_objective)
        objective.start()
        # Wait for motors to finish homing
        # zstage.join()
        outlet.join()
        objective.join()
        self.image_control = ImageControl.MicroControl(port=3121, lock=self._camera_lock)
        self.xy_stage_control = XYControl.PriorControl(lock=self._xy_stage_lock, com='COM4')
        self.daq_board_control = DAQControl.DAQBoard(dev=self._daq_dev, voltage_read=self._daq_voltage_readout,
                                                     current_read=self._daq_current_readout, rfu_read=self._daq_rfu,
                                                     voltage_control=self._daq_voltage_control)
        # self.laser_control = LaserControl.Laser(com=self._laser_com, lock=self._laser_lock, home=HOME)

        self.led_control = LightControl.CapillaryLED(com='COM9', arduino=self.outlet_control.arduino,
                                                     lock=self._led_lock)
        self._start_daq()

        self.pressure_control = PressureControl.PressureControl(com=self._pressure_com, lock=self._pressure_lock,
                                                                arduino=self.outlet_control.arduino, home=HOME)

    def _start_outlet(self):
        self.outlet_control = OutletControl.OutletControl(com=self._outlet_com, lock=self._outlet_lock, home=HOME,
                                                          invt=1)

    def _start_zstage(self):
        self.z_stage_control = ZStageControl.ThorLabs(lock=self._z_stage_lock)

    def _start_objective(self):
        self.objective_control = ObjectiveControl.ArduinoControl(com=self._objective_com, lock=self._objective_lock,
                                                                 home=HOME)

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

    def set_exposure(self, exp):
        with self._camera_lock:
            self.image_control.set_exposure(exp)
        return

    def get_exposure(self):
        with self._camera_lock:
            return self.image_control.get_exposure()

    def get_image(self):
        with self._camera_lock:
            image = self.image_control.get_recent_image(size=self.image_size)

            if image is None:
                return None
            if not HOME:
                self.image_control.save_image(image, "recentImg.png")
        return image

    def save_raw_image(self, filename):
        self.image_control.save_raw_image(filename)

    def close_image(self):
        self.image_control.close()
        self.image_control._close_client()
        return True

    def open_image(self):
        self.image_control.open()
        return True

    def start_feed(self):
        if self.camera_state():
            self.image_control.start_video_feed()
        return True

    def stop_feed(self):
        self.image_control.stop_video_feed()
        return True

    def save_buffer(self, folder, name, fps=5):
        """
        Saves the camera buffer to the folder as .avi file. Also copies sequence of images as reference.
        :param folder: folder to store data
        :param name: video file to save to, will overwrite existing files
        :param fps: frames per second to store the video at, defaults to 5 fps irregardless of camera frame rate
        :return: True
        """
        self.image_control.save_capture_sequence(folder, name, fps)
        return True

    def camera_state(self):
        """ Checks if camera resources are available"""
        return self.image_control.camera_state()

    def set_objective_home(self):
        """Sets the current position of the objective stage/motor as home. Return False if device is not capable."""
        self.objective_control.set_origin()
        return True

    def close_voltage(self):
        self.daq_board_control.change_voltage(0)

    def set_voltage(self, v=None):
        self._start_daq()
        self.daq_board_control.change_voltage(v)
        return True

    def save_data(self, filepath):
        try:
            self.daq_board_control.save_data(filepath)
        except FileNotFoundError:
            logging.info('File not selected')

        return True

    def get_voltage(self):
        return self.daq_board_control.voltage

    def get_voltage_data(self):
        return self.daq_board_control.data['ai1']

    def get_current_data(self):
        return self.daq_board_control.data['ai2']

    def get_rfu_data(self):
        return self.daq_board_control.data['ai3']

    def get_data(self):
        with self.daq_board_control.data_lock:
            rfu = self.daq_board_control.data['avg']
            volts = self.daq_board_control.data[self._daq_voltage_readout]
            current = self.daq_board_control.data[self._daq_current_readout]
        return {'rfu': rfu, 'volts': volts, 'current': current}

    def stop_voltage(self):
        self.daq_board_control.change_voltage(0)

    def set_laser_parameters(self, pfn=None, att=None, energy=None, mode=None, burst=None):
        if pfn:
            self.laser_control.set_pfn('{:03d}'.format(int(pfn)))

        if att:
            self.laser_control.set_attenuation('{:03d}'.format(int(att)))

        if energy:
            logging.info('Cannot set energy of laser currently.')

        if mode:
            self.laser_control.set_mode('0')
            self.laser_control.set_rep_rate('010')

        if burst:
            self.laser_control.set_burst('{:04d}'.format(int(burst)))

        return True

    def laser_standby(self):
        executed = self.laser_control.start()
        if executed:
            self._laser_poll_flag.set()

            self.laser_start_time = time.time()
            threading.Thread(target=self._poll_laser, daemon=True).start()
            logging.info('Laser on standby for {}s'.format(self.laser_max_time))

            return True

    def turn_on_led(self, channel='R'):
        self.led_control.start_led(channel)

    def turn_off_led(self, channel='R'):
        self.led_control.stop_led(channel)

    def turn_on_dance(self):
        threading.Thread(target=self.led_control.dance_party).start()

    def turn_off_dance(self):
        self.led_control.dance_stop.set()


# NEEDS:
# A motor for the outlet (don't really need encoder), and a z stage for the inlet and a
# pressure control device (preferably the same one used on the Barracuda system)
class OstrichSystem(BaseSystem):
    system_id = 'OSTRICH'

    _daq_dev = "/Dev1/"
    _daq_current_readout = "ai2"
    _daq_voltage_readout = "ai1"
    _daq_voltage_control = 'ao1'
    _daq_rfu = "ai3"
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


class CE_TiEclipseSeattle(BaseSystem):
    def __init__(self):
        super().__init__()

        # Hardware Class Objects: These are all (and should remain) the base classes
        self.xy_stage_control = XYControl.MicroControl()

        self.z_stage_control = ZStageControl.PowerStep(com="COM4", invt=-1, home_dir=False)
        self.outlet_control = OutletControl.ArduinoOutlet(com="COM5", invt=1, home_dir=True)
        self.objective_control = ObjectiveControl.MicroControl(mmc=self.xy_stage_control.mmc)
        self.power_supply_control = PowerSupplyControl.BertanSupply(channels=[0])
        configs = {'ai0': 'diff', 'ai1': "RSE", 'ai5': 'RSE'}
        self.adc_control = DAQControl.NI_ADC(mode="continuous", channels=['ai0', 'ai1', 'ai5'], configs=configs,
                                             sampling=80000, samples=10000)

        self._voltage_data=1
        self._current_data=2
        self._rfu_data=0
        self._voltage_conversion = 1/2.5*5000
        self._current_conversion = 1/2.5*(100*10**-6)

        self.daq_board_control = self.adc_control
        self.data_filter_control = DAQControl.Filter()
        self.image_control = ImageControl.MicroControl(mmc=None,
                                                       config_file=r"C:\Users\Luke\Desktop\Barracuda\BarracudaQt\config\hammatsu.cfg")
        self.laser_control = LaserControl.Laser()
        # These are shared resources for the outlet arduino
        arduino_1=self.outlet_control.arduino
        arduino_1_lock = self.outlet_control.lock
        self.pressure_control = PressureControl.ArduinoControl(arduino = arduino_1, lock=arduino_1_lock)
        self.led_control = LightControl.CapillaryLED(arduino=arduino_1, lock = arduino_1_lock)
        self.shutter_control = ScopeControl.ShutterControl()
        self.filter_control = ScopeControl.FilterMicroControl(mmc=self.xy_stage_control.mmc)

        # Start the processes needed
        self.adc_control.start()

    def get_voltage_data(self):
        """
        For the CE system we want to return the voltage column separately .

        """
        with self.adc_control.data_lock:
            data = self.adc_control.data[self._voltage_data].copy()
        data = data * self._voltage_conversion
        return data

    def get_current_data(self):
        """
        For the CE system we want to return the current column seperately
        """
        with self.adc_control.data_lock:
            data = self.adc_control.data[self._current_data].copy()
        data = data * self._current_conversion
        return data

    def get_rfu_data(self):
        """
        For the CE System we want to return the RFU column seperately
        :return:
        """
        with self.adc_control.data_lock:
            data = self.adc_control.data[self._rfu_data].copy()
        return data



class Chip_TiEclipseSeattle(BaseSystem):

    def __init__(self):
        super().__init__()

        #Setup Hardware The Microchip Will need to use:
        self.xy_stage_control = XYControl.MicroControl()
        self.objective_control = ObjectiveControl.MicroControl(mmc=self.xy_stage_control.mmc)
        self.filter_control = ScopeControl.FilterMicroControl(mmc=self.xy_stage_control.mmc)
        self.image_control = ImageControl.MicroControl(mmc=None,
                                                       config_file=r"C:\Users\Luke\Desktop\Barracuda\BarracudaQt\config\hammatsu.cfg")

        # ------------------------------- Power Supply setup --------------------------------
        # Power supply channels. Once inside the PowerSupply class we only care about
        # their order in this list. 0->index 0 2->index 1 4-> index 2 and 6-> index 3
        # Remember: Their order determines the channel.
        bertan_channels = [0, 2, 4, 6]  # Inside the powersupply, we care only about their index in this list
        self.power_supply_control = PowerSupplyControl.BertanSupply(channels=bertan_channels)
        configs = {'ai0': 'diff', 'ai14': "RSE", 'ai15': 'RSE'}

        # Setup ADC
        adc_channels = ['ai1', 'ai2', 'ai3', 'ai4', 'ai5', 'ai6', 'ai7', 'ai15']
        self.adc_control = DAQControl.NI_ADC(mode="continuous", channels=adc_channels,
                                             sampling=20000, samples=10000, output_data=100)

        # Create Dictionary to Help keep track of everything, only used to double check wiring:
        _wiring = {2: [0, 'ai1', 'ai5'],  # Electrode Channel 2
                   3: [2, 'ai2', 'ai6'],  # Electrode Channel 3
                   4: [4, 'ai3', 'ai7'],  # Electrode Channel 4
                   5: [6, 'ai4', 'ai15']}  # Electrode Channel 5

        self._voltage_chnls = [0, 4]
        self._voltage_conversion = 1 / 2.5 * 5000
        self._current_chnls = [4, 8]
        self._current_conversion = 1 / 2.5 * (100 * 10 ** -6)
        self.daq_board_control = self.adc_control
        self.data_filter_control = DAQControl.Filter()
        self.adc_control.start()



    def get_voltage(self):
        """
        For the microchip system we want to return the entire array of voltages and currents together.

        """
        with self.adc_control.data_lock:
            st, end = self._voltage_chnls
            data = self.adc_control.data[st:end].copy()
        data = data * self._voltage_conversion
        return data

    def get_current(self):
        """
        For the microchip system we want to return the entire array of voltages and currents together.
        """
        with self.adc_control.data_lock:
            st, end = self._current_chnls
            data = self.adc_control.data[st:end].copy()
        data = data * self._current_conversion
        return data


def test():
    hardware = CE_TiEclipseSeattle()
    return hardware


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    hardware = test()
