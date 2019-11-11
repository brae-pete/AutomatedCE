import datetime
import logging
import os
import pickle
import threading
import time
import numpy as np
import pandas as  pd

try:
    from BarracudaQt import CESystems, CEObjects, Detection, Lysis
except ModuleNotFoundError:
    import CESystems, CEObjects, Detection, Lysis

LYSIS_ADJUST = 0  # how far up or down to move the lysis laser
# For testing:
TEST_METHOD = r"C:\Users\NikonEclipseTi\Documents\Barracuda\BarracudaQt\Methods\Testing\SimpleAutoTest.met"


class RunMethod:
    """
    Logic behind running an automated CE Method.
    Feel free to change the logic method which contains the order of events for a given step.
    You can test out changes by Loading the GUI, then under system tab pressing the Detection button to reload
    all your changes to RunMethod.py and Detection.py. The next method you run will have reloaded RunMethod and Detection.py
    modules.
    """
    _pause_flag = threading.Event()
    _stop_thread_flag = threading.Event()
    _inject_flag = threading.Event()
    _plot_data = threading.Event()
    _last_cell_positions = {'xy': None, 'cap': None, 'obj': None}  # xy, cap, obj are the keys
    step = {}  # Method dictionary
    save_dir = ""  # Directory where the runs will be saved
    step_id = 0  # which step we currently are running
    rep = 0  # What repetition we are on for the method
    method = CEObjects.Method(None, None)
    method_id = 0  # method id
    cell_finders = {}  # List of Focus Getters
    collection_well = -1
    injection_wait = 6  # How long to wait after an injection for repeatable spontaneous fluid displacement
    sequence_id = round(time.time()) # Time in s from epoch, that links a repetitions in a sequence

    def __init__(self, hardware, methods, repetitions, methods_id,
                 flags, insert, folder, cap_control, cellfinders):
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
        self._collection_flag = flags[4]
        self.collection_well_lock = threading.Lock()
        self.insert = insert
        self.folder = folder
        self.cap_control = cap_control
        self.cell_finders = cellfinders

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

    def move_inlet(self, inlet_travel, wait = True):
        """ Move the inlet for the run method, wait till it has finished"""
        if self._stop_thread_flag.is_set():
            return
        self.hardware.set_z(inlet_travel)
        if wait:
            self.hardware.wait_z()
        return self.check_flags()

    def move_outlet(self, outlet_travel, wait = True):
        """ Move the outlet for the run method"""
        if self._stop_thread_flag.is_set():
            return
        self.hardware.set_outlet(rel_h=outlet_travel)
        self.hardware.pressure_valve_close()  # Close pressure to prevent siphon injections
        if wait:
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
        file_name = self.get_save_path(suffix='.csv')
        save_path = os.path.join(self.save_dir, file_name)
        try:
            self.hardware.save_data(save_path)
        except IndexError:
            logging.error("Index Error on DAQ")
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
        try:
            duration = float(self.step['ValuesDurationEdit'])
        except ValueError:
            logging.error("Duration was not set correctly: {}".format(self.step['ValuesDurationEdit']))
        if pressure_state:
            self.hardware.pressure_rinse_start()

        time.sleep(duration)
        self.hardware.pressure_rinse_stop()

        return True

    def cell_move(self, semi=True):
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
                #self.hardware.set_z(cap)
                pass
            obj = self._last_cell_positions['obj']
            if obj is not None and semi:
                self.move_objective(obj)
                time.sleep(10)

    def auto_cell(self):
        """ Move cell to last position,
            Find and Focus a Cell
            (Start loading that cell)
            Lyse that cell
            Load the cell
            Finish
        """

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
            self.current_fc = fc

        else:
            _, fc, _ = self.cell_finders[self.step_id]
            self.current_fc = fc

        logging.info("Finding a cell, press pause to manually find a cell")

        self.hardware.set_objective(h=fc.last_z)

        logging.info("Moving Objective into Focus")
        while np.abs(self.hardware.get_objective() - fc.last_z) > 5:
            time.sleep(0.5)
        logging.info("Pausing Run... Allow the program to find a cell.\n "
                     "When a cell is found focus the cell manually \n"
                     "Press Start when finished \n ")
        self._pause_flag.set()
        # Move the objective into position
        fc.quickcheck([1,500])
        state = self.check_flags()
        # Take a Snapshot
        if not self.step['Video']:
            logging.info("Taking Brightfield image...")
            # Take a Brightfield Picture
            savepath= self.get_save_path(prefix='BF',suffix='.tiff')
            self.hardware.save_raw_image(savepath)
        if self.step['FluorSnap']:
            logging.info("Taking Fluorescent image...")
            # Take a Fluorescence Picture
            # Stop Live Feed
            self.hardware.stop_feed()
            # Adjust Exposure
            old_exp = self.hardware.get_exposure()
            exp = self.step['Exposure']
            self.hardware.set_exposure(exp)
            # Adjust Filter
            old_chnl = self.hardware.filter_get()
            chnl = self.step['FilterChannel']
            self.hardware.filter_set(chnl)
            logging.info("Filter Set")
            time.sleep(1)
            # Turn off the LED
            old_leds = self.hardware.led_control.channel_states.copy()
            for led in old_leds:
                if old_leds[led]:
                    self.hardware.turn_off_led(led)

            # Adjust Shutter
            self.hardware.shutter_open()
            time.sleep(0.2)
            # Snap
            filepath = self.get_save_path(prefix='FL', suffix='.tiff')
            time.sleep((exp / 1000) + 0.5)
            #st = time.time()
            self.hardware.snap_image()

            self.hardware.save_raw_image(filepath)

            """            self.hardware.snap_image()
            st = time.time()
            while time.time() - st < exp / 1000:
                time.sleep(exp / 10000)
            self.hardware.save_raw_image(filepath)"""
            # Close Shutter
            self.hardware.shutter_close()
            # Start LED
            for led in old_leds:
                if old_leds[led]:
                    self.hardware.turn_on_led(led)
            # Adjust Filter
            self.hardware.filter_set(old_chnl)
            # Adjust Exposure
            self.hardware.set_exposure(100)
            # Restart Live Feed
            self.hardware.start_feed()

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
        return state

    def semi_auto_cell(self):
        """ Move the cell to the last  position and start"""
        self.cell_move()
        self._inject_flag.set()
        return True

    def inject(self):

        st = time.time()
        logging.info("Starting Injection {}".format(time.time() - st))
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
        # repeat the following until the user says a cell is loaded
        loading_cell = True
        while loading_cell:
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
            else:
                loading_cell = False
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
            self.wait_sleep(0.5)

            # Fire the laser half a second after starting the load velocity
            if lyse:
                self.hardware.laser_fire()

            state = self.wait_sleep(duration)
            if not state:
                return state

            self.hardware.set_voltage(0)
            if self.step['SingleCell']:
                # Move the capillary up to see if it was successful
                self.hardware.set_z(z=1)
                logging.info("If a cell did not lyse, press Pause within 5 seconds... ")
                state = self.wait_sleep(5)
                if not state:
                    return state
                if self._pause_flag.is_set():
                    loading_cell = True
                else:
                    loading_cell = False
                    self.hardware.set_objective(h=50)
                    self.hardware.pressure_rinse_stop()
                self._pause_flag.clear()
            # Move then objective down

            self.hardware.pressure_rinse_stop()
            # Take a picture if we are in single cell mode
            if self.step['SingleCell']:
                # Record buffer of injection after lysis.
                if self.step['Video']:
                    save_path = self.get_save_path()
                    threading.Thread(target=self.hardware.save_buffer, args=(save_path, 'cell_lysis.avi')).start()
                else:
                    logging.info("Taking Brightfield image...")
                    # Take a Brightfield Picture
                    savepath = self.get_save_path(prefix='Post_BF', suffix='.tiff')
                    self.hardware.save_raw_image(savepath)
            self.hardware.objective_control.wait_for_move()
            state_n = self.check_flags()
            if not state_n:
                return False
        return True

    def get_save_path(self, prefix='',suffix=''):
        file_name = "{}{}_{}_step{}_rep{}{}".format(self.folder,prefix, self.sequence_id, self.step_id, self.rep,suffix)
        return os.path.join(self.save_dir, file_name)

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
    def move_wells(self):
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
        return state
    def logic(self):
        self.save_dir = self.create_run_folder()
        for self.rep in range(self.repetitions):
            state = self.check_flags()
            if not state:
                return False
            previous_step = None
            self._inject_flag.clear()
            self.sequence_id = round(time.time())
            for self.step_id, self.step in enumerate(self.method.steps):
                if 'Type' in self.step.keys():
                    logging.info('{} Step: {}'.format(self.step['Type'], self.step['Summary']))
                    state = self.check_flags()
                    if not state:
                        return False
                    step_start = time.time()
                    state = self.move_inlet(self.step['InletTravel'], wait = True)
                    if not state:
                        return False
                    state = self.move_outlet(self.step['OutletTravel'], wait=False)
                    if not state:
                        return False

                    self.hardware.wait_z()
                    state = self.check_flags()
                    if not state:
                        return False

                    # Sometimes we move other places than the center of a well
                    # If this is a collection step move to a special vial if requested (flag is set),
                    # otherwise normal move
                    if self.step['Type']=='Separate' and self._collection_flag.is_set() :
                        # Only move if this is a collection separation and the well is within range
                        if self.step['CollectionSep'] and -1 < self.collection_well < len(self.insert.wells)-1 :
                            xy = self.insert.wells[self.collection_well].location
                            state = self.move_xy_stage(xy)
                        else:
                            state = self.move_wells()
                    # if this is a single cell injection step, we need to try and move to the last place we were
                    elif self.step['Type']=='Injection':
                        if self.step['SingleCell']:
                            self.cell_move(semi=False)
                            state = self.check_flags()
                        else:
                            state = self.move_wells()
                    else:
                        state = self.move_wells()

                    if not state:
                        return False

                    if previous_step == 'Inject' and time.time() - step_start < self.injection_wait:
                        time.sleep(abs(self.injection_wait - (time.time() - step_start)))
                        state = self.check_flags()
                        if not state:
                            return False


                    state = self.move_inlet(self.step['InletPos'])
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
    fin = open(TEST_METHOD, 'rb')
    data = pickle.load(fin)
    insert = data.insert
    cap_control = Lysis.CapillaryControl(hardware)
    flags = [threading.Event() for i in range(4)]
    rm = RunMethod(hardware, [data], 3, [0], flags, insert, 'testing', cap_control)
    return rm


