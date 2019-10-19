import datetime
import logging
import os
import pickle
import threading
import time
import numpy as np

from BarracudaQt import CESystems, CEObjects, Detection, Lysis

LYSIS_ADJUST = 0  # how far up or down to move the lysis laser
# For testing:
TEST_METHOD = r"C:\Users\NikonEclipseTi\Documents\Barracuda\BarracudaQt\Methods\Testing\SimpleAutoTest.met"

class RunMethod:
    _pause_flag = threading.Event()
    _stop_thread_flag = threading.Event()
    _inject_flag = threading.Event()
    _plot_data = threading.Event()
    _last_cell_positions = {'xy':None,'cap':None,'obj':None}  # xy, cap, obj are the keys
    step = {}  # Method dictionary
    save_dir = ""  # Directory where the runs will be saved
    step_id = 0  # which step we currently are running
    rep = 0  # What repetition we are on for the method
    method = CEObjects.Method(None, None)
    method_id = 0  # method id
    cell_finders = {}  # List of Focus Getters

    injection_wait = 6  # How long to wait after an injection for repeatable spontaneous fluid displacement

    def __init__(self, hardware, methods, repetitions, methods_id,
                 flags, insert, folder, cap_control):
        """
        Logic to run a CE run

        Includes methods for moving the various parts
        The logic method contains the logic, or sequence of events for each step
        Feel free to add or adjust any part of this and give it a test.

        :param hardware: CESystems object
        :param methods: CEObject.Method object
        :param repetitions: # of repetions for each method
        :param methods_id: int, method identification
        :param flags: list of control flags [pause, stop, inject, and plot]
        :param insert: CEObject.Insert object
        :param folder: string, will be prefix for data and folders
        :param cap_control: Lysis.CapillaryControl object
        """
        if hardware is None:
            hardware = CESystems.NikonEclipseTi()
        self.hardware = hardware
        self.methods = methods
        self.repetitions = repetitions
        self.methods_id = methods_id
        self._pause_flag = flags[0]
        self._stop_thread_flag = flags[1]
        self._inject_flag = flags[2]
        self._plot_data = flags[3]
        self.insert = insert
        self.folder = folder
        self.cap_control = cap_control

    def start_run(self):
        for self.method, self.method_id in zip(self.methods, self.methods_id):
            run_state = self.logic()
            if not run_state:
                logging.info('Run stopped.')
                self._stop_thread_flag.clear()
                return False
        logging.info('Sequence Completed.')
        return True

    def check_flags(self):
        """ Check if the user has requested the program to stop, or if we should continue"""
        while self._pause_flag.is_set():
            if self._stop_thread_flag.is_set():
                # self._plot_data.clear()
                return False
            if self._inject_flag.is_set():
                self.record_cell_info()
            self._plot_data.clear()
            time.sleep(0.2)
            continue
        if self._stop_thread_flag.is_set():
            self._plot_data.clear()
            return False
        self._plot_data.set()
        return True

    def record_cell_info(self):
        """ Record the capillary, stage, and objective position between runs"""
        xy = self.hardware.get_xy()
        cap = self.hardware.get_z()
        obj = self.hardware.get_objective()
        self._last_cell_positions['xy'] = xy
        self._last_cell_positions['cap'] = cap
        self._last_cell_positions['obj'] = obj
        return

    def move_inlet(self, inlet_travel):
        """ Move the inlet for the run method, wait till it has finished"""
        if self._stop_thread_flag.is_set():
            return
        self.hardware.set_z(inlet_travel)
        self.hardware.wait_z()
        return self.check_flags()

    def move_outlet(self, outlet_travel):
        """ Move the outlet for the run method"""
        if self._stop_thread_flag.is_set():
            return
        self.hardware.set_outlet(rel_h=outlet_travel)
        self.hardware.pressure_valve_close()  # Close pressure to prevent siphon injections
        self.hardware.wait_outlet()
        return self.check_flags()

    def move_objective(self, objective_position):
        if self._stop_thread_flag.is_set():
            return
        self.hardware.set_objective(objective_position)
        return self.check_flags()

    def move_xy_stage(self, inlet_location):
        if self._stop_thread_flag.is_set():
            return
        if inlet_location is None:
            logging.error('Unable to make next XY movement.')
            return False
        self.hardware.set_xy(xy=inlet_location)
        self.hardware.wait_xy()
        return self.check_flags()

    def wait_sleep(self, wait_time):
        """ Returns false if wait time was interupted by stop command"""
        start_time = time.time()
        while time.time() - start_time < wait_time and not self._stop_thread_flag.is_set():
            time.sleep(0.05)

        if self._stop_thread_flag.is_set():
            logging.warning("CE Run Stopped during Separation")
            return False
        return True

    def separate(self):
        if self._stop_thread_flag.is_set():
            return
        voltage_level = None
        pressure_state = None

        if self.step['SeparationTypeVoltageRadio']:
            voltage_level = float(self.step['ValuesVoltageEdit'])
        elif self.step['SeparationTypeCurrentRadio']:
            logging.error('Unsupported: Separation with current')
            return False
        elif self.step['SeparationTypePowerRadio']:
            logging.error('Unsupported: Separation with power')
            return False

        # Give user option to run combo of pressure and voltage
        if self.step['SeparationTypePressureRadio']:
            pressure_state = True
        elif self.step['SeparationTypeVacuumRadio']:
            logging.error('Unsupported: Separation with vacuum')
            return False

        if self.step['SeparationTypeWithPressureCheck']:
            pressure_state = True
        elif self.step['SeparationTypeWithVacuumCheck']:
            logging.error('Unsupported: Separation with vacuum.')
            return False

        duration = float(self.step['ValuesDurationEdit'])

        if voltage_level:
            self.hardware.set_voltage(voltage_level)
        if pressure_state:
            self.hardware.pressure_rinse_start()

        state = self.wait_sleep(duration)
        # Save Data
        now = datetime.datetime.now()
        file_name = "{}_{}_self.step_{}_rep_{}.csv".format(self.folder, self.method_id, self.step_id, self.rep)
        save_path = os.path.join(self.save_dir, file_name)
        self.hardware.save_data(save_path)
        self.hardware.set_voltage(0)
        self.hardware.pressure_rinse_stop()

        return state

    def rinse(self):
        if self._stop_thread_flag.is_set():
            return
        pressure_state = None
        if self.step['PressureTypePressureRadio']:
            pressure_state = True
        elif self.step['PressureTypeVacuumRadio']:
            logging.error('Unsupported: Rinsing with vacuum.')
            return False

        duration = float(self.step['ValuesDurationEdit'])

        if pressure_state:
            self.hardware.pressure_rinse_start()

        time.sleep(duration)
        self.hardware.pressure_rinse_stop()

        return True

    def cell_move(self):
        if self._stop_thread_flag.is_set():
            return
        # If wells are the same move back one.
        if self._inject_flag.is_set():
            return False
        xy = self._last_cell_positions['xy']
        if xy is not None:
            self.move_xy_stage(xy)

            cap = self._last_cell_positions['cap']
            if cap is not None:
                self.hardware.set_z(cap)

            obj = self._last_cell_positions['obj']
            if cap is not None:
                self.move_objective(obj)
                time.sleep(2)

    def auto_cell(self):
        """ Move cell to last position,
            Find and Focus a Cell
            (Start loading that cell)
            Lyse that cell
            Load the cell
            Finish
        """
        self.cell_move()
        if self.step_id not in self.cell_finders.keys():
            center = self.insert.get_well_xy(self.step['Inlet'])
            mov = Detection.Mover(center=center)
            # fixme: Hey so 0.4329 and (235,384) are they pixel to um conversion and laser location on the image
            # These will need to be adjusted for each system
            laser_spot = (235, 384)
            det = Detection.CellDetector(self.hardware, 0.4329, laser_spot)
            fc = Detection.FocusGetter(det, mov, laser_spot)
            self.cell_finders[self.step_id] = [det, fc, mov]

            # We need to create a focal plane at the start of the method:
            logging.info("Pausing Run...For now...")
            logging.info("Please bring 3 cells into focus at 3 corners of the well")
            logging.info("Press 'Start' after a cell is into focus")
            for i in range(3):
                logging.info("Focus Point #{}".format(i + 1))
                self._pause_flag.set()
                state = self.check_flags()
                if not state:
                    return state
                fc.add_focus_point()
            fc.find_a_plane()

        else:
            _, fc, _ = self.cell_finders[self.step_id]
        logging.info("Finding a cell, press pause to manually find a cell")
        fc.find_plane_focus(self._pause_flag)
        state = self.check_flags()

        # Lower the Capillary
        get_focus = self.cap_control.move_cap_above_cell()
        if not get_focus:
            self._pause_flag.set()
            logging.info("Bring Capillary into the correct position and record its location")
            logging.info("Press Start to Continue...")
            state = self.check_flags()
            if not state:
                return state
        self.hardware.wait_z()

        # Adjust the focal plane for lysis
        self.hardware.set_objective(rel_h=LYSIS_ADJUST)
        return state

    def semi_auto_cell(self):
        """ Move the cell to the last  position and start"""
        self.cell_move()
        self._inject_flag.set()
        return True

    def inject(self):
        st=time.time()
        logging.info("Starting Injection {}".format(time.time()-st))
        if self._stop_thread_flag.is_set():
            return
        pressure_state = False
        voltage_level = None

        if self.step['InjectionTypeVoltageRadio']:
            voltage_level = float(self.step['ValuesVoltageEdit'])
        elif self.step['InjectionTypePressureRadio']:
            pressure_state = True
        elif self.step['InjectionTypeVacuumRadio']:
            logging.error('Unsupported: Injection with vacuum.')
            return False

        duration = float(self.step['ValuesDurationEdit'])
        lyse = False
        if self.step['SingleCell']:
            if self.step['AutoSingleCell']:
                logging.info("Automated single cell....")
                lyse = self.auto_cell()
            else:
                self.semi_auto_cell()
                logging.info('Run is paused. Locate and lyse cell.')
                self._pause_flag.set()
                state_n = self.check_flags()
                if not state_n:
                    return False

        # Open the outlet to outside air or apply a pressure
        if pressure_state:
            self.hardware.pressure_rinse_start()
        else:
            self.hardware.pressure_rinse_stop()
        if voltage_level:
            self.hardware.set_voltage(voltage_level)
        time.sleep(0.5)
        # Fire the laser half a second after starting the load velocity
        if lyse:
            self.hardware.laser_fire()
        time.sleep(duration)
        self.hardware.set_objective(rel_h = -1000)
        self.hardware.set_voltage(0)
        self.hardware.pressure_rinse_stop()

        # Record buffer of injection after lysis.

        if self.step['SingleCell']:
            file_name = "{}_{}_step{}_rep{}".format(self.folder, self.method_id, self.step_id, self.rep)
            save_path = os.path.join(self.save_dir, file_name)
            threading.Thread(target =  self.hardware.save_buffer, args = (save_path, 'cell_lysis.avi')).start()
        self.hardware.objective_control.wait_for_move()

        return True

    def create_run_folder(self):
        cwd = os.getcwd()
        now = datetime.datetime.now()
        folder_name = self.folder + now.strftime("RunData__%Y_%m_%d__%H_%M_%S")
        save_dir = os.path.join(cwd, 'Data', folder_name)
        try:
            os.makedirs(save_dir, exist_ok=True)
            return save_dir
        except FileExistsError:
            return save_dir

    def logic(self):
        self.save_dir = self.create_run_folder()

        for self.rep in range(self.repetitions):
            state = self.check_flags()
            if not state:
                return False
            previous_step = None
            self._inject_flag.clear()
            for step_id, self.step in enumerate(self.method.steps):
                if 'Type' in self.step.keys():
                    logging.info('{} Step: {}'.format(self.step['Type'], self.step['Summary']))
                    state = self.check_flags()
                    if not state:
                        return False
                    step_start = time.time()

                    state = self.move_inlet(0.25)

                    if not state:
                        return False

                    try:
                        cycles = int(self.step['TrayPositionsIncrementEdit'])
                    except ValueError:
                        state = self.move_xy_stage(self.insert.get_well_xy(self.step['Inlet']))
                    else:
                        if self.rep + 1 > cycles:
                            state = self.move_xy_stage(
                                self.insert.get_next_well_xy(self.step['Inlet'], int(np.floor(self.rep / cycles))))
                        else:
                            state = self.move_xy_stage(self.insert.get_well_xy(self.step['Inlet']))
                    if not state:
                        return False

                    if previous_step == 'Inject' and time.time() - step_start < self.injection_wait:
                        time.sleep(abs(self.injection_wait - (time.time() - step_start)))
                        state = self.check_flags()
                        if not state:
                            return False

                    state = self.move_outlet(self.step['OutletTravel'])
                    if not state:
                        return False

                    state = self.move_inlet(self.step['InletTravel'])
                    if not state:
                        return False

                    if self.step['Type'] == 'Separate':
                        executed = self.separate()
                        if not executed:
                            return False

                    elif self.step['Type'] == 'Rinse':
                        executed = self.rinse()
                        if not executed:
                            return False

                    elif self.step['Type'] == 'Inject':
                        executed = self.inject()

                        if not executed:
                            return False

                    logging.info('Step completed.')

                    previous_step = self.step['Type']
        return True


def test_run(hardware):
    fin = open(TEST_METHOD,'rb')
    data = pickle.load(fin)
    insert = data.insert
    cap_control = Lysis.CapillaryControl(hardware)
    flags = [threading.Event() for i in range(4)]
    rm = RunMethod(hardware,[data],3,[0],flags,insert,'testing',cap_control)
    return rm

def start_run(rm):
    threading.Thread(target = rm.start_run).start()


if __name__ == "__main__":
    hardware = CESystems.NikonEclipseTi()
    rm = test_run(hardware)
    hardware.start_system()
    hardware.image_control.live_view()
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

