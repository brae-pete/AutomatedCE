import time
from L3.SystemsBuilder import CESystem
from L4 import AutomatedControl
import threading
from tkinter import filedialog
import tkinter as tk


class Application(tk.Frame):
    message_header = "Please enter the number for the option below and press 'Send Command' \n"

    def __init__(self, master=None, controller=None, default='Simple UI'):
        super().__init__(master)
        self.master = master
        self.root = tk.Tk()
        self.pack()
        self.create_widgets(default)
        self.controller = controller

    def create_widgets(self, msg=None):
        self.message = tk.Text(self)
        if msg is None:
            msg = ""

        self.message.insert(tk.INSERT, self.message_header + msg)
        self.message.pack()

        self.input = tk.Entry(self)
        self.input.pack()

        self.send_button = tk.Button(self)
        self.send_button['command'] = self.send_command
        self.send_button['text'] = 'Send Command'
        self.master.bind('<Return>', self.send_command)

        self.send_button.pack()

    def send_command(self, *args):
        self.controller.send_command(self.input.get())
        self.input.delete(0, 'end')


class Controller:

    def __init__(self):
        self.root = tk.Tk()
        self.model = Model(controller=self)
        self.view = Application(master=self.root, controller=self, default=self.model.default_text)

        self.view.mainloop()

    def send_command(self, text):
        self.model.interpret(text)

    def send_response(self, msg):
        self.view.message.delete(2.0, tk.END)
        self.view.message.insert(tk.INSERT, msg)

    def update(self):
        self.view.master.after(1000, self.model.run_update)


