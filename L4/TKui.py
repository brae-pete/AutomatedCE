from tkinter import *
from tkinter import ttk
from tkinter import filedialog

from skimage.exposure import adjust_gamma, exposure
from skimage.io import imsave
from skimage.transform import resize

from L3 import SystemsBuilder
from L4 import SystemQueue, FileIO
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib.pyplot import imshow
import numpy as np


class RootWindow(Frame):
    """
    Root contains all the buttons that will allow for subwindows to appear

    """

    def __init__(self, root, **kw):
        super().__init__(root, **kw)
        self.system_queue = SystemQueue.SystemsRoutine()
        self.root = root
        self.injection_data = InjectionData(self)
        # Add the main Buttons
        system_button = ttk.Button(root, text='System', command=lambda x=self: CESystemWindow(x))
        system_button.grid(column=0, row=0)

        init_button = ttk.Button(root, text="Init", command=lambda x=self: InitFrame(x))
        init_button.grid(column=1, row=0)

        method_button = ttk.Button(root, text='Method', command=lambda x=self: MethodWindow(x))
        method_button.grid(column=2, row=0)

        egram_button = ttk.Button(root, text='Manual Cell', command=lambda x=self: InjectionWindow(x))
        egram_button.grid(column=3, row=0)

        egram_button = ttk.Button(root, text='Egram', command=lambda x=self: EgramWindow(x))
        egram_button.grid(column=4, row=0)

        egram_button = ttk.Button(root, text='Camera', command=lambda x=self: CameraWindow(x))
        egram_button.grid(column=5, row=0)

        egram_button = ttk.Button(root, text='Terminal', command=lambda x=self: TerminalWindow(x))
        egram_button.grid(column=6, row=0)

        root.title('Automated Chip')

        root.after(250, self.check_queues)

    def check_queues(self):
        """
        Check the queues for any updates to the UI
        Also sends commands to get updates from the system
        :return:
        """
        self.system_queue.check_error_queue()
        self.system_queue.check_info_queue()
        self.system_queue.send_updates()
        self.root.after(1000, self.check_queues)

    def on_close(self):
        self.system_queue.stop_process()
        self.system_queue.check_info_queue()
        self.system_queue.check_error_queue()
        self.root.destroy()


class CollapsiblePane(ttk.Frame):
    """
     -----USAGE-----
    collapsiblePane = CollapsiblePane(parent,
                          expanded_text =[string],
                          collapsed_text =[string])

    collapsiblePane.pack()
    button = Button(collapsiblePane.frame).pack()
    """

    def __init__(self, parent, expanded_text="Collapse <<",
                 collapsed_text="Expand >>"):

        ttk.Frame.__init__(self, parent)

        # These are the class variable
        # see a underscore in expanded_text and _collapsed_text
        # this means these are private to class
        self.parent = parent
        self._expanded_text = expanded_text
        self._collapsed_text = collapsed_text

        # Here weight implies that it can grow it's
        # size if extra space is available
        # default weight is 0
        self.columnconfigure(1, weight=1)

        # Tkinter variable storing integer value
        self._variable = IntVar()

        # Checkbutton is created but will behave as Button
        # cause in style, Button is passed
        # main reason to do this is Button do not support
        # variable option but checkbutton do
        self._button = ttk.Checkbutton(self, variable=self._variable,
                                       command=self._activate, style="TButton")
        self._button.grid(row=0, column=0)

        # This wil create a seperator
        # A separator is a line, we can also set thickness
        self._separator = ttk.Separator(self, orient="horizontal")
        self._separator.grid(row=0, column=1, sticky="we")

        self.frame = ttk.Frame(self)

        # This will call activate function of class
        self._activate()

    def _activate(self):
        if not self._variable.get():

            # As soon as button is pressed it removes this widget
            # but is not destroyed means can be displayed again
            self.frame.grid_forget()

            # This will change the text of the checkbutton
            self._button.configure(text=self._collapsed_text)

        elif self._variable.get():
            # increasing the frame area so new widgets
            # could reside in this container
            self.frame.grid(row=1, column=0, columnspan=2)
            self._button.configure(text=self._expanded_text)

    def toggle(self):
        """Switches the label frame to the opposite state."""
        self._variable.set(not self._variable.get())
        self._activate()


