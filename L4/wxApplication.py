import multiprocessing as mp
import traceback
import sys
import os
from L3 import SystemsBuilder


class SystemsRoutine:
    """
    Class used to create a python process, a CE systems object, and send and interpret commands to and from
    the gui application.
    """

    def __init__(self):
        """
        """
        self.info_queue = mp.Queue()
        self.error_queue = mp.Queue()
        self.command_queue = mp.Queue()
        self.process = None

    def check_info_queue(self):
        """
        Checks the queue where data information from the Systems object will be sent.

        incoming command:
        (xystage.readxy, (data))
        (xystage.readxy, xy_stage_position, (data))
        command that was read, identifier for how to interpret the data, incoming data
        :return:
        """
        pass

    def check_error_queue(self):
        """
        Checks the error queue to see if the systems object has acquired an error.
        :return:
        """
        pass

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

    def send_command(self, cmd):
        self.command_queue.put(cmd)
        return


class SystemsInterpreter:
    """
    Class to control interpreting systems commands from the SystemsRoutine, running the commands on the systems object
    and returning the data or errors to the info or error queue's' respectively.
    """

    def __init__(self, info, error):
        self.info_queue = info
        self.error_queue = error
        self.system = SystemsBuilder.CESystem()

    def create_systems_object(self, config=None):
        """
        Opens the CE System object
        :param config:
        :return:
        """
        self.system = SystemsBuilder.CESystem()
        if config is not None:
            self.system.load_config(config)

    def interpret_and_respond(self, command, *args, **kwargs):
        """
        interprets an incoming command and runs the CE system object. When a response is required adds that to the
        appropriate queue.
        :param parent:
        :param utility:
        :param command:
        :param args:
        :param kwargs:
        :return:
        """

        try:
            if command.find('system') >= 0:
                _, utility, cmd = command.split('.')
                resp = self.system.__getattribute__(utility).__getattribute(cmd)(*args)
                self.info_queue.put((utility, cmd, resp))
            elif command == 'reset':
                try:
                    self.system.close_controllers()
                except Exception as e:
                    self.error_queue.put(e)
                self.create_systems_object(**kwargs)

        except Exception as e:
            self.error_queue.put(e)


def wait_n_read(info: mp.Queue, error: mp.Queue, command: mp.Queue):
    interpret = SystemsInterpreter(info, error)
    while True:
        try:
            cmd, args, kwargs = command.get()
            if cmd == 'stop':
                return 0
            interpret.interpret_and_respond(cmd, *args, **kwargs)
        except Exception as e:
            error.put(e)


if __name__ == "__main__":
    rout = SystemsRoutine()
    rout.start_process()
    rout.command_queue.put(("system.xy_stage.read_xy", (), {}))
