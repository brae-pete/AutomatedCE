import CESystems
import time
import datetime
import threading
import logging
import os
import numpy as np


class CE_Run:
    """
    Controls the running of CE methods. In addition to a method, requires a CESytems object

    Logic behind how the Run is controlled and in what order the actions take place is given
    in the run_logic method.


    """
    stop_events = []  # List of threading.event objects
    pause_flag = []  # flag to pause the run
    inject_flag = threading.Event()
    _last_cell_positions = {'xy': []}
    step = {}
    save_dir = os.path.join(os.pardir, 'Data')
    stop_idx = None
    injection_wait = 7

    def __init__(self, hardware):
        self.hardware = hardware

    def load_method(self, method_file_path):
        pass

    def wait_duration(self, stop, duration):
        """ Waits specified time while checking the stop event for the current method/run
        
        stop: threading.event() that corresponds to the current run
        duration: time in s to wait 
        """

        st = time.time()

        while time.time() - st < duration:
            time.sleep(0.05)
            # Quit if stop has been triggered
            if stop.is_set():
                return False
        return True

    def check_flags(self, stop):
        # Loop while paused, check stop flag
        while self.pause_flag.is_set():
            if stop.is_set():
                return False
            if self.inject_flag:
                self.record_cell_info()
            time.sleep(0.1)
        return True

    def start_run(self, steps):
        pass

    def move_inlet(self, inlet_travel, stop):
        if stop.is_set():
            return
        self.hardware.set_z(inlet_travel)
        self.hardware.wait_z()
        return self.check_flags(stop)

    def move_outlet(self, outlet_travel, stop):
        if stop.is_set():
            return
        self.hardware.set_outlet(rel_h=outlet_travel)

        time.sleep(2)
        return self.check_flags(stop)

    def move_objective(self, objective_position, stop):
        if stop.is_set():
            return
        self.hardware.set_objective(objective_position, stop)
        return self.check_flags(stop)

    def move_xy_stage(self, inlet_location, stop):
        if stop.is_set():
            return
        if inlet_location is None:
            logging.error('Unable to make next XY movement.')
            return False
        self.hardware.set_xy(xy=inlet_location)
        time.sleep(2)
        return self.check_flags(stop)

    def separate(self, stop):
        if stop.is_set():
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

        time.sleep(duration)
        # Save Data
        file_name = "Separation_step{}_Rep{}.csv".format(self.step_id, self.rep)
        save_path = os.path.join(self.save_dir, file_name)
        self.hardware.save_data(save_path)
        self.hardware.set_voltage(0)
        self.hardware.pressure_rinse_stop()

        return True

    def rinse(self, stop):
        if stop.is_set():
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

    def semi_auto_cell(self, stop):
        if stop.is_set():
            return
        # If wells are the same move back one.
        if self.inject_flag.is_set():
            return False
        xy = self._last_cell_positions['xy']
        if xy is not None:
            self.move_xy_stage(xy,stop)

            cap = self._last_cell_positions['cap']
            if cap is not None:
                self.move_inlet(cap, stop)

            obj = self._last_cell_positions['obj']
            if cap is not None:
                self.move_objective(obj, stop)
        self.inject_flag.set()
        return True

    def inject(self, stop):
        if stop.is_set():
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

        if self.step['SingleCell']:
            if self.step['AutoSingleCell']:
                logging.info('Focusing, locating and lysing cell.')
                pass
            else:
                state_n =self.semi_auto_cell()
                logging.info('Run is paused. Locate and lyse cell.')
                if not state_n:
                    return
                self.pause_flag.set()
                state_n = self.check_flags()
                if not state_n:
                    return False
                else:

                    self.hardware.set_objective(rel_h=-1500)
                    self.hardware.objective_control.wait_for_move()

        if pressure_state:
            self.hardware.pressure_rinse_start()

        if voltage_level:
            self.hardware.set_voltage(voltage_level)

        time.sleep(duration)
        self.hardware.set_voltage(0)
        self.hardware.pressure_rinse_stop()

        return True

    def create_run_folder(self, stop):
        cwd = os.getcwd()
        now = datetime.datetime.now()
        save_dir = os.path.join(cwd, 'Data', now.strftime("RunData__%Y_%m_%d__%H_%M_%S"))
        try:
            os.makedirs(save_dir, exist_ok=True)
            return save_dir
        except FileExistsError:
            return save_dir

    save_dir = create_run_folder()

    def run_logic(self, method, repetitions, stop):

        for rep in range(repetitions):
            if self._stop_thread_flag.is_set():
                return
            previous_step = None
            self._inject_flag.clear()
            for step_id, step in enumerate(method.steps):
                if 'Type' in step.keys():
                    logging.info('{} Step: {}'.format(step['Type'], self.step['Summary']))
                    state = self.check_flags(stop)
                    if not state:
                        return False
                    step_start = time.time()

                    state = self.move_inlet(0.25, stop)

                    if not state:
                        return False

                    try:
                        cycles = int(step['TrayPositionsIncrementEdit'])
                    except ValueError:
                        state = self.move_xy_stage(self.insert.get_well_xy(step['Inlet']), stop)
                    else:
                        if rep + 1 > cycles:
                            state = self.move_xy_stage(
                                self.insert.get_next_well_xy(step['Inlet'], int(np.floor(rep / cycles))), stop)
                        else:
                            state = self.move_xy_stage(self.insert.get_well_xy(step['Inlet']), stop)
                    if not state:
                        return False

                    if previous_step == 'Inject' and time.time() - step_start < self.injection_wait:
                        time.sleep(abs(self.injection_wait - (time.time() - step_start)))
                        state = self.check_flags(stop)
                        if not state:
                            return False

                    state = self.move_outlet(step['OutletTravel'], stop)
                    if not state:
                        return False

                    state = self.move_inlet(step['InletTravel'], stop)
                    if not state:
                        return False

                    if self.step['Type'] == 'Separate':
                        executed = self.separate(stop)
                        if not executed:
                            return False

                    elif self.step['Type'] == 'Rinse':
                        executed = self.rinse(stop)
                        if not executed:
                            return False

                    elif self.step['Type'] == 'Inject':
                        executed = self.inject(stop)
                        if not executed:
                            return False

                    logging.info('Step completed.')
                    previous_step = self.step['Type']
        return True
