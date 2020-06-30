"""
Modules for displaying images from a microscope. Live or snapped.
"""
import queue
import threading
from abc import ABC, abstractmethod
from queue import Queue

import matplotlib.pyplot as plt
from matplotlib import animation

from L3.SystemsBuilder import CESystem
from skimage.exposure import adjust_gamma


class MicroscopeDisplayAbstraction(ABC):
    """
    Each Display should have a few basic commands.

    Display should show the image, which brings up a window, or some sort of visual with the image displayed.
    Display should also allow user control over the brightness and contrast of the image

    Display should be able to get a Single Image
    Display should be able to get a livestream of images.
    """

    def __init__(self, system: CESystem):
        self.gain = 1.0
        self.gamma = 1.0
        self.lock = threading.Lock()
        self.system = system

    @abstractmethod
    def show(self):
        """
        Displays the image in a window or other visual representation.
        :return:
        """

    def adjust_gamma(self, gamma: float, gain=1.0):
        """
        Adjusts brightness of an image using Gamma correction. G
        :param brightness_scalar: must be a nonnegative number
        :return:
        """
        with self.lock:
            self.gamma = gamma
            self.gain = gain
        return True

    @abstractmethod
    def single_image(self):
        """
        Retrieves a single image from the source and displays it in the window. Updates the window image if an image
        is already present
        :return:
        """

    @abstractmethod
    def live_image(self):
        """
        Retrieves a live stream of images from the source and continuously updates them in the window.
        :return:
        """


class PLTMicroscopeDisplay(MicroscopeDisplayAbstraction):

    def __init__(self, system: CESystem):
        super().__init__(system)
        self.fig = None
        self.img_ax = None
        self.im = None
        self.queue = Queue(maxsize=1)
        self.system.camera.add_callback(self._update)
        self._ani_func = None

    def show(self):
        self.fig = fig = plt.figure()
        gs = fig.add_gridspec(10, 1)
        self.img_ax = fig.add_subplot(gs[0:9])
        self.img_ax.set_title("Camera View")
        plt.show()
        self.single_image()

    def single_image(self):
        img = self.system.camera.snap()
        img = self._pre_plot_image(img)
        with self.lock:
            self.im = self.img_ax.imshow(img)

    def _pre_plot_image(self, image):
        image = adjust_gamma(image, gamma=self.gamma, gain=self.gain)
        return image

    def live_image(self):
        self.system.camera.continuous_snap()
        if self._ani_func is None:
            self._ani_func = animation.FuncAnimation(self.fig, self._update, interval=100, blit=True)

    def stop_live_image(self):
        self.system.camera.stop()
        self._ani_func = None

    def _update(self, img):
        try:
            self.queue.put_nowait(img)
        except queue.Full:
            return

    def _animate(self, *args):
        try:
            img = self.queue.get_nowait()
            img = self._pre_plot_image(img)
            self.im.set_array(img)
            return self.im,

        except queue.Empty:
            return self.im,


class CEDisplayAbstraction(ABC):
    """
    Displays the CE electropherogram and updates as the plot updates.
    """

    def __init__(self, detector):
        """
        Creates a CE display object with the following properities.
        lock: threading lock to access data and plots in a thread safe way
        detector: Detector object from the Utilities folder that contains a get_data function.
        :param detector: Detector object from Utilities that contains the processed data
        """
        self.lock = threading.Lock()
        self.detector = detector

    @abstractmethod
    def show(self):
        """
        Displays the window containing the electropherogram
        :return:
        """

    @abstractmethod
    def start_live_view(self):
        """
        Starts updating the plot's live view
        :return:
        """

    @abstractmethod
    def stop_live_view(self):
        """
        Stops updating the plots live view
        :return:
        """

    @abstractmethod
    def add_trace(self, filename, **kwargs):
        """
        Adds an electropherogram trace from previously acquired data
        :return:
        """

    @abstractmethod
    def remove_trace(self, **kwargs):
        """
        Removes all electropherogram traces from the plots
        :param kwargs:
        :return:
        """


class PLTCEDisplay(CEDisplayAbstraction):

    def __init__(self, detector):
        super().__init__(detector)
        self.fig = None
        self.img_ax = None
        self.show()

    def show(self):
        """
        Creates a matplot figure and defines the figure and image axes.
        :return:
        """
        self.fig = fig = plt.figure()
        gs = fig.add_gridspec(10, 1)
        self.img_ax = fig.add_subplot(gs[0:9])
        self.img_ax.set_title("CE Live View")
        plt.show()

    def start_live_view(self):
        pass

    def stop_live_view(self):
        pass

    def add_trace(self, filename, **kwargs):
        pass

    def remove_trace(self, **kwargs):
        pass
