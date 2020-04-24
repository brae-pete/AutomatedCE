import threading
import time


class SingleAxis:
    """
    Motor simulation class to test program updates without running motors. Contains basic functions
    such as moving to a position and reading a position. Sets flags for when the motor arrives at a limit.

    """

    def __init__(self):
        self.set_position = 0
        self.last_command_time = time.time()
        self.last_read_time = time.time()
        self.last_command_position = 0
        self.max_velocity = 5  # units per second
        self.direction = 1  # Go forward (1) or reverse (-1)
        self.velocity_unit = "mm per s"
        self.max_limit = 100
        self.min_limit = 0
        self.max_limit_flag = threading.Event()
        self.min_limit_flag = threading.Event()

    def move_to(self, position):
        """
        Adjusts the velocity position equation. Resets the offset time_data and offset position. Adjusts the direction if
        needed. Changes the set or target position.

        >>>ax = SingleAxis()
        >>>ax.move_to(1)
        >>>True
        >>>time_data.sleep(1)
        >>>ax.get_position()
        >>>1.0

        :param position:
        :return:
        """

        self.last_command_position = self.get_position()
        self.last_command_time = self.last_read_time
        # Set the direction
        if self.last_command_position > position:
            self.direction = -1
        else:
            self.direction = 1
        self.set_position = position
        return True

    def jog(self, distance):
        """
        Moves the axis forward or backward by the specified distance. Uses the current position to determine how far to

        position

        >>>ax = SingleAxis()
        >>>ax.move_to(1)
        >>>True
        >>>time_data.sleep(1)
        >>>ax.get_position()
        >>>1.0

        :param distance:
        :return:
        """
        current_position = self.get_position()
        result = self.move_to(current_position+distance)
        return result

    def get_position(self):
        self.last_read_time = time.time()

        return self.direction * self.max_velocity * (self.last_command_time - self.last_read_time) + \
               self.last_command_position