class ZExpandable(CollapsiblePane):
    """
    Z expandable frame allows control over essential Z stage functionality.
    Z position is displayed in mm
    Z position can be set absolutely or relatively using a combination of spin boxes and buttons.

    """

    def __init__(self, parent, root: RootWindow, z_name='inlet_z', **kw):
        super().__init__(parent, **kw)

        self.name = z_name
        self.z_stage_readout = StringVar(value="{} Position:  mm".format(self.name))
        self.z_step = None  # type: ttk.Spinbox
        self.z_abs = None  # type: ttk.Spinbox

        self.setup()
        root.system_queue.add_info_callback("system.{}.read_z".format(z_name), self.read_z)
        self.root_window = root

    def setup(self):
        lbl = ttk.Label(self.frame)
        lbl.grid(row=0, column=0)
        lbl['textvariable'] = self.z_stage_readout

        up_btn = ttk.Button(self.frame, text='Up', command=lambda: self.rel_z(1))
        up_btn.grid(column=0, row=1)

        down_btn = ttk.Button(self.frame, text='Down', command=lambda: self.rel_z(-1))
        down_btn.grid(column=0, row=2)

        lbl_z = ttk.Label(self.frame, text="Step mm: ")
        lbl_z.grid(column=1, row=0)
        spin_z = ttk.Spinbox(self.frame, from_=0, to_=10 ** 9, increment=0.05)
        spin_z.grid(column=1, row=1)
        self.z_step = spin_z

        lbl_z = ttk.Label(self.frame, text="{} Z position: ".format(self.name))
        lbl_z.grid(column=0, row=3)
        spin_z = ttk.Spinbox(self.frame, from_=-10 ** 9, to=10 ** 9, increment=0.05)
        spin_z.set(0)
        spin_z.grid(column=1, row=3)
        self.z_abs = spin_z
        lbl_z_unit = ttk.Label(self.frame, text=" mm ")
        lbl_z_unit.grid(column=2, row=3)

        go_btn = ttk.Button(self.frame, text="Go", command=self.go_abs)
        go_btn.grid(column=1, row=4)

        startup = ttk.Button(self.frame, text='Startup', command=self.startup_command)
        startup.grid(column=0, row=4)

    def read_z(self, z, *args):
        self.z_stage_readout.set(z)

    def startup_command(self):
        self.root_window.system_queue.send_command('system.{}.startup'.format(self.name))

    def rel_z(self, direction: int, *args):
        value = float(self.z_step.get()) * direction
        self.root_window.system_queue.send_command('system.{}.set_rel_z'.format(self.name), value)

    def go_abs(self):
        value = float(self.z_abs.get())
        self.root_window.system_queue.send_command('system.{}.set_z'.format(self.name), value)


class XYExpandable(CollapsiblePane):
    """
    XY Expandable Frame allows user to control the most important aspects of the XY stage.
    XY position is displayed in mm,
    the absolute or relative position can be set using a combination of spin boxes and buttons
    """

    def __init__(self, parent, root: RootWindow, **kw):
        super().__init__(parent, **kw)

        self.xy_stage_readout = StringVar(value="X: mm Y: mm")
        self.step_spin = None  # type: ttk.Spinbox
        self.x_spin = None  # type: ttk.Spinbox
        self.y_spin = None  # type: ttk.Spinbox

        self.setup()
        root.system_queue.add_info_callback("system.xy_stage.read_xy", self.read_xy)
        self.root_window = root

    def setup(self):
        """
        Places all the buttons into their respective positions.
        :return:
        """
        lbl = ttk.Label(self.frame)
        lbl['textvariable'] = self.xy_stage_readout
        lbl.grid(column=0, row=0, columnspan=3)

        up_btn = ttk.Button(self.frame, text="Up", command=lambda: self.set_rel('y', 1))
        up_btn.grid(row=1, column=1)
        down_btn = ttk.Button(self.frame, text="Down", command=lambda: self.set_rel('y', -1))
        down_btn.grid(row=3, column=1)
        left_btn = ttk.Button(self.frame, text="Left", command=lambda: self.set_rel('x', -1))
        left_btn.grid(row=2, column=0)
        right_btn = ttk.Button(self.frame, text="Right", command=lambda: self.set_rel('x', 1))
        right_btn.grid(row=2, column=2)

        step_bx = ttk.Spinbox(self.frame, from_=0, to=5, increment=0.02)
        step_bx.grid(row=1, column=2)
        self.step_spin = step_bx

        x_lbl = ttk.Label(self.frame, text="X: ")
        x_lbl.grid(row=4, column=0)
        x_spin = ttk.Spinbox(self.frame, increment=0.02)
        x_spin.grid(row=4, column=1)
        self.x_spin = x_spin
        x_lbl_unit = ttk.Label(self.frame, text=" mm")
        x_lbl_unit.grid(row=4, column=2)

        y_lbl = ttk.Label(self.frame, text="Y: ")
        y_lbl.grid(row=5, column=0)
        y_spin = ttk.Spinbox(self.frame, increment=0.02)
        y_spin.grid(row=5, column=1)
        self.y_spin = y_spin
        y_lbl_unit = ttk.Label(self.frame, text=" mm")
        y_lbl_unit.grid(row=5, column=2)

        go_btn = ttk.Button(self.frame, text="Go!", command=self.set_abs)
        go_btn.grid(row=6, column=2)

        start_btn = ttk.Button(self.frame, text='Startup', command=self.startup_command)
        start_btn.grid(row=6, column=2)

    def read_xy(self, xy, *args):
        try:
            self.xy_stage_readout.set("X: {:.3f} Y: {:.3f}".format(xy[0], xy[1]))
        except:
            self.xy_stage_readout.set("incoming err read_xy: {}".format(xy))

    def set_abs(self):
        xy = [float(self.x_spin.get()), float(self.y_spin.get())]
        self.root_window.system_queue.send_command('system.xy_stage.set_xy', xy)

    def set_rel(self, axis: str, direction: int):
        value = float(self.step_spin.get()) * direction
        if axis == 'x':
            self.root_window.system_queue.send_command('system.xy_stage.set_rel_x', value)
        elif axis == 'y':
            self.root_window.system_queue.send_command('system.xy_stage.set_rel_y', value)

    def startup_command(self):
        self.root_window.system_queue.send_command('system.xy_stage.startup')