def start_run(rm):
    threading.Thread(target=rm.start_run).start()


class ZStackData:
    """
    Class for controlling the Z acquisition of images.
    Stores data into a data frame according to the columns

    Methods that would probably need to be changed for additional auxiliary function are:
    _record_data() -> depending on the information you want to capture. default is xy, obj_z, cap_z,
    img_folder, slide_movment, well_num.

    _move_hardware()-> should be connected to the hardware that is moving (either objective or capillary)

    Fields that may need to be changed are:
    temp_file -> CSV filename from the database


    """
    _columns = ['x', 'y', 'objective_z', 'capillary_z', 'img_folder', 'slide_movement',
                'well_num']
    _focus_dir = os.getcwd() + "\\focus_data"
    _temp_file = _focus_dir + "\\cap_data.csv"
    file_prefix = "Orig-"
    def __init__(self, apparatus):
        self.apparatus = apparatus
        self.df = self._create_dataframe()
        self._load_temp()

    def start_acquisition(self, slide_movement=False, well_num=1):
        new_data = self._record_data(slide_movement)
        self._move_focus(new_data)
        self._save_temp()
        return

    def _record_data(self, slide_movment, well_num=1):
        """
        Records data at the start of the acquisition. The capillary and objective should be in focus with each other.
        The objective should be 100 microns above the focal plane of the glass.

        :param slide_movment: Bool. True signifies slide was adjusted or moved between the last
         acquisition and now
        :param well_num: Which of the sample wells this image was taken from
        :return:
        """
        # Record new data of the in focus region
        new_data = [None] * len(self._columns)
        new_data[0:2] = self.apparatus.get_xy()
        new_data[2] = self.apparatus.get_objective()
        new_data[3] = self.apparatus.get_z()
        new_data[4] = self._create_sample_folder()
        new_data[5] = slide_movment
        new_data[6] = well_num

        # Create new Data frame and add it to our dataset
        numpy_data = np.reshape(np.asarray(new_data), (1, len(self._columns)))
        new_df = pd.DataFrame(data=numpy_data, columns=self._columns)
        self.df = self.df.append(new_df)
        return new_data

    def _create_sample_folder(self):
        sample_time = datetime.datetime.now()
        name = "\\{}_{}".format(self.file_prefix, sample_time.strftime("%Y-%m-%d_%H-%M-%S"))
        dir_name = self._focus_dir + name
        os.mkdir(dir_name)
        return dir_name

    def _move_focus(self, new_data):
        """ Moves the objective up and down from the focus position."""
        start_pos = new_data[2]
        save_dir = new_data[4]
        # Move objective up
        self._loop_acquisition(start_pos, save_dir, 1)
        # Move objective down
        self._loop_acquisition(start_pos, save_dir, -1)

    def _move_hardware(self, position):
        """ Moves the objective to the absolute position specified by position"""
        self.apparatus.set_objective(position)
        self.apparatus.objective_control.wait_for_move()

    def _loop_acquisition(self, start_pos, save_dir, direction=1):
        """
        Moves the objective up and down from the focal plane. Acquires images according to the funciton
        set in the _move_function method

        :param start_pos: float, starting position of the objective
        :param save_dir: string, location to save the images
        :param direction: int, scalar to indicate up or down (+1 = up, -1 = down)
        :return:
        """
        move_x = 0
        while 100 > move_x > -100:
            self._move_hardware(move_x + start_pos)
            time.sleep(0.3)
            filename = save_dir + "\\z_stack_{:+04.0f}.png".format(move_x)
            self.apparatus.image_control.record_recent_image(filename)
            move_x += direction * self._move_function(np.abs(move_x))
        self._move_hardware(start_pos)
        return

    @staticmethod
    def _move_function(x):
        """
        Helps control the spacing around a point of interest, more detail near zero, an less detail farther out.
        :param x: current absolute position from center
        :return y: distance to move
        """

        y = 0.002 * (x ** 2.1) + 0.1 * x + 2
        return y

    def _save_temp(self):
        self.df.to_csv(self._temp_file)
        return

    def _load_temp(self):
        try:
            self.df = pd.read_csv(self._temp_file)
        except FileNotFoundError:
            logging.info("Creating new file...")
        return

    def save_as(self):
        return

    def _create_dataframe(self):
        df = pd.DataFrame(columns=self._columns)
        return df


if __name__ == "__main__":
    hardware = CESystems.NikonEclipseTi()
    rm = test_run(hardware)
    hardware.start_system()
    hardware.image_control.live_view()
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
