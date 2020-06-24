"""
Modules for displaying images from a microscope. Live or snapped.
"""
from abc import ABC, abstractmethod

class DisplayAbstraction(ABC):

    """
    Each Display should have a few basic commands.

    Display should show the image, which brings up a window, or some sort of visual with the image displayed.
    Display should also allow user control over the brightness and contrast of the image

    Display should be able to get a Single Image
    Display should be able to get a livestream of images.
    """

    @abstractmethod
    def show(self):
        """
        Displays the image in a window or other visual representation.
        :return:
        """

    @abstractmethod
    def set_brightness(self, brightness_scalar:float):
        """
        Sets the brightness to the pixel values passed in.
        :param brightness_scalar: value to scale brightness by. when > 0, increase brightness.
        :return:
        """

    @abstractmethod
    def get_brightness(self):
        """
        Returns the current setting of the brightness scalar
        :return: brightness_scalar value where >0 increases brightness
        :rtype: float
        """

    @abstractmethod
    def set_contrast(self):
        """
        Sets the contrast of the image
        :return:
        """

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