class SolenoidExpandable(CollapsiblePane):

    def __init__(self, parent, root: RootWindow, **kw):
        super().__init__(parent, **kw)
        self.pressure_state_var = StringVar()
        self.pressure_state_var.trace('w', self.change_pressure)
        self.root_window = root
        self.setup()

    def setup(self):
        states = [('Seal', 'seal'),
                  ('Release', 'release'),
                  ('Vacuum', 'rinse_vacuum'),
                  ('Pressure', 'rinse_pressure')]

        for label, cmd in states:
            rd_btn = ttk.Radiobutton(self.frame, text=label, variable=self.pressure_state_var, value=cmd)
            rd_btn.grid()

    def change_pressure(self, *args):
        utility_method = self.pressure_state_var.get()
        self.root_window.system_queue.send_command('system.outlet_pressure.{}'.format(utility_method))


class LEDExpandable(CollapsiblePane):

    def __init__(self, parent, root: RootWindow, **kw):
        super().__init__(parent, **kw)
        self.r_var = IntVar()
        self.g_var = IntVar()
        self.b_var = IntVar()

        self.root_window = root
        self.setup()

    def setup(self):
        channels = [('Red', self.r_var),
                    ('Green', self.g_var),
                    ('Blue', self.b_var)]

        col = 0
        for label, var in channels:
            ck_button = ttk.Checkbutton(self.frame, text=label, variable=var)
            ck_button.grid(row=0, column=col)
            col += 1

        apply_button = ttk.Button(self.frame, text='Apply', command=self.set_led)
        apply_button.grid(row=0, column=col)

    def set_led(self):
        for var, rgb in [(self.r_var, 'R'), (self.g_var, 'G'), (self.b_var, 'B')]:
            state = var.get()
            if state > 0:
                self.root_window.system_queue.send_command('system.inlet_rgb.turn_on_channel', rgb)
            elif state == 0:
                self.root_window.system_queue.send_command('system.inlet_rgb.turn_off_channel', rgb)


class HighVoltageExpandable(CollapsiblePane):
    def __init__(self, parent, root: RootWindow, **kwargs):
        super().__init__(parent, **kwargs)

        self.root_window = root
        self.volt_spin = DoubleVar(value=0)
        self.setup()

    def setup(self):
        lbl = ttk.Label(self.frame, text="Voltage (kV)")
        lbl.grid()

        spn = ttk.Spinbox(self.frame, textvariable=self.volt_spin)
        spn.grid()

        btn = ttk.Button(self.frame, text='Set Voltage', command=self.set_voltage)
        btn.grid()

    def set_voltage(self):
        volts = self.volt_spin.get()
        self.root_window.system_queue.send_command('system.high_voltage.set_voltage', voltage=volts)
        self.root_window.system_queue.send_command('system.high_voltage.start')


