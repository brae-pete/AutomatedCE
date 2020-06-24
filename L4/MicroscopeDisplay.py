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


class DisplayAbstraction(ABC):
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


class MatplotlibDisplay(DisplayAbstraction):

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
            self._ani_func = animation.FuncAnimation(self.fig, self._update, interval =100, blit=True)

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


