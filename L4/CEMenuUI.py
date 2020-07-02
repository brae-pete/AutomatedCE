import logging
import queue
import time
import tkinter
from queue import Queue
from tkinter import filedialog, ttk
from tkinter import messagebox
from L4 import MenuUi as mui
from L3.SystemsBuilder import CESystem
from L4 import AutomatedControl
from L2 import ZControl  # just for type hints


class MainMenu(mui.Menu):
    main_menu_options = """
        CE Main Menu: 
        
        1. System Menu
        2. Config Menu
        3. Start Run
        4. Stop CE
        5. Simulate Run
        
        """

    def __init__(self):
        super().__init__(self)
        self.options = self.main_menu_options
        self.system = CESystem()
        self.auto_run = AutomatedControl.AutoRun(self.system)
        self.auto_run.path_information.add_callback(print)
        self.view = None  # type: tkinter.Tk
        self.menu = None
        # Define Submenus
        self.system_menu = SystemMenu(self, self)
        self.config_menu = ConfigMenu(self, self)

    def setup(self):
        # Assign Callbacks
        self.auto_run.continue_callbacks['manual_cell'] = lambda msg: messagebox.askokcancel(
            "Manual Cell Lysis and Loading", msg)

        self.menu = ManualCellPopup(self.view, None,None,True, self.auto_run, self.system)
        self.auto_run.continue_callbacks['manual_cell'] = lambda message, step, simulation:self.menu.update_step(message, step, simulation)
        self.menu.top.withdraw()


    def interpret(self, text: str):
        """
        Interprets the Main menu options
        :param text: string identifier for the method
        :return: new menu to be loaded
        :rtype: mui.Menu
        """

        if text == "1":
            return self.system_menu
        elif text == "2":
            return self.config_menu
        elif text == "3":
            self.auto_run.start_run()
        elif text == "4":
            self.system.stop_ce()
            self.auto_run.stop_run()
        elif text == "5":
            self.auto_run.start_run(simulated=True)


        return self


class SystemMenu(mui.Menu):
    system_menu_options = """
        System Menu
        
        1. Load System Configuration
        2. Open Controllers
        3. Initialize Hardware
        4. XY Menu
        5. Inlet Height Menu
        6. Pressure Menu
        """

    def __init__(self, master: MainMenu, parent):
        super().__init__(master, parent)
        self.options = self.system_menu_options
        self.master = master  # Redundant but helps with type hinting our specialized class
        self.xy_menu = XYMenu(master, self)
        self.inlet_menu = ZMenu(master, self, 'inlet_z', 'Inlet Z')
        self.pressure_menu = PressureMenu(master, self)

    def interpret(self, text: str):
        """
        Interprets the system menu options
        :param text: string identifier for option
        :return: new menu to be loaded
        :rtype: mui.Menu
        """

        if text == '1':  # Load system config
            file_path = filedialog.askopenfilename()
            if file_path != -1 and file_path != "":
                self.master.system.load_config(file_path)
                self.header = f"Config {file_path} loaded"
            return self

        if text == '2':
            self.master.system.open_controllers()
            return self

        elif text == '3':
            self.master.system.startup_utilities()
            return self

        elif text == '4':
            return self.xy_menu

        elif text == '5':
            return self.inlet_menu

        elif text == '6':
            return self.pressure_menu

        else:
            return self


class XYMenu(mui.Menu):
    xy_menu_options = """
        XY Stage Menu
        
        1. Go Home
        2. Set Home
        3. Go XY
        4. Go Rel XY
        
        """

    def __init__(self, master, parent):
        super().__init__(master, parent)
        self.master = master  # type: MainMenu
        self.options = self.xy_menu_options

    def interpret(self, text: str):
        """
        Interprets XY options
        :param text: string identifier
        :return: new menu to display
        :rtype: mui.Menu
        """
        xy_stage = self.master.system.xy_stage
        view = self.master.view
        if text == '1':
            xy_stage.go_home()
            self.header = "Returned Home"
            return self

        elif text == '2':
            xy_stage.set_home()
            self.header = "Set as Home"
            return self

        elif text == '3':  # Set the XY coordinates
            xy = []
            for dimension in ['x', 'y']:
                msg = f"Enter {dimension} coordinate in mm:"
                d = mui.get_float_value(msg, view)
                if d is None:
                    self.header = f"Err: {dimension} coordinate required. \n"
                    return self
                xy.append(d)
            xy_stage.set_xy(xy)
            self.header = f"XY set to {xy} (mm, mm) \n"
            return self

        elif text == '4':  # Set the relative XY coordinates
            xy = []
            for dimension in ['x', 'y']:
                msg = f"Enter relative {dimension} coordinate in mm:"
                d = mui.get_float_value(msg, view, exit_value=0)
                xy.append(d)
            xy_stage.set_xy(xy)
            self.header = f"XY moved by {xy} (mm, mm) \n"
            return self