class LaserExpandable(CollapsiblePane):

    def __init__(self, parent, root: RootWindow, **kwargs):
        super().__init__(parent, **kwargs)

        self.root_window = root
        self.enable_var = IntVar(value=0)
        self.enable_var.trace('w', self.standby_laser)
        self.setup()

    def setup(self):
        ck_button = ttk.Checkbutton(self.frame, text='Enable Laser')
        ck_button.grid()

        fire = ttk.Button(self.frame, text='Fire', command=self.fire_laser)
        fire.grid()

    def fire_laser(self):
        self.root_window.system_queue.send_command('system.lysis_laser.laser_fire')

    def standby_laser(self):
        enb = self.enable_var.get()
        if enb == 1:
            self.root_window.system_queue.send_command('system.lysis_laser.laser_standby')
        elif enb == 0:
            self.root_window.system_queue.send_command('system.lysis_laser.stop')


class CESystemWindow(Frame):

    def __init__(self, parent: RootWindow, **kw):
        window = Toplevel(parent)
        super().__init__(window, **kw)

        window.title('System Controls')
        self.parent = parent
        reset_button = ttk.Button(window, text="Reset", command=self.reset_process)
        reset_button.grid(row=0, column=0)
        st = 1

        xy_stage_label = ttk.Label(window, text='XY Stage')
        xy_stage_label.grid(row=st + 0, column=0, sticky="NEW")
        self.xy_stage_frame = XYExpandable(window, parent)
        self.xy_stage_frame.grid(row=st + 0, column=1, sticky="NSEW")

        objective_label = ttk.Label(window, text='Objective Z ')
        objective_label.grid(row=1 + st, column=0, sticky="NEW")
        self.objective_frame = ZExpandable(window, parent, z_name='objective')
        self.objective_frame.grid(row=1 + st, column=1, sticky="NSEW")

        outlet_label = ttk.Label(window, text='Outlet Z ')
        outlet_label.grid(row=2 + st, column=0, sticky="NEW")
        self.outlet_z_frame = ZExpandable(window, parent, z_name='outlet_z')
        self.outlet_z_frame.grid(row=2 + st, column=1, sticky="NSEW")

        inlet_label = ttk.Label(window, text='Inlet Z ')
        inlet_label.grid(row=3 + st, column=0, sticky="NEW")
        self.inlet_z_frame = ZExpandable(window, parent, z_name='inlet_z')
        self.inlet_z_frame.grid(row=3 + st, column=1, sticky="NSEW")

        label = ttk.Label(window, text='Pressure')
        label.grid(row=4 + st, column=0, sticky="NEW")
        self.pressure_frame = SolenoidExpandable(window, parent)
        self.pressure_frame.grid(row=4 + st, column=1, sticky="NSEW")

        label = ttk.Label(window, text='RGB LED ')
        label.grid(row=5 + st, column=0, sticky="NEW")
        self.led_frame = LEDExpandable(window, parent)
        self.led_frame.grid(row=5 + st, column=1, sticky="NSEW")

        label = ttk.Label(window, text='Lysis Laser')
        label.grid(row=6 + st, column=0, sticky="NEW")
        self.lysis_frame = LaserExpandable(window, parent)
        self.lysis_frame.grid(row=6 + st, column=1, sticky="NSEW")

        label = ttk.Label(window, text='High Voltage')
        label.grid(row=7 + st, column=0, sticky="NEW")
        self.voltage_frame = HighVoltageExpandable(window, parent)
        self.voltage_frame.grid(row=7 + st, column=1, sticky="NSEW")

    def reset_process(self):
        try:
            self.parent.system_queue.stop_process()
        except Exception as e:
            print(e)
        self.parent.system_queue.start_process()


