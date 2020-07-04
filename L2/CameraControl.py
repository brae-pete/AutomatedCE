import threading
from abc import ABC, abstractmethod
from L2.Utility import UtilityControl, UtilityFactory
from L1.Controllers import ControllerAbstraction
import time
import numpy as np

class CameraAbstraction(ABC):
    """
    Utility class for controlling camera hardware
    """

    def __init__(self, controller, role):
        self.controller = controller
        self.role = role
        self._callbacks = []
        self.last_image = []
        self.dimensions = [1,1] # Width and height of the image in pixels
        self.update_frequency = 4  # How many times per second to check the camera

        # Continuous properties
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
    def stop(self):
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

    def _update_callbacks(self, img):
        """
        Called during a continuous acquisition, sends new images to the callback functions.
        :param img: image (np.ndarray) to send to the callback functions
        :return:
        """

        for fnc in self._callbacks:
            fnc(img)
        return True


    @abstractmethod
    def set_exposure(self, exposure: int):
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


class PycromanagerControl(CameraAbstraction, UtilityControl):
    """
    Utility class for controlling camera hardware using Micromanager via Pycromanager library
    """
    def __init__(self, controller, role):
        super().__init__(controller, role)

    def _reshape(self, img:np.ndarray):
        return img.reshape(self.dimensions)

    def snap(self):
        """
        Take one image from the camera and return the image
        :return:
        """
        self.controller.send_command(self.controller.core.snap_image)
        img = self.controller.send_command(self.controller.core.get_image)
        return self._reshape(img)

    def _get_running(self):
        """
        Checks if sequence acquisition is running, returns True when running. False when not.
        :return: True/False if acquisition is running
        :rtype: bool
        """
        status = self.controller.send_command(self.controller.core.is_sequence_running)
        return status

    def continuous_snap(self):
        """
        Start continuous acquisition from the camera.
        :return:
        """
        if not self._get_running():
            self.controller.send_command(self.controller.core.start_continuous_sequence_acquisition, args=(1.0,))
            self._continuous_running.set()
            self._continuous_thread = threading.Thread(target=self._sequence_update)
            self._continuous_thread.start()

        return True

    def _sequence_update(self):
        """
        Reads the continuous acquisition buffer and sends the images to the functions
        listed inside the callback list.
        :return:
        """
        st = time.time()
        while self._continuous_running.is_set():
            images_ready = self.controller.send_command(self.controller.core.get_remaining_image_count)
            if images_ready > 0:
                img = self.controller.send_command(self.controller.core.get_last_image)
                self._update_callbacks(self._reshape(img))
            # Sleep until the next update time point
            time.sleep((time.time() - st) % (1 / self.update_frequency))

    def stop(self):
        """
        Stops the continuous acquisiton
        :return:
        """
        if self._get_running():
            self._continuous_running.clear()
            self._continuous_thread.join()
            self.controller.send_command(self.controller.core.stop_sequence_acquisition)
        return True

    def set_exposure(self, exposure: int):
        """
        Set the exposure in milliseconds
        :param exposure:
        :return:
        """
        exposure = float(exposure)
        self.controller.send_command(self.controller.core.set_exposure, args=(exposure,))
        return True

    def get_exposure(self):
        """
        Returns the camera's current exposure setting
        :return:
        """
        exposure = self.controller.send_command(self.controller.core.get_exposure)
        return exposure

    def startup(self):
        """
        Function to call on startup.
        :return:
        """
        h = self.controller.send_command(self.controller.core.get_image_height)
        w = self.controller.send_command(self.controller.core.get_image_width)
        self.dimensions = [h,w]
        return True

    def get_status(self):
        """
        Returns whether or not the continuous sequence is acquring
        :return:
        """
        return self._get_running()

    def shutdown(self):
        """
        Stops the continuous acquisition
        :return:
        """
        self.stop()
        return True


class MicroManagerCamera(CameraAbstraction, UtilityControl):
    """
    Camera control using the Micromanager controller class
    """

    def __init__(self, controller: ControllerAbstraction, role):
        super().__init__(controller, role)

    def snap(self):
        """
        Take and return a single image
        :return:
        """
        _ = self.controller.send_command('camera,snap\n')
        image = self.controller.send_command('camera,get_image\n')
        return image

    def continuous_snap(self):
        """
        Start the continuous image sequence
        :return:
        """
        _ = self.controller.send_command('camera,start_continuous\n')
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

    def stop(self):
        """
        Stops the continuous acquisition
        :return:
        """
        self.controller.send_command('camera,stop_continuous\n')
        self._continuous_running.clear()

    def set_exposure(self, exposure: float):
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
        self.stop()

    def get_status(self):
        """
        Return the continuous running status
        :return:
        """
        return {'camera': self._continuous_running.is_set()}


class CameraFactory(UtilityFactory):
    """ Determines the type of Camera Utility to return based off the controller being used"""

    def build_object(self, controller, role, *args):
        if controller.id == 'micromanager':
            return MicroManagerCamera(controller, role)
        elif controller.id == "pycromanager":
            return PycromanagerControl(controller, role)
        else:
            return None


if __name__ == "__main__":
    from L1.Controllers import MicroManagerController
    import time

    cont = MicroManagerController()
    cont.open()
    cc = MicroManagerCamera(cont)


    def update_log_screen(*args):
        print("New Image")


    cc.add_callback(update_log_screen)
    cc.continuous_snap()
    time.sleep(5)
    cc.stop()
