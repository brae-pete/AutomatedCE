from tkinter import *
from tkinter import ttk
from tkinter import filedialog

from skimage.exposure import adjust_gamma, exposure
from skimage.transform import resize

from L3 import SystemsBuilder
from L4 import SystemQueue
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
        # Add the main Buttons
        system_button = ttk.Button(root, text='System', command=lambda x=self: CESystemWindow(x))
        system_button.grid(column=0, row=0)

        init_button = ttk.Button(root, text="Init", command=lambda x=self: InitFrame(x))
        init_button.grid(column=1, row=0)

        method_button = ttk.Button(root, text='Method', command=lambda x=self: MethodWindow(x))
        method_button.grid(column=2, row=0)

        egram_button = ttk.Button(root, text='Egram')
        egram_button.grid(column=3, row=0)

        egram_button = ttk.Button(root, text='Camera', command=lambda x=self: CameraWindow(x))
        egram_button.grid(column=4, row=0)

        egram_button = ttk.Button(root, text='Terminal', command=lambda x=self: TerminalWindow(x))
        egram_button.grid(column=5, row=0)

        root.title('Automated Chip')

        root.after(1000, self.check_queues)

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
        self.setup()
        root.system_queue.add_info_callback("system.{}.read_z".format(z_name), self.read_z)

    def setup(self):
        lbl = ttk.Label(self.frame)
        lbl.grid(row=0, column=0)
        lbl['textvariable'] = self.z_stage_readout

        up_btn = ttk.Button(self.frame)
        up_btn.grid(column=0, row=1)

        down_btn = ttk.Button(self.frame)
        down_btn.grid(column=0, row=2)

        lbl_z = ttk.Label(self.frame, text="{} Z position: ".format(self.name))
        lbl_z.grid(column=0, row=3)
        spin_z = ttk.Spinbox(self.frame)
        spin_z.grid(column=1, row=3)
        lbl_z_unit = ttk.Label(self.frame, text=" mm ")
        lbl_z_unit.grid(column=2, row=3)

        go_btn = ttk.Button(self.frame)
        go_btn.grid(column=1, row=4)

    def read_z(self, z, *args):
        self.z_stage_readout.set(z)


class XYExpandable(CollapsiblePane):
    """
    XY Expandable Frame allows user to control the most important aspects of the XY stage.
    XY position is displayed in mm,
    the absolute or relative position can be set using a combination of spin boxes and buttons
    """

    def __init__(self, parent, root, **kw):
        super().__init__(parent, **kw)

        self.xy_stage_readout = StringVar(value="X: mm Y: mm")
        self.setup()
        root.system_queue.add_info_callback("system.xy_stage.read_xy", self.read_xy)

    def setup(self):
        """
        Places all the buttons into their respective positions.
        :return:
        """
        lbl = ttk.Label(self.frame)
        lbl['textvariable'] = self.xy_stage_readout
        lbl.grid(column=0, row=0, columnspan=3)

        up_btn = ttk.Button(self.frame, text="Up")
        up_btn.grid(row=1, column=1)
        down_btn = ttk.Button(self.frame, text="Down")
        down_btn.grid(row=3, column=1)
        left_btn = ttk.Button(self.frame, text="Left")
        left_btn.grid(row=2, column=0)
        right_btn = ttk.Button(self.frame, text="Right")
        right_btn.grid(row=2, column=2)

        x_lbl = ttk.Label(self.frame, text="X: ")
        x_lbl.grid(row=4, column=0)
        x_spin = ttk.Spinbox(self.frame)
        x_spin.grid(row=4, column=1)
        x_lbl_unit = ttk.Label(self.frame, text=" mm")
        x_lbl_unit.grid(row=4, column=2)

        y_lbl = ttk.Label(self.frame, text="Y: ")
        y_lbl.grid(row=5, column=0)
        y_spin = ttk.Spinbox(self.frame)
        y_spin.grid(row=5, column=1)
        y_lbl_unit = ttk.Label(self.frame, text=" mm")
        y_lbl_unit.grid(row=5, column=2)

        go_btn = ttk.Label(self.frame, text="Go!")
        go_btn.grid(row=6, column=2)

    def read_xy(self, xy, *args):
        try:
            self.xy_stage_readout.set("X: {:.3f} Y: {:.3f}".format(xy[0], xy[1]))
        except:
            self.xy_stage_readout.set("incoming: {}".format(xy))


class CESystemWindow(Frame):

    def __init__(self, parent: RootWindow, **kw):
        window = Toplevel(parent)
        super().__init__(window, **kw)

        window.title('System Controls')

        reset_button = ttk.Button(window, text="Reset", command=parent.system_queue.start_process)
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


