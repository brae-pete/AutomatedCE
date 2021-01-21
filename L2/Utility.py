from abc import ABC, abstractmethod


class UtilityControl(ABC):
    """
    Each hardware  class in Layer 2 should be a subclass of this class. These are methods that will be common to
    all hardware classes and include the startup procedure (homing the hardware, setting default values, etc...),
    retrieving the current status of the hardware, and the shutdown procedure (moving to home, setting default values,
    etc...).

    The hardware abstraction class will further specialize each subclass but Utility control should remain generalizable
    for all hardware components.
    """
    def __init__(self, controller):
        self.controller=controller

    @abstractmethod
    def startup(self):
        pass

    @abstractmethod
    def get_status(self):
        pass

    @abstractmethod
    def shutdown(self):
        pass

    @abstractmethod
    def stop(self):
        pass

class UtilityFactory(ABC):

    """
    Each hardware factory will implement a build_object functionality that reads the daqcontroller ID
    then determines what type of UtilityControl class to use.
    """

    @abstractmethod
    def build_object(self, controller, role, *args):
        """Use the daqcontroller ID to determine what type of daqcontroller will be used for the utility. Then select the
        appropriate UtilityControl class that matches that daqcontroller and return the object
        """
        pass