class ZMenu(mui.Menu):
    z_menu_options = """
        1. Go Home
        2. Set Home
        3. Set Z
        4. Set Rel Z
        5. Get Z
        """

    def __init__(self, master: MainMenu, parent: mui.Menu, z_stage: str, name: str):
        """

        :param master: the main menu object
        :param parent: the parent menu object
        :param z_stage: the systems attribute name for the z_stage to be adjusted
        :param name: name the stage will be referred to as by
        """
        super().__init__(master, parent)
        self.master = master  # type: MainMenu
        self.z_stage = z_stage  # type: str
        self.name = name
        self.options = f"{name} Menu \n" + self.z_menu_options

    def interpret(self, text):

        view = self.master.view
        z_stage = self.master.system.__getattribute__(self.z_stage)

        if text == '1':
            z_stage.go_home()
            self.header = f"Moved {self.name} to home position"
            return self

        elif text == '2':
            z_stage.set_home()
            self.header = f"Set home position for {self.name}"
            return self

        elif text == '3':
            msg = "Enter Z value in mm:"
            z_value = mui.get_float_value(msg, view)
            if z_value is None:
                self.header = f"Did not change Z value"
            else:
                z_stage.set_z(z_value)
                self.header = f"Attempted to move to {z_value} mm"
            return self

        elif text == '4':
            msg = "Enter Z value in mm:"
            z_value = mui.get_float_value(msg, view)
            if z_value is None:
                self.header = f"Did not change Z value"
            else:
                z_stage.set_rel_z(z_value)
                self.header = f"Attempted to move to {z_value} mm"
            return self

        elif text == '5':
            zval = z_stage.read_z()
            self.header = f"Position: {zval:.3f} mm"
            return self

class PressureMenu(mui.Menu):
    pressure_menu_options = """
        Pressure Menu Options
        1. Release Pressure
        2. Apply Rinse Pressure
        3. Apply Rinse Vacuum
        4. Apply Seal
        """

    def __init__(self, master, parent):
        super().__init__(master, parent)
        self.options = self.pressure_menu_options
        self.master = master  # type: MainMenu

    def interpret(self, text: str):
        """
        Interprets the options for the pressure menu
        :param text: string identifier
        :return: new menu options
        :rtype: mui.Menu
        """
        pressure = self.master.system.outlet_pressure
        view = self.master.view
        if text == '1':
            pressure.release()
            self.header = "Release Valve Opened"
        elif text == '2':
            pressure.rinse_pressure()
            self.header = "Pressure Valve Opened"
        elif text == '3':
            pressure.rinse_vacuum()
            self.header = "Vacuum Valve Opened"
        elif text == '4':
            pressure.seal()
            self.header = "All Valves Closed"
        return self