class InitFrame(Frame):

    def __init__(self, parent: RootWindow, **kw):
        self.window = window = Toplevel(parent)
        super().__init__(window, **kw)
        self.setup()
        self.parent = parent

    def setup(self):
        """ Place the buttons"""
        window = self.window

        # Instructions Frame
        instruction_frame = ttk.Frame(window)
        instruction_frame.grid(row=0, column=0, rowspan=2)

        header_lbl = ttk.Label(instruction_frame, text='Initialize System')
        header_lbl.grid(row=0, column=0)

        step_1_lbl = ttk.Label(instruction_frame, text=" 1. Load the System ")
        step_1_lbl.grid()

        step_1_file_button = ttk.Button(instruction_frame, text='Select Config',
                                        command=self.set_config)
        step_1_file_button.grid()

        step_2_lbl = ttk.Label(instruction_frame, text='2. Load the Template')
        step_2_lbl.grid()

        step_2_btn = ttk.Button(instruction_frame, text='Select Template', command=lambda: filedialog.askopenfilename())
        step_2_btn.grid()

        step_3_lbl = ttk.Label(instruction_frame, text="3. Calibrate the CE Apparatus")
        step_3_lbl.grid()

        step_4_lbl = ttk.Label(instruction_frame, text="4. Calibration Check")
        step_4_lbl.grid()

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


class CameraWindow(Frame):

    def __init__(self, parent: RootWindow, **kw):
        self.parent = parent
        window = self.window = Toplevel(parent)
        super().__init__(window, **kw)
        self.fig = None
        self.ax = None
        self._update_img = False
        self.img = np.zeros((512, 512))
        self.im_plot= None
        self.canvas = None

        self.figure_setup()
        self.setup()
        self.scalar = 0.75
        self.gamma = 1
        self.gain = 1
        self.percentiles = [0.05, 0.95]
        self.ani = animation.FuncAnimation(self.fig, self.update_image, interval=2000)
        parent.system_queue.add_info_callback('system.camera.get_last_image', self.read_image)
        parent.system_queue.add_info_callback('system.camera.get_camera_dimensions', self.update_dims)

    def setup(self):

        self.grid()

        canvas = FigureCanvasTkAgg(self.fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, columnspan=2)

        frame = Frame(self)
        frame.grid(row=1, column=0)
        toolbar = NavigationToolbar2Tk(canvas, frame)
        toolbar.update()
        #canvas.get_tk_widget().pack()
        self.canvas = canvas

        reset_button = ttk.Button(self, text='acquire', command=self.reset_acquisition)
        reset_button.grid(row=1, column=1)

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
        self.im_plot= self.ax.imshow(self.img)

    def read_image(self, img, *args, **kwargs):
        if img is not None and img != []:
            print("LLL:{},{}".format(img, args))

            img = self._pre_plot_image(img)
            self.img = img
            self._update_img = True

    # noinspection PyUnresolvedReferences
    def update_image(self, *args):
        print(self.img.max())
        if self._update_img:
            print("UU")
            self.im_plot.set_data(self.img)
            vmax = np.max(self.img)
            vmin = np.min(self.img)
            self.im_plot.set_clim(vmin, vmax)
            self._update_img = False
            self.canvas.draw()
        return [self.im_plot]

    def _pre_plot_image(self, image):
        #image = adjust_gamma(image, gamma=self.gamma, gain=self.gain)
        low, hi = np.percentile(image, self.percentiles)

        img_rescale = exposure.rescale_intensity(image, in_range=(low, hi))
        return image

    def update_dims(self, data, *args):
        self.dims = data


class MethodWindow(Frame):
    """
    Displays the Methods that will be run, their order, and their repetitions.
    """

    def __init__(self, parent, **kw):
        window = self.window = Toplevel(parent)
        super().__init__(window, **kw)

        text = Text(window, state='disabled', width=80, height=10, wrap='none')
        text['state'] = 'normal'
        text.insert('1.0+3c', 'Method Name', ('header'))
        text.tag_add('method_line', 2.0, 10.0)
        text.grid(row=0, column=0, columnspan=4, sticky="NSEW")
        text['state'] = 'disabled'
        text.tag_bind('method_line', '<<Selection>>', lambda event, text=text: print(text.tag_ranges('sel')))

        btn = ttk.Button(window, text="Add New")
        btn.grid(row=1, column=0, sticky="NSEW")

        btn = ttk.Button(window, text="Delete Selected")
        btn.grid(row=1, column=1, sticky="NSEW")

        spin_label = ttk.Label(window, text="Repetitions")
        spin_label.grid(row=1, column=2, sticky="NSE")
        spin_box = ttk.Spinbox(window)
        spin_box.grid(row=1, column=3, sticky="NSW")

        text.tag_ranges('sel')


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
