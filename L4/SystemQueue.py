import multiprocessing as mp
import traceback
import sys
import os
from L3 import SystemsBuilder
from L4 import AutomatedControl

class SystemsRoutine:
    """
    Class used to create a python process, a CE systems object, and send and interpret commands to and from
    the gui application.

    It is beneficial for the CE system object to live in a different process so that all resources (hardware
    resources especially) can be reset without resetting the main python interface.

    Communication between the systems object and the python interface takes place using queues where the queues are
    read and their commands run.

    In addition to the CE System object, there will also be an auto_run object. This will handle the automation tasks
    required by the System.
    """

    def __init__(self):
        """
        """
        self.info_queue = mp.Queue() # Queue that contains data from the CE system
        self.error_queue = mp.Queue() # Queueue that contains error messages from the CE system
        self.command_queue = mp.Queue() # Queue that contains commands sent to the CE system
        self.process = None # Python Process containing the CE system
        self.updates={} # Dictionary of command msgs and a list of callbacks to call for each data recieved
        self.error_updates=[] # List of callbacks to send the error information to
        self.update_commands = [] # List of commands that will be sent periodically

    def check_info_queue(self):
        """
        Checks the queue where data information from the Systems object will be sent.

        incoming command:
        (xystage.readxy, (data))
        (xystage.readxy, xy_stage_position, (data))
        command that was read, identifier for how to interpret the data, incoming data
        :return:
        """

        while not self.info_queue.empty():
            msg, data = self.info_queue.get()
            if msg in self.updates.keys():
                self.updates[msg](*data)

    def check_error_queue(self):
        """
        Checks the error queue to see if the systems object has acquired an error.
        :return:
        """
        while not self.error_queue.empty():
            level, msg = self.error_queue.get()
            for fnc in self.error_updates:
                try:
                    fnc(level, msg)
                except Exception as e:
                    print("Terminal Error: removing")
                    self.error_updates.remove(fnc)


    def start_process(self):
        """
        Starts a fresh python process
        :return:
        """
        self.process = mp.Process(target=wait_n_read, args=(self.info_queue, self.error_queue,
                                                            self.command_queue))
        self.process.start()

    def stop_process(self):
        self.command_queue.put(('stop', (), {}))

    def get_error(self):
        """
        returns an error if any is in the queue
        :return:
        """
        if not self.error_queue.empty():
            return self.error_queue.get()

    def send_command(self, cmd, *args, **kwargs):
        self.command_queue.put((cmd, args, kwargs))
        return

    def add_info_callback(self, msg, fnc):
        """
        Adds a callback to a given system function where a return data is expected
        :param msg: string command given to the system
        :param fnc: callback function
        :return:
        """

        if msg not in self.updates.keys():
            self.updates[msg]=[]
        self.updates[msg].append(fnc)
        self.add_update_command(msg)

    def add_error_callback(self, fnc):
        """
        Adds a callback that will be called when the error queue is checked
        :param fnc:
        :return:
        """
        self.error_updates.append(fnc)

    def add_update_command(self, msg):
        """
        Adds a command msg to the list of commands that will be sent during the send_updates
        :param msg: command  message for the system
        :return:
        """
        if msg not in self.update_commands:
            self.update_commands.append(msg)

    def send_updates(self):
        """
        Sends update commands to the system
        :return:
        """
        for msg in self.update_commands:
            self.send_command(msg)
        return


class SystemsInterpreter:
    """
    Class to control interpreting systems commands from the SystemsRoutine, running the commands on the systems object
    and returning the data or errors to the info or error queue's' respectively.
    """

    def __init__(self, info, error):
        self.info_queue = info
        self.error_queue = error
        self.system = SystemsBuilder.CESystem
        self.auto = AutomatedControl.AutoRun

    def create_systems_object(self, config=None):
        """
        Opens the CE System object
        :param config:
        :return:
        """
        self.system = SystemsBuilder.CESystem()
        if config is not None:
            self.system.load_config(config)
        self.auto.system = self.system

    def create_auto_object(self):
        """
        Creates an AutoRun object from Automated Control
        :return:
        """
        self.auto = AutomatedControl.AutoRun(self.system)

    def interpret_and_respond(self, command, *args, **kwargs):
        """
        interprets an incoming command and runs the CE system object. When a response is required adds that to the
        appropriate queue.

        Example commands would be:

        system.xy_stage.read_xy  ---> This will read the xy_stage
        system.objective.set_rel_z, 5  -----> This will set the the objective relative hight 5 mm higher


        :param command: String command that matches either a CE_system utility method or AutoRun method.
        :param args:
        :param kwargs:
        :return:
        """

        try:
            # Identify which component to control, CE System (system), AutoRun (auto_run), or reset.
            if command.find('system') >= 0:
                _, utility, cmd = command.split('.')
                self.error_queue.put(("info", "{}::{}".format(utility, cmd)))
                resp = self.system.__getattribute__(utility).__getattribute(cmd)(*args)
                self.info_queue.put((command, resp))
            elif command.find('auto_run')>=0:
                _, cmd = command.split('.')
                resp = self.system.__getattribute__(cmd)(*args)
                self.info_queue.put(('auto_run', cmd, resp))
            elif command == 'reset':
                try:
                    self.system.close_controllers()
                except Exception as e:
                    self.error_queue.put(('error-3',"{}::{}".format(e,command)))
                self.create_systems_object(**kwargs)

        except Exception as e:
            a,b,c = sys.exc_info()
            self.error_queue.put(("traceback", "{}\n {}\n Line Number {}\n".format(a,c.tb_frame.f_code.co_filename,c.tb_lineno)))
            self.error_queue.put(('error-2',"{}::{}\n".format(e,command)))


def wait_n_read(info: mp.Queue, error: mp.Queue, command: mp.Queue):
    interpret = SystemsInterpreter(info, error)
    while True:
        try:
            cmd, args, kwargs = command.get()
            if cmd == 'stop':
                return 0
            interpret.interpret_and_respond(cmd, *args, **kwargs)
        except Exception as e:
            error.put(('error-1',e))


if __name__ == "__main__":
    rout = SystemsRoutine()
    rout.start_process()
    rout.command_queue.put(("system.xy_stage.read_xy", (), {}))
