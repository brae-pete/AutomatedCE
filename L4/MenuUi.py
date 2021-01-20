"""
This MenuUi module is used to create a text based tkinter GUI that can *easily* be modified.

The basic premise is to display a text menu where there are options identified by a number or string, and each option
is associated with a new menu to display, as well as optional input windows (for retrieving floats, integers, keywords,
etc...).

Multiple menu classes can be created  as a sub-menu of the MainMenu class. Each sub-menu can have its
own submenu, providing some decent organization.

Each menu class will have two properties, master, and parent. Master refers to the main menu on start up and contains
the 'global' objects (ie CESystem, AutoRun, etc...). Parent refers to the menu directly above.

Try to avoid creating too many Master properties when adding functionality. Probably best to keep those properties inside
the classes and objects responsible for the functionality when possible.

Several get_<type>_value functions can be used to retrieve the desired value from a pop up window. All these functions
follow the same format, user can pass in the message to display, the parent Tk window, and the value to return if
the user exits the window.

For a default UI the menu structure could be created as shown here:

MainMenu
    |_ SubMenu 1
        |_ SubMenu 1.1
        |_ SubMenu 1.2
        |_ SubMenu 1.3
    |_ SubMenu 2
        |_ SubMenu 2.1

"""
import tkinter
from tkinter import ttk
from abc import ABC, abstractmethod
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class Menu(ABC):
    """
    Menus Must have a options string property and an interpret method. This contains all of the options for the menu.
    The options menu will be appended with the footer string and header string.

    Option keywords or identifiers should be interpreted as strings, numbers can be used but should not be converted
    to numerical types.

    The option '0' and '00' should be reserved for returning to the parent menu, and main menu respectively.

    The interpret command should be customized to meet the needs of the menu. For each option listed there should be
    a conditional statement followed by the optional action (method or function) to be performed and return the menu
    object that should be displayed next (see interpret doc string)

    """

    parent_options = " No options were defined... "

    def __init__(self, master=None, parent=None):
        self.options = self.parent_options
        self.master = master  # type: Menu
        self.parent = parent  # type: Menu
        self.header = "\n\n"  # type: str
        self.footer = "0: Return to parent menu        00:Return to main menu"  # type: str

    @abstractmethod
    def interpret(self, text: str):
        """
        The option string identifier should be interpreted here. An example is given below for how this interpret
        command can be used.

        if text == '1':
            # Define an action to be performed, in this case get an integer number
            repetitions = GetInteger(msg = 'Enter # of Repetitions', ui_master = master.view)
            # Use the master to set this value if the user entered a value
            if repetitions is not None:
                self.master.auto_run.repetition = repetitions
            return self

        :param text: The user input from the GUI entry box
        :return: Returns the menu that should be displayed next for the UI
        :rtype: Menu
        """
        pass

    def get_options(self, *args, **kwargs):
        """
        Get the string that will be displayed, appending the header and footer. This can be adjusted as necessary
        to customize your headers and footers with updated information or other informational messages
        :return:
        """
        options = '\n' + self.header + '\n' + self.options + self.footer
        self.header = "" # Reset the header after it has been displayed
        self.footer = "0: Return to parent menu        00:Return to main menu"  # type: str
        return options

    def check_upper_menu_options(self, text: str):
        """
        Check if '0' or '00' have selected to return to parent menus. If they have return a True flag and the menu
        to return to.

        :param text:
        :return return_flag, menu: Returns a bool stating if a upper menu option was selected, and the menu to return to.
        :rtype : tuple(bool, Menu)
        """
        if text == '00':
            if self.master is not None:
                return True, self.master
            else:
                return True, self
        elif text == '0':
            if self.parent is not None:
                return True, self.parent
            else:
                return True, self
        else:
            return False, self

    def setup(self):
        """
        Any code that may need the root application reference can be executed inside the setup method
        :return:
        """
        pass


# Some helpful entry windows
def get_float_value(msg:str, root:tkinter.Tk, exit_value=None):
    """
    Use to get a single float value from the user.
    :param msg: message to display to user on what to enter
    :param root: the original TK() object
    :param exit_value: what to return if the user exits, None by default
    :return: value the user selected
    :rtype: float
    """
    window = FloatWindow(msg, root, exit_value)
    root.wait_window(window.top)
    return window.value


def get_string_value(msg:str, root:tkinter.Tk, exit_value=None):
    """
    Use to get a single string value from the user.
    :param msg: message to display to user on what to enter
    :param root: the original TK() object
    :param exit_value: what to return if the user exits, None by default
    :return: value the user selected
    :rtype: str
    """
    window = StringWindow(msg, root, exit_value)
    root.wait_window(window.top)
    return window.value


