# Standard library modules
import threading
import logging
import time

# Custom Hardware Modules
import DAQControl
import ImageControl
import OutletControl
import XYControl
import ZStageControl
import ObjectiveControl
import LaserControl
import PressureControl


HOME = False


class BaseSystem:
    _system_id = None

    def __init__(self):
        self.z_stage_control = None
        self.outlet_control = None
        self.objective_control = None
        self.image_control = None
        self.xy_stage_control = None
        self.daq_board_control = None
        self.laser_control = None
        self.pressure_control = None

        self.laser_max_time = None

    def start_system(self):
        """Puts the system into its functional state."""
        pass

    def close_system(self):
        """Takes system out of its functional state."""
        pass

    def close_xy(self):
        """Removes immediate functionality of XY stage."""
        pass

    def set_xy(self, xy=None, rel_xy=None):
        """Sets the position of the XY Stage. 'xy' is absolute, 'rel_xy' is relative to current."""
        pass

    def get_xy(self):
        """Gets the current position of the XY stage."""
        pass

    def stop_xy(self):
        """Stops current movement of the XY stage."""
        pass

    def set_xy_home(self):
        """Sets the current position of XY stage as home. Return False if device has no 'home' capability."""
        pass

    def home_xy(self):
        """Goes to current position marked as home. Return False if device has no 'home' capability."""
        pass

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

    def set_z_home(self):
        """Sets the current position of the Z stage/motor as home. Return False if device has no 'home' capability."""
        pass

    def home_z(self):
        """Goes to current position marked as home. Return False if device has no 'home' capability."""
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

    def set_outlet_home(self):
        """Sets the current position of the outlet stage/motor as home. Return False if device is not capable."""
        pass

    def home_outlet(self):
        """Goes to the current position marked as home. Return False if device has no 'home' capability."""
        pass

    def close_objective(self):
        """Removes immediate functionality of the objective stage/motor."""
        pass

    def set_objective(self, h=None, rel_h=None):
        """Sets the position of the objective stage/motor. 'h' is absolute, 'rel_h' is relative to current."""
        pass

    def get_objective(self):
        """Gets the current position of the objective stage/motor."""
        pass

    def stop_objective(self):
        """Stops the current movement of the objective stage/motor."""
        pass

    def set_objective_home(self):
        """Sets the current position of the objective stage/motor as home. Return False if device is not capable."""
        pass

    def home_objective(self):
        """Goes to the current position marked as home. Return False if device has no 'home' capability."""
        pass

    def close_voltage(self):
        """Removes immediate functionality of the voltage source."""
        pass

    def set_voltage(self, v=None):
        """Sets the current voltage of the voltage source."""
        pass

    def get_voltage(self):
        """Gets the current voltage of the voltage source."""
        pass

    def get_voltage_data(self):
        """Gets a list of the voltages over time."""
        pass

    def get_current_data(self):
        """Gets a list of the current over time."""
        pass

    def get_rfu_data(self):
        """Gets a list of the RFU over time."""
        pass

    def close_image(self):
        """Removes the immediate functionality of the camera."""
        pass

    def start_feed(self):
        """Sets camera to start gathering images. Does not return images."""
        pass

    def stop_feed(self):
        """Stops camera from gathering images."""
        # Only fill out stop_feed if you can fill out start_feed.
        pass

    def get_image(self):
        """Returns the most recent image from the camera."""
        pass

    def set_laser_parameters(self, pfn=None, att=None, energy=None, mode=None, burst=None):
        """Sets the parameters of the laser device."""
        pass

    def laser_standby(self):
        """Puts laser in a standby 'fire-ready' mode."""
        pass

    def laser_fire(self):
        """Fires the laser."""
        pass

    def laser_stop(self):
        """Stops current firing of the laser."""
        pass

    def laser_close(self):
        """Removes immediate functionality of the laser."""
        pass

    def laser_check(self):
        """Logs status of laser system."""
        pass

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


