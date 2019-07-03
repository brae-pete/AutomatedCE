import sys
import os

# if r"C:\Micro-Manager-2.0gamma" not in sys.path:
#     sys.path.append(r"C:\Micro-Manager-2.0gamma")
# print(sys.path)
# os.chdir(r"C:\Micro-Manager-2.0gamma")

import MMCorePy
from PIL import Image as pilImage
import cv2
import time
import numpy as np
import logging

class ImageControl:
    """GUI will read an image (recentImage). In mmc use Continuous sequence Acquisition
     """
    def __init__(self, mmc = None, config ="C:\KivyBarracuda\ConfigFiles\QCam3Test.cfg", home = False):
        self.mmc = mmc
        self.config = config
        self.home = home
        if home:
            self.config = "C:\KivyBarracuda\ConfigFiles\DemoCam.cfg"
        if mmc is None:
            self.mmc = MMCorePy.CMMCore()
        self.open()
    def open(self):
        """Opens the MMC resources"""
        self.mmc.loadSystemConfiguration(self.config)

    def close(self):
        self.mmc.unloadAllDevices()

    def getSingleImage(self):
        """Snaps single image, returns image"""
        self.mmc.snapImage()
        image = self.mmc.getImage()
        return image


    def startVideoFeed(self):
        self.mmc.startContinuousSequenceAcquisition(1)

    def getRecentImage(self):
        """Returns most recent image from the camera"""
        if self.home:
            time.sleep(0.05)
        time.sleep(0.05)
        if self.mmc.getRemainingImageCount() > 0:
            img = self.mmc.getLastImage()
            img = self.imageConversion(img)
            try:
                img = pilImage.fromarray(img, 'L')
            except :
                img = pilImage.fromarray(img)
            return img

    def imageConversion(self,img):
        """ Adjusts the contrast and brightness"""
        equ = cv2.equalizeHist(img)
        return equ

