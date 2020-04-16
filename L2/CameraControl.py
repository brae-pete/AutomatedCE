import threading
from abc import ABC, abstractmethod
from L2.Utility import UtilityControl, UtilityFactory
from L1.Controllers import ControllerAbstraction


class CameraAbstraction(ABC):
    """
    Utility class for controlling camera hardware
    """

    def __init__(self, controller):
        self.controller = controller
        self._callbacks = []
        self.last_image = []

        #Continuous properties
        self._continuous_thread = threading.Thread()
        self._continuous_running = threading.Event()

    @abstractmethod
    def snap(self):
        """
        Take one image from the camera and return the image
        :return:
        """

    @abstractmethod
    def continuous_snap(self):
        """
        Start continuous acquisition from the camera
        :return:
        """

    @abstractmethod
    def stop_continuous(self):
        """
        Stops the continuous acquisiton
        :return:
        """
        pass


    def add_callback(self, function):
        """
        Add function to call during continuous acquisition
        :param function:
        :return:
        """
        self._callbacks.append(function)

    @abstractmethod
    def set_exposure(self, exposure:int):
        """
        Set the exposure in milliseconds
        :param exposure:
        :return:
        """
        pass

    def get_exposure(self):
        """
        Returns the camera's current exposure setting
        :return:
        """
        pass


class MicroManagerCamera(CameraAbstraction, UtilityControl):

    """
    Camera control using the Micromanager controller class
    """

    def __init__(self, controller : ControllerAbstraction):
        super().__init__(controller)

    def snap(self):
        """
        Take and return a single image
        :return:
        """
        response = self.controller.send_command('camera,snap\n')
        image = self.controller.send_command('camera,get_image\n')
        return image

    def continuous_snap(self):
        """
        Start the continuous image sequence
        :return:
        """
        response = self.controller.send_command('camera,start_continuous\n')
        self._continuous_running.set()
        self._continuous_thread = threading.Thread(target=self._continuous_callback)
        self._continuous_thread.start()

    def _continuous_callback(self):
        """
        Retieves the most recent image from the camera circular buffer. Forwards that picture to the releavent
        image callbacks. Runs on its own thread.
        :return:
        """

        while self._continuous_running.is_set():
            image = self.controller.send_command('camera,get_last\n')
            for func in self._callbacks:
                func(image)

    def stop_continuous(self):
        """
        Stops the continuous acquisition
        :return:
        """
        self.controller.send_command('camera,stop_continuous\n')
        self._continuous_running.clear()


    def set_exposure(self, exposure:int):
        """
        Sets the camera exposure in milliseconds
        :param exposure:
        :return:
        """
        self.controller.send_command('camera,set_exposure,{}\n'.format(exposure))

    def get_exposure(self):
        """
        Returns the camera's current exposure setting
        :return:
        """
        return self.controller.send_command('camera,get_exposure\n')

    def startup(self):
        """
        Set exposure to 100 on start up
        :return:
        """
        self.set_exposure(100)

    def shutdown(self):
        """
        Make sure continuous acquisiton is stopped
        :return:
        """
        self.stop_continuous()

    def get_status(self):
        """
        Return the continuous running status
        :return:
        """
        return {'camera':self._continuous_running.is_set()}


if __name__ == "__main__":
    from L1.Controllers import MicroManagerController
    import time
    cont = MicroManagerController()
    cont.open()
    cc = MicroManagerCamera(cont)

    def update_log_screen(image,*args):
        print("New Image")

    cc.add_callback(update_log_screen)

    cc.continuous_snap()
    time.sleep(5)
    cc.stop_continuous()