class InitFrame(Frame):

    def __init__(self, parent: RootWindow, **kw):
        self.window = window = Toplevel(parent)
        super().__init__(window, **kw)
        self.well_var = StringVar(value="Select")

        self.setup()
        self.parent = parent
        self.grid()
        self.setup()

    def setup(self):
        """ Place the buttons"""
        window = self.window

        # Instructions Frame
        instruction_frame = ttk.Frame(window)
        instruction_frame.grid(row=0, column=0, rowspan=2)

        header_lbl = ttk.Label(instruction_frame, text='Initialize System')
        header_lbl.grid(row=0, column=0)

        step_1_lbl = ttk.LabelFrame(instruction_frame, text=" 1. Load the System ")
        step_1_lbl.grid()

        step_1_file_button = ttk.Button(step_1_lbl, text='Select Config',
                                        command=self.set_config)
        step_1_file_button.grid()

        step_2_lbl = ttk.LabelFrame(instruction_frame, text='2. Load the Template')
        step_2_lbl.grid()

        step_2_btn = ttk.Button(step_2_lbl, text='Select Template', command=self.set_template)
        step_2_btn.grid()

        step_3_lbl = ttk.LabelFrame(instruction_frame, text="3. Calibrate the CE Apparatus")
        step_3_lbl.grid()

        btn = ttk.Button(step_3_lbl, text='Home Z Stage', command=self.z_home)
        btn.grid()

        btn = ttk.Button(step_3_lbl, text='Set XY Home', command=self.xy_home)
        btn.grid()

        step_4_lbl = ttk.LabelFrame(instruction_frame, text="4. Calibration Check")
        step_4_lbl.grid()

        lbl = ttk.Label(step_4_lbl, text='Select a Box')
        lbl.grid(row=0)
        cbx = ttk.Entry(step_4_lbl, textvariable=self.well_var)
        cbx.grid(row=1)
        btn = ttk.Button(step_4_lbl, text='Move to well', command=self.move_to_well)
        btn.grid()

        picture_frame = ttk.Frame(window)
        picture_frame.grid(row=0, column=1)

        detail_frame = ttk.Frame(window)
        detail_frame.grid(row=1, column=1)

    def set_config(self):
        """ Set the system config file """
        f_name = filedialog.askopenfilename()
        if f_name is not None:
            self.parent.system_queue.send_command("system.load_config", config_file=f_name)
            self.parent.system_queue.config = f_name

    def set_template(self):
        """ Set the automated run template """
        f_name = filedialog.askopenfilename()
        if f_name is not None:
            self.parent.system_queue.send_command('auto_run.set_template', template_file=f_name)

    def xy_home(self):
        """Sets the XY home position"""
        self.parent.system_queue.send_command('system.xy_stage.set_home')

    def z_home(self):
        """ Moves to the Z inlet home position"""
        self.parent.system_queue.send_command('system.inlet_z.homing')

    def move_to_well(self):
        """
        Moves to a well
        """
        well_name = self.well_var.get()
        if well_name != 'Select':
            self.parent.system_queue.send_command('auto_run.move_to_well', well_name)


class EgramWindow(Frame):
    def __init__(self, parent: RootWindow, **kw):
        self.parent = parent
        window = self.window = Toplevel(parent)
        super().__init__(window, **kw)
        self.fig = None  # type: Figure
        self.ax = None
        self._update = False
        self.time = [1, 2, 3]
        self.data = {}
        self.power_data = {}
        self.current = [0, 0, 0]
        self.im_plot = None
        self.canvas = None
        self._artists = []
        self.plot_axes = []
        self.figure_setup()
        self.setup()
        self.ani = animation.FuncAnimation(self.fig, self.update_graph, interval=2000)

        parent.system_queue.add_info_callback('system.detector.get_data', self.add_data)
        parent.system_queue.add_info_callback('system.high_voltage.get_data', self.add_power_data)

    def setup(self):

        self.grid()

        canvas = FigureCanvasTkAgg(self.fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, columnspan=6)

        frame = Frame(self)
        frame.grid(row=1, column=0)
        toolbar = NavigationToolbar2Tk(canvas, frame)
        toolbar.update()
        # canvas.get_tk_widget().pack()
        self.canvas = canvas

        btn = ttk.Button(self, text='RESET', command=self.start_acquire)
        btn.grid()

    def start_acquire(self):
        self.parent.system_queue.send_command('system.detector.start')

    def add_data(self, data, *args, **kwargs):
        if data is not None:
            self.data = data
            self._update = True

    def add_power_data(self, data, *args, **kwargs):
        if data is not None:
            self.power_data = data
            self._update = True

    def figure_setup(self):
        self.fig = fig = Figure(figsize=(5, 4))
        gs = fig.add_gridspec(10, 1)
        ax1 = fig.add_subplot(gs[0:9])
        ax2 = ax1.twinx()
        ax1.set_ylabel('PMT (V)')
        ax2.set_ylabel('Current (uA)')
        ax2.set_ylim(-10, 100)
        self._artists = []
        self._artists.append(ax1.plot([0], [0], c='forestgreen')[0])
        self._artists.append(ax2.plot([0], [0], c='darkorange')[0])
        self.plot_axes = [ax1, ax2]
        ax1.set_title("CE Live View")

    def update_graph(self, *args):
        if self._update:
            self._update = False
            data = self.data
            power_data = self.power_data
            ax1, ax2 = self.plot_axes[0:2]
            try:
                ax1.set_xlim(min(data['time_data']), max(data['time_data']))
                ax1.set_ylim(min(data['rfu']) * 0.95, max(data['rfu'] * 1.05))
                ax2.set_ylim(0 * 0.7, max(power_data['current']) * 1.03)
                # ax2.set_ylim(min(power_data['current'])*0.95, max(power_data['current'])*1.05)
            except (ValueError, KeyError):
                return self._artists
            self._artists[0].set_data(data['time_data'], data['rfu'])
            self._artists[1].set_data(power_data['time_data'], power_data['current'])
            self.canvas.draw()
        return self._artists


