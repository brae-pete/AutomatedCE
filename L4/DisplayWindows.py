"""
Modules for displaying images from a microscope. Live or snapped.
"""
import logging
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

    def __init__(self, detector, voltage_supply):
        """
        Creates a CE display object with the following properities.
        lock: threading lock to access data and plots in a thread safe way
        detector: Detector object from the Utilities folder that contains a get_data function.
        :param detector: Detector object from Utilities that contains the processed data
        :param voltage_supply: Power supply object from utilities that contains current and voltage information
        """
        self.lock = threading.Lock()
        self.detector = detector
        self.voltage_supply = voltage_supply

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
    def add_trace(self, time_data, rfu_data, **kwargs):
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

    def __init__(self, detector, voltage_supply):
        super().__init__(detector, voltage_supply)
        self.fig = None
        self.plot_axes = []
        self._ani_func = None
        self._artists = []
        self.show()

    def show(self):
        """
        Creates a matplot figure and defines the figure and image axes.
        :return:
        """
        self.fig = fig = plt.figure()
        gs = fig.add_gridspec(10, 1)
        ax1 = fig.add_subplot(gs[0:9])
        ax2 = ax1.twinx()
        ax1.set_ylabel('PMT (V)')
        ax2.set_ylabel('Current (uA)')
        self._artists = []
        self._artists.append(ax1.plot([0], [0], c='forestgreen')[0])
        self._artists.append(ax2.plot([0], [0], c='darkorange')[0])
        self.plot_axes = [ax1, ax2]
        ax1.set_title("CE Live View")
        plt.show(block=False)

    def start_live_view(self):
        """
        Create the animation function which will update automatically as long
        as there is a reference to it.
        :return:
        """
        if self._ani_func is None:
            self._ani_func = animation.FuncAnimation(self.fig, self._animate, interval=500, blit=False)
        logging.debug("Started")
        self.fig.canvas.draw()

    def stop_live_view(self):
        """
        Stop the animation function
        being updated.
        :return:
        """
        self._ani_func.event_source.stop()
        self._ani_func = None

    def add_trace(self, time_data, rfu_data, **kwargs):
        """
        Adds electropherogram with a given filename to the plot.
        Adds to the list of artists (beyond the first two default artists)
        :param time_data: list of time points to plot
        :param rfu_data: list of fluorescent data points to plot
        :param kwargs: matplotlib plot keywords
        :return:
        """
        settings = {'label': 'trace'}
        settings.update(**kwargs)
        with self.lock:
            ax1 = self.plot_axes[0]
            self._artists.append(ax1.plot(time_data, rfu_data, **settings)[0])

    def remove_trace(self, **kwargs):
        """
        Removes all auxillary traces from the electropherograms
        :param kwargs:
        :return:
        """
        with self.lock:
            self._artists = self._artists[0:2]

    def _animate(self, *args):
        """
        Gets data from the detector and plots it on the plotting axes.
        Data object from detector is a dictionary with keys being either Time or RFU

        :param args:
        :return: list of artists for animation function
        """

        data = self.detector.get_data()
        power_data = self.voltage_supply.get_data()
        ax1, ax2 = self.plot_axes[0:2]
        ax1.set_xlim(min(data['time_data']),max(data['time_data']))
        ax1.set_ylim(min(data['rfu'])*0.95, max(data['rfu']*1.05))
        ax2.set_ylim(min(power_data['current'])*0.95, max(power_data['current'])*1.05)
        self._artists[0].set_data(data['time_data'], data['rfu'])
        self._artists[1].set_data(power_data['time_data'], power_data['current'])
        return self._artists
