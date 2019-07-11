import sys
import os
from PIL import Image as pilImage
import cv2
import time
import numpy as np
import logging

if r"C:\Program Files\Micro-Manager-2.0gamma" not in sys.path:
    sys.path.append(r"C:\Program Files\Micro-Manager-2.0gamma")
prev_dir = os.getcwd()
os.chdir(r"C:\Program Files\Micro-Manager-2.0gamma")

import MMCorePy

os.chdir(prev_dir)

# Locate the directory of config files
cwd = os.getcwd()
contents = os.listdir(cwd)

if "config" in contents:
    CONFIG_FOLDER = os.path.join(cwd, "config")
elif "BarracudaQt" in contents:
    contents = os.listdir(os.path.join(contents, "BarracudaQt"))
    if "config" in contents:
        os.chdir(os.path.join(contents, "BarracudaQt"))
        CONFIG_FOLDER = os.path.join(os.getcwd(), "config")
    else:
        CONFIG_FOLDER = os.getcwd()
else:  # fixme prompt for program folder if it is not the cwd or within the cwd.
    CONFIG_FOLDER = os.getcwd()

CONFIG_FILE = os.path.join(CONFIG_FOLDER, "QCam3Test.cfg")


class ImageControl:
    """GUI will read an image (recentImage). In mmc use Continuous sequence Acquisition
     """
    def __init__(self, mmc=None, config=None, home=False):
        self.mmc = mmc
        self.config = config
        self.home = home

        if mmc is None:
            self.mmc = MMCorePy.CMMCore()
        if not home:
            self.open()

    def open(self):
        """Opens the MMC resources"""
        self.mmc.loadSystemConfiguration(CONFIG_FILE)

    def close(self):
        self.mmc.unloadAllDevices()

    def get_single_image(self):
        """Snaps single image, returns image"""
        self.mmc.snapImage()
        image = self.mmc.getImage()
        return image

    def start_video_feed(self):
        self.mmc.startContinuousSequenceAcquisition(1)

    def get_recent_image(self):
        """Returns most recent image from the camera"""
        if self.home:
            time.sleep(0.05)
        time.sleep(0.05)
        if self.mmc.getRemainingImageCount() > 0:
            img = self.mmc.getLastImage()
            img = self.image_conversion(img)
            try:
                img = pilImage.fromarray(img, 'L')
            except:  # fixme, pin down the exceptions we want to include here, don't use broad.
                img = pilImage.fromarray(img)
            return img

    @staticmethod
    def image_conversion(img):
        """ Adjusts the contrast and brightness"""
        equ = cv2.equalizeHist(img)
        return equ

