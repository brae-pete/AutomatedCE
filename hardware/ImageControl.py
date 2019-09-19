import sys
import os
from PIL import Image as pilImage
import cv2
import time
import numpy as np
import logging
from skimage import io, data, img_as_float
from skimage import exposure
from skimage import transform
from skimage.color import rgb2gray
import matplotlib.pyplot as plt
import matplotlib.animation as animation


io.use_plugin('pil')

if r"C:\Program Files\Micro-Manager-2.0gamma" not in sys.path:
    sys.path.append(r"C:\Program Files\Micro-Manager-2.0gamma")
prev_dir = os.getcwd()
os.chdir(r"C:\Program Files\Micro-Manager-2.0gamma")

MMCOREPY_FATAL = False

try:
    import MMCorePy
except ImportError:
    logging.error('Can not import MMCorePy.')
    if MMCOREPY_FATAL:
        sys.exit()
else:
    logging.info('MMCorePy successfully imported.')

os.chdir(prev_dir)

# Locate the directory of config files
cwd = os.getcwd()
contents = os.listdir(cwd)

if "config" in contents:
    CONFIG_FOLDER = os.path.join(cwd, "config")
elif "CEGraphic" in contents:
    contents = os.listdir(os.path.join(contents, "CEGraphic"))
    if "config" in contents:
        os.chdir(os.path.join(contents, "CEGraphic"))
        CONFIG_FOLDER = os.path.join(os.getcwd(), "config")
    else:
        CONFIG_FOLDER = os.getcwd()
else:  # fixme prompt for program folder if it is not the cwd or within the cwd.
    CONFIG_FOLDER = os.getcwd()

CONFIG_FILE = os.path.join(CONFIG_FOLDER, "QCam3Test.cfg")


class ImageControl:
    """GUI will read an image (recentImage). In mmc use Continuous sequence Acquisition
     """

    contrast_exposure = [2, 98]  # Low and high percintiles for contrast exposure
    rotate = 90
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
        try:
            self.mmc.loadSystemConfiguration(CONFIG_FILE)
        except MMCorePy.CMMError:
            self.close()
            time.sleep(1)
            try:
                cfg = r'C:\KivyBarracuda\BarracudaQt\BarracudaQt\config\DemoCam.cfg'
                self.mmc.loadSystemConfiguration(cfg)
            except MMCorePy.CMMError:
                logging.warning("Could not load camera")

    def close(self):
        self.mmc.unloadAllDevices()

    def stop_video_feed(self):
        if not self.home:
            if self.mmc.isSequenceRunning():
                self.mmc.stopSequenceAcquisition()

    def get_single_image(self):
        """Snaps single image, returns image"""
        self.mmc.snapImage()
        image = self.mmc.getImage()
        return image

    def start_video_feed(self):
        if not self.home:
            self.mmc.startContinuousSequenceAcquisition(1)

    def get_recent_image(self, size=None):
        """Returns most recent image from the camera"""
        if self.home:
            time.sleep(0.25)

        time.sleep(0.1)
        if self.mmc.getRemainingImageCount() > 0:
            img = self.mmc.getLastImage()
            ims = img.shape
            # From bring back from 32 bit to 3 rgb channels
            img = img.view(dtype=np.uint8).reshape(ims[0], ims[1], 4)[..., 2::-1]  # img = np.float32(img)
            new_ims=[0,0]
            new_ims[0] = ims[0]/4
            new_ims[1] = ims[1]/4
            img = transform.resize(img, new_ims, anti_aliasing=True)
            img = transform.rotate(img, 90, resize=True)
            img = rgb2gray(img)
            self.img = img.copy()
            img = self.image_conversion(img)
            """
            try:
                img = pilImage.fromarray(img, 'L')
            except:
                img = pilImage.fromarray(img)
            """
            return img

    def record_recent_image(self, filename):
        if self.home:
            time.sleep(0.25)
        img = self._get_image()
        ims = img.shape
        img = img.view(dtype=np.uint8).reshape(ims[0], ims[1], 4)[..., 2::-1]
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(filename, img)

    def _get_image(self):
        try:
            img = self.mmc.getLastImage()
        except MMCorePy.CMMError:
            time.sleep(0.15)
            img = self._get_image()
        return img

    def image_conversion(self, img):
        """ Adjusts the contrast and brightness"""
        p2, p98 = np.percentile(img, self.contrast_exposure)
        img_rescale = exposure.rescale_intensity(img, in_range=(p2, p98))
        return img_rescale

    @staticmethod
    def save_image(img, filename):
        io.imsave(filename,img)

    def live_view(self):

        def animate(i):
            img = self.get_recent_image()
            if img is not None:
                im.set_array(img)
            return im,

        fig = plt.figure()
        try:
            self.start_video_feed()
        except MMCorePy.CMMError:
            logging.WARNING("Continuous already starting")
        time.sleep(1)
        img = self.get_recent_image()
        im = plt.imshow(img, animated=True)
        ani = animation.FuncAnimation(fig, animate, interval=50, blit=True)
        plt.show()