class Model:
    main_menu = """
        1: Initialize System
        2: Configure Run
        3: Set Data Directory
        4: Start Run
        """

    system_menu = """
        1. Load System Config
        2. Open Controllers
        3. Initialize Hardware (reset to default states)
        
        0. Main Menu
        More hardware options can be added here...
        """
    run_menu = """
        1. Add Method
        2. Set Template
        3. Set Repetitions
        4. Configure Collection Gate
        
        0. Main Menu
        """

    gate_menu = """
        Configure Gate. 
        1. Add peak 
        2. Add gate settings
        
        0. Main Menu
        """

    params = {'sequence_type': 'sequence'}

    def __init__(self, controller):

        self.controller = controller
        self.system = CESystem()
        self.auto_run = AutomatedControl.AutoRun(system=self.system)
        # Menu Variables
        self.menu_choice = 'main'
        self.default_text = self.main_menu

        # Threading Parameters
        self._threads = {}
        self.is_running = threading.Event()
        self._remaining_time = 0

    def interpret(self, text):
        msg = self.menu_choice
        if self.menu_choice == 'main':
            msg = self.main_menu_options(text)

        elif self.menu_choice == 'run':
            msg = self.run_menu_options(text)

        elif self.menu_choice == 'system':
            msg = self.system_menu_options(text)

        elif self.menu_choice == 'gate':
            msg = self.gate_menu_options(text)

        elif self.menu_choice == 'running':
            self.running_menu_options(text)
            return

        elif self.menu_choice == 'repetition_entry':
            msg = self.repetition_entry(text)

        elif self.menu_choice == 'sequence_entry':
            msg = self.sequence_entry(text)

        elif self.menu_choice == 'peak_entry':
            msg = self.peak_entry(text)

        elif self.menu_choice == 'gate_entry':
            msg = self.gate_entry(text)

        self.controller.send_response(msg)

    def main_menu_options(self, text):
        """
        :param text:
        :return:
        """
        resp = int(text)

        if resp == 1:
            self.menu_choice = 'system'
            return self.system_menu

        if resp == 2:
            self.menu_choice = 'run'
            return self.run_menu

        elif resp == 3:
            dir_path = filedialog.askdirectory()
            if dir_path != -1:
                self.auto_run.data_dir = dir_path
            return f"Data directory set to {self.auto_run.data_dir}"

        elif resp == 4:
            self.auto_run.start_run()
            self.menu_choice = 'main'
            # Create a Timer program
            self._remaining_time = self.run_time
            return self.main_menu

        return self.main_menu

    def system_menu_options(self, text):

        if text == '1':  # Load system config
            file_path = filedialog.askopenfilename()
            if file_path != -1:
                self.system.load_config(file_path)
                return f"Config {file_path} loaded" + self.system_menu
            return self.system_menu

        elif text == '2':  # Load Controllers
            self.system.open_controllers()
            return 'Controllers Opened \n\n\n' + self.system_menu

        elif text == '3':  # Initialize Hardware
            self.system.initialize_hardware()
            return 'System Initialized \n\n\n' + self.system_menu

        elif text == '0':
            self.menu_choice = 'main'
            return self.main_menu

    def run_menu_options(self, text):

        if text == '1':  # Load Method
            self.menu_choice = 'main'
            file_path = filedialog.askopenfilename()
            if file_path != -1:
                self.auto_run.add_method(file_path)
                return f"Method {file_path} loaded" + self.main_menu
            return self.main_menu

        elif text == '2':  # Set template
            self.menu_choice = 'main'
            file_path = filedialog.askopenfilename()
            if file_path != -1:
                self.auto_run.set_template(file_path)
                return f"Template {file_path} loaded" + self.main_menu
            return self.main_menu

        elif text == '3':  # Set repetitions
            self.menu_choice = 'repetition_entry'
            msg = '\n\n\n Please enter the number of repetitions to perform: \n\n'
            return msg

        elif text == '4':  # Set Sequence type
            self.menu_choice = 'sequence_entry'
            msg = """ Pleas select a sequence type: 
             1. Repeat methods individually
             2. Repeat methods sequentially \n\n
             """
            return msg

        elif text == '4':
            self.menu_choice = 'gate'
            return self.gate_menu

        elif text == '0':
            self.menu_choice = 'main'
            return self.main_menu

    def gate_menu_options(self, text):

        if text == '1':
            msg = """Please enter the peak name, starting point, and ending point of the peak in this format:
                  
                  EXAMPLE: Fluorescein, 15 s, 20 s
                  
                  ensure values are separated by commas, acceptable units for time are 's' or 'min'
                  Value and units must be separated by a space. 
                  """
            self.menu_choice = 'peak_entry'
            return msg

        elif text == '2':
            msg = f""" Please enter the fraction of peak_A to implement gate, the well name to move the collection to, 
            the peak_A name, and all other peaks to consider. 
            Logic can be thought of as: if Area_A/sum(Area_others+Area_A) > fraction --> move to well_name

            EXAMPLE: 0.5, 'well_1', 'peak_1', 'peak_2', 'peak_3',...'peak_i'

            Acceptable peaks are: {self.auto_run.gate.peaks.keys()}
            Acceptable wells are: {self.auto_run.template.wells.keys()}
            """
            self.menu_choice = 'gate_entry'

        elif text == '0':
            self.menu_choice = 'main'
            return self.main_menu

    def repetition_entry(self, text):
        rep = float(text)
        self.auto_run.repetitions = rep
        self.menu_choice='gate'
        return self.gate_menu

    def sequence_entry(self, text):
        if text == '1':
            self.params['sequence_type'] = 'sequence'
        else:
            self.params['sequence_type'] = 'method'
        self.menu_choice = 'run'
        return self.run_menu

    def peak_entry(self, text):
        entries = text.split(',')
        assert len(entries)==3, "Incorrect format, need 3 values separated commas"
        start_time = AutomatedControl.get_standard_unit(entries[1].strip())
        stop_time = AutomatedControl.get_standard_unit(entries[2].strip())
        self.auto_run.gate.add_peak(entries[0], start_time, stop_time)
        self.menu_choice='gate'
        return self.gate_menu

    def gate_entry(self, text):
        entries = [x.strip() for x in text.split(',')]
        assert len(entries) >= 4, 'Not enough arguments'
        fraction = float(entries[0])
        assert 0 <= fraction <= 1, f'Fraction ({fraction}) must be a value between 0 and 1'
        well_name = entries[1]
        assert well_name in self.auto_run.template.wells.keys(), f"Well name {well_name} not in list."
        for peak in entries[2:]:
            assert peak in self.auto_run.gate.peaks.keys(), f'Peak {peak} not in list'
        peak_name = entries[2]
        peaks = tuple(entries[3:])
        self.auto_run.gate.set_gate(fraction, well_name, peak_name, *peaks)
        self.menu_choice='gate'
        return self.main_menu

    def running_menu_options(self, text):
        """ User can choose to end the run early. The is running event will trigger, and the
        CE run code will exit theloop.
        """
        if int(text) == 1:
            self.auto_run.is_running.clear()
            self.system.stop_ce()
            self.menu_choice = 'main'
            return self.main_menu



def better_sleep(target, sample_time):
    """
    This is a more accurate sleep call, it takes into account time_data that has elapsed while gathering data
    :param moment: a object from time_data.time_data(), the last time_data better_sleep was run.
    :param SAMPLE_FREQ: The sampling frequency you wish to sample at
    :return:
    """
    while time.time() < target + (sample_time):
        # Sleep 1 milliseconds and check again
        time.sleep(0.01)
    return target + sample_time


ctl = Controller()