class CameraWindow(Frame):

    def __init__(self, parent: RootWindow, **kw):
        self.parent = parent
        window = self.window = Toplevel(parent)
        super().__init__(window, **kw)
        self.fig = None
        self.ax = None
        self._update_img = False
        self.img = np.zeros((512, 512))
        self.im_plot = None
        self.canvas = None
        self.lower_var = DoubleVar(value=1)
        self.upper_var = DoubleVar(value=98)
        self.exposure_var = DoubleVar(value=100)
        self.exposure_var.trace('w', self.adjust_exposure)
        self.percentiles = [1, 98]

        self.figure_setup()
        self.setup()
        self.scalar = 0.75
        self.gamma = 1
        self.gain = 1

        self.ani = animation.FuncAnimation(self.fig, self.update_image, interval=2000)
        parent.system_queue.add_info_callback('system.camera.get_last_image', self.read_image)
        parent.system_queue.add_info_callback('system.camera.get_camera_dimensions', self.update_dims)

    def setup(self):

        self.grid()

        canvas = FigureCanvasTkAgg(self.fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, columnspan=6)

        frame = Frame(self)
        frame.grid(row=1, column=0)
        toolbar = NavigationToolbar2Tk(canvas, frame)
        toolbar.update()
        # canvas.get_tk_widget().pack()
        self.canvas = canvas

        reset_button = ttk.Button(self, text='acquire', command=self.reset_acquisition)
        reset_button.grid(row=2, column=0)

        snap_button = ttk.Button(self, text='Save Raw', command=self.snap_image)
        snap_button.grid(row=3, column=0)

        label = ttk.Label(self, text="Lower perc.")
        label.grid(row=2, column=1)
        spin_box = ttk.Spinbox(self, from_=0, to=100, increment=0.5, format="%.1f",
                               textvariable=self.lower_var)
        spin_box.grid(row=3, column=1)

        label = ttk.Label(self, text="Upper perc.")
        label.grid(row=2, column=2)
        spin_box = ttk.Spinbox(self, from_=0, to=100, increment=0.5, format="%.1f",
                               textvariable=self.upper_var)
        spin_box.grid(row=3, column=2)

        label = ttk.Label(self, text="Exposure (ms)")
        label.grid(row=2, column=3)
        spin_box = ttk.Spinbox(self, from_=0, to=10000, increment=10, format="%.1f",
                               textvariable=self.exposure_var)
        spin_box.grid(row=3, column=3)

    def reset_acquisition(self):
        """
        Stops and resets the camera continuous acquisition
        :return:
        """
        self.parent.system_queue.send_command("system.camera.stop")
        self.parent.system_queue.send_command("system.camera.continuous_snap")

    def figure_setup(self):
        self.fig = Figure(figsize=(5, 4))
        self.ax = self.fig.add_subplot(111)
        self.im_plot = self.ax.imshow(self.img)

    def read_image(self, img, *args, **kwargs):

        if img is not None and img != []:
            self.raw_image = img.copy()
            # print("LLL:{},{}".format(img, args))

            img = self._pre_plot_image(img)
            self.img = img
            self._update_img = True

    # noinspection PyUnresolvedReferences
    def update_image(self, *args):
        if self._update_img:
            self.im_plot.set_data(self.img)
            vmax = np.max(self.img)
            vmin = np.min(self.img)
            self.im_plot.set_clim(vmin, vmax)
            self._update_img = False
            self.canvas.draw()
        return [self.im_plot]

    def _pre_plot_image(self, image):
        # image = adjust_gamma(image, gamma=self.gamma, gain=self.gain)
        try:
            self.percentiles = [self.lower_var.get(), self.upper_var.get()]
        except Exception as e:
            pass

        print(self.percentiles)
        low, hi = np.percentile(image, self.percentiles)
        print(low, hi)
        img_rescale = exposure.rescale_intensity(image, in_range=(low, hi))
        print(img_rescale)
        return img_rescale

    def update_dims(self, data, *args):
        self.dims = data

    def snap_image(self, *args):
        img = self.raw_image.copy()
        file = filedialog.asksaveasfilename(defaultextension=".tif", filetypes=[("Raw Image Tiffs", "*.tif")])
        if file is not None:
            imsave(file, img)

    def adjust_exposure(self, *args):
        try:
            exp = self.exposure_var.get()
            if exp > 0:
                self.parent.system_queue.send_command('system.camera.set_exposure', exp)
        except Exception as e:
            print(e)