class ConfigMenu(mui.Menu):
    config_menu_options = """
        AutoRun Configuration Menu
        1. Add Method
        2. Clear Methods
        3. Load Template
        4. New Template
        5. Set Repetition
        6. Set Sequence Style
        """

    def __init__(self, master, parent):
        super().__init__(master, parent)
        self.options = self.config_menu_options
        self.master = master  # type: MainMenu

        self.new_template_menu = NewTemplateMenu(self.master, self)

    def interpret(self, text: str):
        """
        Interpret string identifier for config menu options
        :param text: string identifier for options
        :return: new menu to display
        :rtype: mui.Menu
        """
        auto_run = self.master.auto_run
        view = self.master.view

        if text == '1':  # Add a method file
            file_path = filedialog.askopenfilename()
            if file_path != -1 and file_path != "":
                auto_run.add_method(file_path)
                self.header = f"Method {file_path} loaded"

        elif text == '2':  # clear the methods list
            num = len(auto_run.methods)
            auto_run.methods = []
            self.header = f"{num} Methods removed"

        elif text == '3':  # Set the template file
            file_path = filedialog.askopenfilename()
            if file_path != -1 and file_path != "":
                auto_run.set_template(file_path)
                self.header = f"Method {file_path} loaded"

        elif text == '4':  # Open the New Template MEnu
            return self.new_template_menu

        elif text == '5':  # Set the repetition number
            reps = mui.get_integer_value("Please enter the number of repetitions:", root=view, exit_value=1)
            auto_run.repetitions = reps
            self.header = f" {reps} Repetitions of the methods will be performed."

        elif text == '6':  # Set the sequence style
            options = ['Method', 'Sequence']
            msg = "Select whether to apply repeitions on individual methods or collective sequence:"
            selection = mui.get_options_value(msg, view, options, exit_value='sequence')
            auto_run.repetition_style = selection.lower()
            self.header = f"{selection} repetition style selected"

        return self


class NewTemplateMenu(mui.Menu):
    new_template_menu_options = """
        New Template Menu
        
        1. Add Dimensions
        2. Add Circular Well
        3. Add Array of Circular Wells
        4. Add Rectangular Ledge
        5. Add Header Information 
        
        6. Save Template
        7. Clear Template
        
        """

    def __init__(self, master: MainMenu, parent):
        super().__init__(master, parent)
        self.options = self.new_template_menu_options
        self.master = master  # type: MainMenu
        self._new_template = AutomatedControl.TemplateMaker()

    @staticmethod
    def _get_stage_or_value(parameters: list, xy_stage, view):
        """
        Returns a list of values either from user input or the stage reading
        :param parameters: should have x or y in the name so that it can be determined whether to grab the x or y coord.
        :return: list of values in according to parameter
        """
        dims = []
        for dimension in parameters:
            msg = f"Enter {dimension} coordinate in mm \n or leave blank to stage position:\n"
            d = mui.get_float_value(msg, view)
            if d is None:
                xy_point = xy_stage.read_xy()
                if 'x' in dimension.lower():
                    d = xy_point[0]
                else:
                    d = xy_point[1]
            dims.append(d)
        return dims

    def interpret(self, text: str):
        """
        Interpret string identifier for config menu options
        :param text: string identifier for options
        :return: new menu to display
        :rtype: mui.Menu
        """
        # auto_run = self.master.auto_run
        view = self.master.view
        xy_stage = self.master.system.xy_stage

        if text == '1':  # Add a Dimensions file
            dims = self._get_stage_or_value(['left x', 'lower y', 'right x', 'upper y'], xy_stage, view)
            self._new_template.add_dimension(dims[0], dims[1], dims[2], dims[3])
            return self

        elif text == '2':  # Add a circle to the well list
            dims = self._get_stage_or_value(['center x', 'center y'], xy_stage, view)
            diameter = mui.get_float_value("Enter the well diameter:", view)
            name = mui.get_string_value("Enter the Label for the well:", view)
            self._new_template.add_well(name, dims, diameter, 'circle')
            return self

        elif text == '3':  # Add array of circular wells
            name = mui.get_string_value("Enter the Label for the well:", view)
            dims = self._get_stage_or_value(['Corner 1 X', 'Corner 1 Y', 'Corner 2 X', 'Corner 2 Y'], xy_stage, view)
            diameter = mui.get_float_value("Enter the well diameter:", view)
            rows = mui.get_integer_value("Enter the number of rows:", view)
            cols = mui.get_integer_value("Enter the number of columns:", view)
            self._new_template.add_array(name, dims[0:2], dims[2:], rows, cols, diameter, 'circle')
            return self

        elif text == '4':  # Add a ledge to the template
            dims = self._get_stage_or_value(['Left x', 'Lower Y'], xy_stage, view)
            width = mui.get_float_value("Enter Width (x) of ledge", view)
            depth = mui.get_float_value("Enter Depth (y) of ledge", view)
            height = mui.get_float_value("Enter Height (z) of ledge", view)
            name = mui.get_string_value("Enter the Label for the Ledge:", view)
            self._new_template.add_ledge(name, dims, [width, depth], 'rectangle', height)
            return self

        elif text == '5':  # Set the repetition number
            info = mui.get_string_value('Enter any Notes for this Template: ', view)
            self._new_template.header = info
            return self

        elif text == '6':  # Set the sequence style
            file_path = filedialog.asksaveasfilename(defaultextension = ".txt")
            if file_path != -1 and file_path != "":
                self._new_template.save_to_file(file_path)
            return self

        elif text == '7':
            self._new_template = AutomatedControl.TemplateMaker()

        return self