class BarracudaSystem(BaseSystem):
    _system_id = 'BARRACUDA'

    _z_stage_com = "COM4"
    _outlet_com = "COM7"
    _objective_com = "COM8"
    _laser_com = "COM6"
    _pressure_com = "COM7"
    _daq_dev = "/Dev1/"
    _z_stage_lock = threading.Lock()
    _outlet_lock = threading.Lock()
    _objective_lock = threading.Lock()
    _xy_stage_lock = threading.Lock()
    _pressure_lock = threading.Lock()
    _camera_lock = threading.Lock()
    _laser_lock = threading.Lock()
    _laser_poll_flag = threading.Event()
    _laser_rem_time = 0

    xy_stage_size = [112792, 64340]  # Rough size in mm
    xy_stage_upper_left = [112598, -2959]  # Reading on stage controller when all the way to left and up (towards wall)
    xy_stage_inversion = [-1, -1]

    def __init__(self):
        super(BarracudaSystem, self).__init__()
        self.laser_max_time = 600

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

    def start_system(self):
        self.z_stage_control = ZStageControl.ZStageControl(com=self._z_stage_com, lock=self._z_stage_lock, home=HOME)
        self.outlet_control = OutletControl.OutletControl(com=self._outlet_com, lock=self._outlet_lock, home=HOME)
        self.objective_control = ObjectiveControl.ObjectiveControl(com=self._objective_com, lock=self._objective_lock, home=HOME)
        # self.image_control = ImageControl.ImageControl(home=HOME)
        self.xy_stage_control = XYControl.XYControl(lock=self._xy_stage_lock, stage='XYStage', config_file='PriorXY.cfg', home=HOME)
        self.daq_board_control = DAQControl.DAQBoard(dev=self._daq_dev)
        self.laser_control = LaserControl.Laser(com=self._laser_com, lock=self._laser_lock, home=HOME)
        self.pressure_control = PressureControl.PressureControl(com=self._pressure_com, lock=self._pressure_lock, arduino=self.outlet_control.arduino, home=HOME)

        self._start_daq()
        pass

    def close_system(self):
        pass

    def get_image(self):
        with self._camera_lock:
            image = self.image_control.get_recent_image(size=(512, 384))

            if image is None:
                return None

            if not HOME:
                image.save("recentImg.png")

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
            return True

        elif rel_xy:
            self.xy_stage_control.set_rel_xy(rel_xy)
            return True

        return False

    def get_xy(self):
        return self.xy_stage_control.read_xy()

    def stop_xy(self):
        self.xy_stage_control.stop()
        return True

    def set_xy_home(self):
        """Sets the current position of XY stage as home. Return False if device has no 'home' capability."""
        pass

    def home_xy(self):
        """Goes to current position marked as home. Return False if device has no 'home' capability."""
        pass

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
        pass

    def home_z(self):
        """Goes to current position marked as home. Return False if device has no 'home' capability."""
        pass

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
        pass

    def home_outlet(self):
        """Goes to the current position marked as home. Return False if device has no 'home' capability."""
        pass

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
        pass

    def home_objective(self):
        """Goes to the current position marked as home. Return False if device has no 'home' capability."""
        pass

    def close_voltage(self):
        pass

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
            self.laser_control.set_pfn('{:03d}'.format(pfn))

        if att:
            self.laser_control.set_attenuation('{:03d}'.format(att))

        if energy:
            logging.info('Cannot set energy of laser currently.')

        if mode:
            logging.info('Cannot set mode of laser currently.')

        if burst:
            self.laser_control.set_burst('{:04d}'.format(burst))

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


class FinchSystem(BaseSystem):
    def __init__(self):
        super(FinchSystem, self).__init__()


class OstrichSystem(BaseSystem):
    _xy_stage_lock = threading.Lock()

    def __init__(self):
        super(OstrichSystem, self).__init__()
        self.xy_stage_control = XYControl.XYControl(lock=self._xy_stage_lock, stage='TIXYDrive', config_file='sysConfig.cfg', home=HOME)

    def start_system(self):
        """Puts the system into its functional state."""
        pass

    def close_system(self):
        """Takes system out of its functional state."""
        pass

    def close_xy(self):
        """Removes immediate functionality of XY stage."""
        pass

    def set_xy(self, xy=None, rel_xy=None):
        """Sets the position of the XY Stage. 'xy' is absolute, 'rel_xy' is relative to current."""
        pass

    def get_xy(self):
        """Gets the current position of the XY stage."""
        pass

    def stop_xy(self):
        """Stops current movement of the XY stage."""
        pass

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
        pass

    def set_objective(self, h=None, rel_h=None):
        """Sets the position of the objective stage/motor. 'h' is absolute, 'rel_h' is relative to current."""
        pass

    def get_objective(self):
        """Gets the current position of the objective stage/motor."""
        pass

    def stop_objective(self):
        """Stops the current movement of the objective stage/motor."""
        pass

    def close_voltage(self):
        """Removes immediate functionality of the voltage source."""
        pass

    def set_voltage(self, v=None):
        """Sets the current voltage of the voltage source."""
        pass

    def get_voltage(self):
        """Gets the current voltage of the voltage source."""
        pass

    def get_voltage_data(self):
        """Gets a list of the voltages over time."""
        pass

    def get_current_data(self):
        """Gets a list of the current over time."""
        pass

    def get_rfu_data(self):
        """Gets a list of the RFU over time."""
        pass

    def close_image(self):
        """Removes the immediate functionality of the camera."""
        pass

    def start_feed(self):
        """Sets camera to start gathering images. Does not return images."""
        pass

    def stop_feed(self):
        """Stops camera from gathering images."""
        # Only fill out stop_feed if you can fill out start_feed.
        pass

    def get_image(self):
        """Returns the most recent image from the camera."""
        pass

    def set_laser_parameters(self, pfn=None, att=None, energy=None, mode=None, burst=None):
        """Sets the parameters of the laser device."""
        pass

    def laser_standby(self):
        """Puts laser in a standby 'fire-ready' mode."""
        pass

    def laser_fire(self):
        """Fires the laser."""
        pass

    def laser_stop(self):
        """Stops current firing of the laser."""
        pass

    def laser_close(self):
        """Removes immediate functionality of the laser."""
        pass

    def laser_check(self):
        """Logs status of laser system."""
        pass

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