class InjectionData():
    """ Object to hold collection data"""

    def __init__(self, root_window: RootWindow):
        self.last_obj = None  # type: float
        self.difference = None  # type: float
        self.cap_z = None  # type: float
        self.obj_z = None  # type: float
        self.add_cap = False
        self.add_obj = False
        self.dif_var = DoubleVar()
        self.root_window = root_window
        root_window.system_queue.add_info_callback('system.objective.read_z', self.obj_callback)
        root_window.system_queue.add_info_callback('system.inlet_z.read_z', self.inlet_callback)

    def get_difference(self):
        if self.add_obj or self.add_cap:
            self.root_window.root.after(1000, self.get_difference)
        else:
            assert self.obj_z is not None or self.cap_z is not None, "Did not have objective or inlet positions recorded"
            self.difference = self.obj_z - self.cap_z
            self.dif_var.set(self.difference)
        print(self.difference)

    def get_cap_height(self, obj_height):
        assert self.difference is not None, "Difference must be calculated before calling get_cap_height"
        cap_height = obj_height - self.difference
        return cap_height

    def obj_callback(self, z, *args, **kwargs):
        if self.add_obj:
            self.obj_z = z
            self.add_obj = False
            print(z)

    def inlet_callback(self, z, *args, **kwargs):
        if self.add_cap:
            self.cap_z = z
            self.add_cap = False
            self.get_difference()


class InjectionWindow(Frame):
    """
    Displays control buttons for the CE system Controller
    """
    calibration = []

    def __init__(self, parent: RootWindow, **kw):
        window = self.window = Toplevel(parent)
        self.methods = []
        super().__init__(window, **kw)
        self.root_window = parent
        self.grid()
        self.time_var = DoubleVar()
        self.volt_var = DoubleVar()
        self.drop_var = DoubleVar()
        self.setup()

    def setup(self):

        # Calibration Control Buttons
        lf = ttk.LabelFrame(self, text='Objective-Capillary Calibration')
        lf.grid()
        bt = ttk.Button(lf, text='Set Objective Focus', command=self.objective_focus)
        bt.grid()
        bt = ttk.Button(lf, text='Set Capillary Focus', command=self.capillary_focus)
        bt.grid()
        spn = ttk.Spinbox(lf, from_=-0.5, to=10)
        spn.grid()

        # Capillary Adjustments
        lf = ttk.LabelFrame(self, text='Capillary Adjustments')
        lf.grid()
        bt = ttk.Button(lf, text='Lower Capillary', command=self.lower_cap)
        bt.grid(row=0, column=0)
        moves = [('-10', -0.01),
                 ('-5', -0.005),
                 ('-2', -0.002),
                 ('2', 0.002),
                 ('5', 0.005),
                 ('10', 0.01)]
        c_idx = 0
        r_idx = 1
        for lbl, dis in moves:
            bt = ttk.Button(lf, text=lbl,
                            command=lambda x=dis: self.root_window.system_queue.send_command('system.inlet_z.set_rel_z',
                                                                                             x))
            bt.grid(row=r_idx, column=c_idx)
            c_idx += 1

        # Injection Parameters
        lf = ttk.LabelFrame(self, text='Injection Parameters')
        lf.grid()
        params = [('Time (s)', self.time_var, 0, 1000),
                  ('Voltage (kV)', self.volt_var, 0, 1000),
                  ('Drop (mm)', self.drop_var, -10, 10)]
        c_idx = 0
        r_idx = 0
        for lbl, var, lw, hi in params:
            lb = ttk.Label(lf, text=lbl)
            lb.grid(row=r_idx, column=c_idx)
            sp = ttk.Spinbox(lf, from_=lw, to=hi, textvariable=var)
            sp.grid(row=r_idx + 1, column=c_idx)
            c_idx += 1
        btn = ttk.Button(lf, text='Start', command=self.start_injection)
        btn.grid(row=r_idx + 2, column=c_idx - 1)

        # Method Commands
        lf = ttk.LabelFrame(self, text='Method Control')
        lf.grid()
        btn = ttk.Button(lf, text='Continue Method', command=self.continue_run)
        btn.grid()

    def continue_run(self):
        self.root_window.system_queue.send_command('auto_run.continue_event.set')

    def start_injection(self):
        """Injection"""
        volts = self.volt_var.get()
        drop = self.drop_var.get()
        dt = self.time_var.get()

        # Make sure inputs are floats
        if type(volts) != float or type(drop) != float or type(dt) != float:
            return

        self.root_window.system_queue.send_command('auto_run.injection', dt, volts, drop)

    def objective_focus(self):
        self.root_window.injection_data.add_obj = True

    def capillary_focus(self):
        self.root_window.injection_data.add_cap = True

    def lower_cap(self):
        diff = self.root_window.injection_data.difference
        self.root_window.system_queue.send_command('auto_run.lower_dif', diff)