class ManualCellPopup:

    def __init__(self, ui_parent, msg, step,simulated, auto_run:AutomatedControl.AutoRun, system:CESystem):
        top = self.top = tkinter.Toplevel(ui_parent)
        self.parent = ui_parent
        self.event = auto_run.continue_event
        self.auto_run = auto_run
        self.system = system
        self.step = step
        self.simulated = simulated

        # We will need to use a Queue to let the parent window when to show this window
        self.parent.after(100, self.check_show)
        self.queue = Queue()

        # Create the widgets
        self.label = ttk.Label(top, text=msg)
        self.label.pack()
        self.hold = tkinter.IntVar()
        self.hold_btn = ttk.Checkbutton(top, text='Hold and Load',
                              variable=self.hold)
        self.hold_btn.pack()
        self.timed_btn = ttk.Button(top, text='Timed Load', command =self.timed_injection)
        self.timed_btn.pack()
        self.fire_btn = ttk.Button(top, text='Fire', command=self.fire)
        self.fire_btn.pack()
        self.continue_btn1 = ttk.Button(top, text='Continue', command=self.close_and_continue)
        self.continue_btn1.pack()

        self.top.protocol("WM_DELETE_WINDOW", self.exit)
        self.hold.trace("w",self.hold_injection)
        self.total_time = 0
        self._last_hold_start_time = time.time()

    def check_show(self, *args):
        if not self.queue.empty():
            try:
                req = self.queue.get_nowait()

                if req == 'show':
                    self.top.deiconify()
                elif req == 'hide':
                    self.top.withdraw()
            except queue.Empty:
                logging.debug("Request is empty")
        self.parent.after(100, self.check_show)

    def fire(self, *args):
        self.system.lysis_laser.laser_fire()

    def timed_injection(self, *args):
        """
        Runs a timed injection
        :param args:
        :return:
        """
        self.auto_run.timed_step(self.step, simulated=self.simulated)

    def hold_injection(self, *args):
        """
        Checks if the state is 0 or 1
        :param args:
        :return:
        """
        if self.hold.get() == 1:
            self._last_hold_start_time = time.time()
            if not self.simulated:
                self.system.high_voltage.set_voltage(self.step.voltage)
                self.system.high_voltage.start()
                self.system.outlet_pressure.release()
                time.sleep(0.2)
                self.system.lysis_laser.laser_fire()

        else:
            if not self.simulated:
                self.system.high_voltage.stop()
                self.system.outlet_pressure.seal()
            self.total_time += (time.time()-self._last_hold_start_time)

    def close_and_continue(self):
        """Close the window and set the continue event"""
        self.event.set()
        self.queue.put('hide')

    def exit(self):
        """When the window closes check if the event has been set, if not stop the run"""

        if not self.event.is_set():

            self.auto_run.stop_run()
        self.queue.put('hide')

    def update_step(self, message, step, simulation):
        self.step = step
        self.simulated = simulation
        self.queue.put('show')

if __name__ == "__main__":

    import os

    resp = os.getcwd()
    os.chdir(os.path.abspath(os.path.join(os.getcwd(), '..')))
    print(f"new directory is: {os.getcwd()}")
    main = MainMenu()
    root = tkinter.Tk()

    # Skip to the step we want
    main.system.load_config()
    main.system.open_controllers()
    main.system.startup_utilities()
    #main.auto_run.add_method(os.path.abspath(os.path.join(os.getcwd(),'config/method-test.txt')))
    #main.auto_run.set_template(os.path.abspath(os.path.join(os.getcwd(), 'config/template-test.txt')))
    main.system.load_config(r"C:\Users\NikonTE300CE\Desktop\Barracuda\AutomatedCE\var\TE300.cfg")
    main.system.open_controllers()
    main.system.startup_utilities()


    # Start the GUI part
    app = mui.Application(master=root, main_menu=main)
    root.mainloop()
