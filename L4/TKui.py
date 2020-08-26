from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from L3 import SystemsBuilder

class RootWindow(Frame):
    """
    Root contains all the buttons that will allow for subwindows to appear

    """

    def __init__(self, root, **kw):
        super().__init__(root, **kw)
        self.system = SystemsBuilder.CESystem()

        # Add the main Buttons
        system_button = ttk.Button(root, text='System', command=lambda x=self: CESystemWindow(x))
        system_button.grid(column=0, row=0)

        init_button = ttk.Button(root, text="Init", command=lambda x=self: InitFrame(x))
        init_button.grid(column=1, row=0)

        method_button = ttk.Button(root, text='Method', command=lambda x=self: MethodWindow(x))
        method_button.grid(column=2, row=0)

        egram_button = ttk.Button(root, text='Egram')
        egram_button.grid(column=3, row=0)

        egram_button = ttk.Button(root, text='Camera')
        egram_button.grid(column=4, row=0)

        egram_button = ttk.Button(root, text='Terminal')
        egram_button.grid(column=5, row=0)

        root.title('Automated Chip')


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

    def __init__(self, parent, z_name, **kw):
        super().__init__(parent, **kw)

        defaults = {'z_name': 'z_stage'}
        defaults.update(kw)

        self.name = z_name
        self.z_stage_readout = StringVar(value="{} Position:  mm".format(self.name))

        self.setup()

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


class XYExpandable(CollapsiblePane):
    """
    XY Expandable Frame allows user to control the most important aspects of the XY stage.
    XY position is displayed in mm,
    the absolute or relative position can be set using a combination of spin boxes and buttons
    """

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)

        self.xy_stage_readout = StringVar(value="X: mm Y: mm")
        self.setup()

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


class CESystemWindow(Frame):

    def __init__(self, parent, **kw):
        window = Toplevel(parent)
        super().__init__(window, **kw)

        window.title('System Controls')
        xy_stage_label = ttk.Label(window, text='XY Stage')
        xy_stage_label.grid(row=0, column=0, sticky="NEW")
        self.xy_stage_frame = XYExpandable(window)
        self.xy_stage_frame.grid(row=0, column=1, sticky="NSEW")

        objective_label = ttk.Label(window, text='Objective Z ')
        objective_label.grid(row=1, column=0, sticky="NEW")
        self.objective_frame = ZExpandable(window, z_name='objective')
        self.objective_frame.grid(row=1, column=1, sticky="NSEW")

        outlet_label = ttk.Label(window, text='Outlet Z ')
        outlet_label.grid(row=2, column=0, sticky="NEW")
        self.outlet_z_frame = ZExpandable(window, z_name='Outlet')
        self.outlet_z_frame.grid(row=2, column=1, sticky="NSEW")

        inlet_label = ttk.Label(window, text='Inlet Z ')
        inlet_label.grid(row=3, column=0, sticky="NEW")
        self.inlet_z_frame = ZExpandable(window, z_name='Inlet')
        self.inlet_z_frame.grid(row=3, column=1, sticky="NSEW")


class InitFrame(Frame):

    def __init__(self, parent, **kw):
        self.window = window = Toplevel(parent)
        super().__init__(window, **kw)
        self.setup()

    def setup(self):
        window = self.window

        # Instructions Frame
        instruction_frame = ttk.Frame(window)
        instruction_frame.grid(row=0, column=0, rowspan=2)

        header_lbl = ttk.Label(instruction_frame, text='Initialize System')
        header_lbl.grid(row=0, column=0)

        step_1_lbl = ttk.Label(instruction_frame, text=" 1. Load the System ")
        step_1_lbl.grid()

        step_1_file_button = ttk.Button(instruction_frame, text='Select Config',
                                        command=lambda: filedialog.askopenfilename())
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


root = Tk()
wn = RootWindow(root)

root.mainloop()