class MethodWindow(Frame):
    """
    Displays the Methods that will be run, their order, and their repetitions.
    """

    def __init__(self, parent: RootWindow, **kw):
        window = self.window = Toplevel(parent)
        self.methods = []
        super().__init__(window, **kw)

        text = Text(window, state='disabled', width=80, height=10, wrap='none')
        text['state'] = 'normal'
        text.insert('1.0+3c', 'Method Name \n', ('header'))
        text.tag_add('method_line', 1.0, 10.0)
        text.grid(row=0, column=0, columnspan=4, sticky="NSEW")
        text['state'] = 'disabled'
        text.tag_bind('method_line', '<<Selection>>', lambda event, text=text: print(text.tag_ranges('sel')))
        btn = ttk.Button(window, text="Add New", command=self.add_method)
        btn.grid(row=1, column=0, sticky="NSEW")

        btn = ttk.Button(window, text="Delete Selected", command=self.delete_method)
        btn.grid(row=1, column=1, sticky="NSEW")

        spin_label = ttk.Label(window, text="Repetitions")
        spin_label.grid(row=1, column=2, sticky="NSE")
        spin_box = ttk.Spinbox(window, from_=1, to=1000, increment=1)
        spin_box.set(1)
        self.reps = spin_box
        spin_box.grid(row=1, column=3, sticky="NSW")
        text.tag_ranges('sel')

        btn = ttk.Button(window, text="Start Run", command=self.start_method)
        btn.grid(row=2, column=2, sticky="NSEW")
        btn = ttk.Button(window, text="Stop Run", command=self.stop_method)
        btn.grid(row=2, column=3, sticky="NSEW")

        self.method_style = StringVar(value='CE')
        rd = ttk.Radiobutton(window, text='CE Style', variable=self.method_style, value='CE')
        rd.grid(row=2, column=0)
        rd = ttk.Radiobutton(window, text='CHIP Style', variable=self.method_style, value='CHIP')
        rd.grid(row=2, column=1)
        self.style = 'auto_run'
        self.text = text
        self.root_window = parent

    def add_method(self):
        f_name = filedialog.askopenfilename()
        if f_name is not None:
            self.methods.append(f_name)
            self.update_message()

    def update_message(self):
        self.text['state'] = 'normal'
        self.text.delete(1.0, END)
        self.text.insert(1.0, 'Method Name \n')
        for idx, line in enumerate(self.methods):
            self.text.insert(END, f'{idx + 1}   ' + line + '\n')
        self.text['state'] = 'disabled'

    def delete_method(self):
        try:
            start, stop = self.text.tag_ranges('sel')
            line_start = int(start.string.split('.')[0])
            # line_stop = int(stop.string.split('.')[0])
            self.methods.remove(self.methods[line_start - 2])
            self.update_message()
        except ValueError:
            pass

    def start_method(self):

        if self.method_style.get() == 'CE':
            style = 'auto_run'
        else:
            style = 'chip_run'
        value = self.reps.get()
        self.style = style

        self.root_window.system_queue.send_command(f'{style}.set_repetitions', value)
        for method in self.methods:
            self.root_window.system_queue.send_command(f'{style}.add_method', method)
        self.root_window.system_queue.send_command(f'{style}.start_run', simulated=False)

    def stop_method(self):
        self.root_window.system_queue.send_command(f'{self.style}.stop_run')


class TerminalWindow(Frame):

    def __init__(self, parent: RootWindow, **kw):
        window = Toplevel(parent)
        super().__init__(window, **kw)

        text = Text(window, state='disabled', width=80, height=10, wrap='none')
        text['state'] = 'normal'
        text.insert('1.0+3c', 'Terminal Inputs Name', ('header'))
        text.tag_add('method_line', 2.0, 10.0)
        text.grid(row=0, column=0, columnspan=4, sticky="NSEW")
        text['state'] = 'disabled'
        self.text = text

        parent.system_queue.add_error_callback(self.update_text)

    def update_text(self, level, msg):
        text = self.text
        text['state'] = 'normal'
        text.insert('end', "{}::{}".format(level, msg.replace('\\n', '\n')), (level))
        text['state'] = 'disabled'


if __name__ == "__main__":
    root = Tk()
    wn = RootWindow(root)
    root.protocol("WM_DELETE_WINDOW", wn.on_close)
    root.mainloop()