def get_integer_value(msg:str, root:tkinter.Tk, exit_value=None):
    """
    Use to get a integer float value from the user.
    :param msg: message to display to user on what to enter
    :param root: the original TK() object
    :param exit_value: what to return if the user exits, None by default
    :return: value the user selected
    :rtype: int
    """
    window = IntegerWindow(msg, root, exit_value)
    root.wait_window(window.top)
    return window.value


def get_options_value(msg:str, root:tkinter.Tk, options: list, exit_value=None):
    """
    Use to get a single option value from a list of options provided by the user.
    :param msg: message to display to user on what to enter
    :param root: the original TK() object
    :param options: list of options (strings) that the user can select from
    :param exit_value: what to return if the user exits, None by default
    :return: value the user selected
    :rtype: string
    """
    window = OptionWindow(msg, root, options, exit_value)
    root.wait_window(window.top)
    return window.value


class GraphWindow:

    def __init__(self, figure, parent):
        self.top = tkinter.Toplevel(parent)
        self.canvas = FigureCanvasTkAgg(figure, self.top)
        self.canvas.get_tk_widget().pack(expand=True)
        self.canvas._tkcanvas.pack( expand=True)


class PopupWindow(ABC):

    def __init__(self, msg, ui_master, exit_value=None):
        top = self.top = tkinter.Toplevel(ui_master)
        self.label = ttk.Label(top, text=msg)
        self.label.pack()
        self.value = exit_value
        self.input = ttk.Entry(top)
        self.enter = ttk.Button(top, text="Enter", command=self.cleanup)
        self.top.bind('<Return>', self.cleanup)

    def get_value(self):
        self.value = self.input.get()

    def cleanup(self, *args):
        self.get_value()
        self.top.destroy()


class StringWindow(PopupWindow):
    def __init__(self, msg, ui_master, exit_value=None):
        super().__init__(msg, ui_master, exit_value)
        self.input = ttk.Entry(self.top)
        self.input.pack()
        self.enter.pack()
        self.input.focus_set()


class FloatWindow(PopupWindow):
    def __init__(self, msg, ui_master, exit_value=None):
        super().__init__(msg, ui_master, exit_value)
        self.input = ttk.Spinbox(self.top, increment=0.1, format="%9.3f")
        self.input.pack()
        self.input.focus_set()
        self.enter.pack()

    def get_value(self):
        try:
            self.value = float(self.input.get())
        except ValueError:
            return None

class IntegerWindow(PopupWindow):

    def __init__(self, msg, ui_master, exit_value=None):
        super().__init__(msg, ui_master, exit_value)
        self.input = ttk.Spinbox(self.top, increment=1, format="%6.0f")
        self.input.pack()
        self.input.focus_set()

    def get_value(self):
        self.value = int(self.input.get())


class OptionWindow(PopupWindow):

    def __init__(self, msg, ui_master, options, exit_value=None):
        super().__init__(msg, ui_master, exit_value)
        self.input = ttk.Combobox(self.top,values=options)
        self.input.focus_set()

    def get_value(self):
        self.value = self.input.get()


class Application(ttk.Frame):
    """Pass in the Main Menu object to this application """
    message_header = "Please enter the number for the option below and press 'Send Command' \n"

    def __init__(self, master=None, main_menu=Menu):
        super().__init__(master)
        self.master = master

        # Set up the main menu and set our object to the main_menu view property
        self.menu = main_menu
        self.menu.view = self.master
        self._main = main_menu
        self.root = tkinter.Tk()
        self.pack()
        self.create_widgets(self.menu)
        self.menu.setup()

    def create_widgets(self, menu):
        self.message = tkinter.Text(self)
        msg = menu.get_options()
        self.message.insert(tkinter.INSERT, self.message_header + msg)
        self.message.pack()
        self.input = ttk.Entry(self)
        self.input.pack()
        self.send_button = ttk.Button(self)
        self.send_button['command'] = self.send_command
        self.send_button['text'] = 'Send Command'
        self.master.bind('<Return>', self.send_command)
        self.send_button.pack()

    def send_command(self, *args):
        """
        When the send command is pressed, updates the menu to the users selection, running a check if the user
        selected an option to return to the parent, or main menu before running the menu's interpret command.

        :param args:
        :return:
        """
        # Check if main menu first
        user_input = self.input.get()
        (go_up, menu) = self.menu.check_upper_menu_options(user_input)
        # if a go up option was not selected, interpret remaining options
        if not go_up:
            menu = self.menu.interpret(user_input)

        # Define the new menu
        self.menu = menu

        # Get the new menu options and replace the old ones
        options = self.menu.get_options()
        self.message.delete(2.0, tkinter.END)
        self.message.insert(tkinter.INSERT, options)

        # Delete the old input text
        self.input.delete(0, 'end')
