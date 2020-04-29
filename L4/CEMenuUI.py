import tkinter
from tkinter import filedialog
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
        
        """

    def __init__(self):
        super().__init__(self)
        self.options = self.main_menu_options
        self.system = CESystem()
        self.auto_run = AutomatedControl.AutoRun(self.system)
        self.view = None  # type: tkinter.Tk

        # Define Submenus
        self.system_menu = SystemMenu(self, self)
        self.config_menu = ConfigMenu(self, self)

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
            if file_path != -1:
                self.master.system.load_config(file_path)
                self.header = f"Config {file_path} loaded"
            return self

        if text == '2':
            self.master.system.open_controllers()
            return self

        elif text == '3':
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
        3. Add Template
        4. Set Repetition
        5. Set Sequence Style
        """

    def __init__(self, master, parent):
        super().__init__(master, parent)
        self.options = self.config_menu_options
        self.master = master  # type: MainMenu

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
            if file_path != -1:
                auto_run.add_method(file_path)
                self.header = f"Method {file_path} loaded"

        elif text == '2':  # clear the methods list
            num = len(auto_run.methods)
            auto_run.methods = []
            self.header = f"{num} Methods removed"

        elif text == '3':  # Set the template file
            file_path = filedialog.askopenfilename()
            if file_path != -1:
                auto_run.set_template(file_path)
                self.header = f"Method {file_path} loaded"

        elif text == '4':  # Set the repetition number
            reps = mui.get_integer_value("Please enter the number of repetitions:", root=view, exit_value=1)
            auto_run.repetitions = reps
            self.header = f" {reps} Repetitions of the methods will be performed."

        elif text == '5':  # Set the sequence style
            options = ['Method', 'Sequence']
            msg = "Select whether to apply repeitions on individual methods or collective sequence:"
            selection = mui.get_options_value(msg, view, options, exit_value='sequence')
            auto_run.repetition_style = selection.lower()
            self.header = f"{selection} repetition style selected"

        return self


if __name__ == "__main__":
    main = MainMenu()
    root = tkinter.Tk()

    # Skip to the step we want
    main.system.load_config()
    main.system.open_controllers()

    # Start the GUI part
    app = mui.Application(master=root, main_menu=main)
    root.mainloop()
