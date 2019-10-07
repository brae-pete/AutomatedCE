import sys
import os
import shutil
import cv2
import time
import numpy as np
import logging
from skimage import io
from skimage import exposure
from skimage import transform
from skimage.util import img_as_ubyte
from skimage.color import rgb2gray
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from pyvcam import pvc
from pyvcam.camera import Camera
import threading


"""
For Micromanager, you need to transfer the Micromanager 2.0 gamma folder from the barracuda PC to the computer you are 
working with. Alternatively you can try building a python 3 compatible Micromanager. 

For PVCAM, you will need to follow the install instructions for PVCAM python wrapper at https://github.com/Photometrics/PyVCAM
Be sure you have PVCAM, PVCAM SDK, Misrosoft Visual C++ Build Tools all installed before running the python setup.py install
command. 
Restart the PC after running python setup.py install

python version 3.7
skimage can be installed via 'conda install scikit-image'
cv2 can be installed via python -m pip install opencv_python
"""

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

CONFIG_FILE = os.path.join(CONFIG_FOLDER, "PVCAM.cfg")


class ImageControl:
    """GUI will read an image (recentImage). In mmc use Continuous sequence Acquisition
    Default uses micromanager (mmc). Instead you can use PVCAM shown below if using a PVCAM compatiable camera
    like the coolnap hq2
     """

    contrast_exposure = [2, 98]  # Low and high percintiles for contrast exposure
    rotate = 90
    _frame_num = 0
    _capture_ref=[]
    buffer_time = 30 # time to buffer images in seconds
    _capture_lock = threading.Lock()
    live_running=threading.Event()
    save_sequence = threading.Event()
    sequence_filepath = os.getcwd()
    sequence_prefix = "IMGS"
    capture_folder = os.path.join(sequence_filepath, 'Capture')

    def open(self):
        """Opens the camera resources"""
        pass

    def close(self):
        """ Closes the camera resources, called when program exits"""
        pass

    def stop_video_feed(self):
        """Stops the live video feed"""
        pass

    def get_single_image(self):
        """Snaps single image, returns image"""
        pass

    def start_video_feed(self):
        """ Starts a live video feed, typicall using camera circular buffer """
        pass

    def get_recent_image(self, size=None):
        """Returns most recent image from the camera circular buffer (live feed)
        performs image processing. Returns PIL image
        """
        pass

    def record_recent_image(self, filename):
        """ Saves recent image from circular buffer to designaed file"""
        pass

    def _get_image(self):
        """ Command that retrieves image from the camera"""
        pass

    def camera_state(self):
        """ Returns the camera state True is open, false is closed"""
        return False
    @staticmethod
    def _adjust_size(img, size):
        ims = img.shape
        if ims is None:
            return None

        new_ims = [0, 0]
        new_ims[0] = int(ims[0] * size)
        new_ims[1] = int(ims[1] * size)
        img = transform.resize(img, new_ims, anti_aliasing=True)
        return img

    @staticmethod
    def _rotate_img(img, rotation):
        if rotation == 0:
            return img
        return transform.rotate(img, 90, resize=True)

    def image_conversion(self, img):
        """ Adjusts the contrast and brightness"""
        p2, p98 = np.percentile(img, self.contrast_exposure)
        img_rescale = exposure.rescale_intensity(img, in_range=(p2, p98))
        return img_rescale

    @staticmethod
    def save_image(img, filename):
        """ Saves PIL image with filename"""
        io.imsave(filename, img)

    def live_view(self):
        """ Simple window to view the camera feed using matplotlib
         Live update is performed using the animate functionality in matplotlib

         """
        def animate(i):
            # Get an image
            img = self.get_recent_image()
            if img is not None:
                # put the image into the display data array
                im.set_array(img)
            return im,

        #initialize our matplotlib figure
        fig = plt.figure()
        self.start_video_feed()
        time.sleep(1)
        img = self.get_recent_image()
        im = plt.imshow(img, animated=True)

        # Calls the above animate function every 50 ms. Uses blit to reduce workload.
        ani = animation.FuncAnimation(fig, animate, interval=50, blit=True)
        plt.show()

    def capture_save(self, frame, passed_time):
        """ Saves a 30 s buffer of camera images.
         Ordered Dictionary where the first element is checked to see if it is more than 30 s old.
         If so that frame is deleted.

         A new frame is added to the dictionary with the time it was taken at in ms it was taken at
         as the key for the filename.

         Filename is the frame number.
         """
        # Check if capture folder exists
        if not os.path.exists(self.capture_folder):
            os.makedirs(self.capture_folder)

        # Save the frame to the file and add to the capture dictionary
        # Make this thread safe so we can save it without removing older frames
        with self._capture_lock:
            filepath = os.path.join(self.capture_folder,'{:09d}.png'.format(self._frame_num))
            self._capture_ref.append([passed_time,filepath])
            self.save_image(frame, filepath)
            self._frame_num += 1

            # Check if first frame in the buffer is older than the buffer period
            # Remove the expired file
            if passed_time -self._capture_ref[0][0] > self.buffer_time:
                _, old_file = self._capture_ref.pop(0)
                os.remove(old_file)

    def _get_unique_folder(self,parent,folder):
        """ Returns a unique folder name """
        tracker=0
        folder = folder +' ({})'.format(tracker)
        while os.path.exists(os.path.join(parent, folder)):
            tracker+=1
            folder = folder + ' ({})'.format(tracker)

        return folder

    def _clear_buffer(self):
        for file_del in os.listdir(self.capture_folder):
            file_path = os.path.join(self.capture_folder, file_del)
            if file_path.endswith('.png'):
                os.remove(file_path)
        return

    def save_capture_sequence(self, out_folder, name='capture_movie.avi', fps=5):
        """
        saves the capture buffer to a avi video and copies all of the formatted images (not originals)
        :param out_folder: folder to save, should not be the same as other buffers must be unique
        :param name: must end with .avi. What the video file will be called
        :param fps: frames per second
        :return:
        """
        capture_folder = os.path.join(out_folder, 'capture_sequence')
        if os.path.exists(capture_folder):
            logging.error('Output folder {}\n for capture sequence already exists'.format(capture_folder))
            capture_folder = os.path.join(out_folder, self._get_unique_folder(out_folder,'capture_sequence'))
            logging.error("New folder is {}".format(capture_folder))

        if name[-4:] != '.avi':
            logging.error('Image file name {} must end with .avi. Attempting to append'.format(name))
            name=name+'.avi'
        outfile = os.path.join(out_folder, name)

        # keep this thread safe, copy the files with a lock on the sequence
        with self._capture_lock:
            # copy the sequence to the destination
            shutil.copytree(self.capture_folder, capture_folder)

        # get all files in copied folder
        frames = [img for img in os.listdir(capture_folder) if img.endswith('.png')]
        frame = cv2.imread(os.path.join(capture_folder, frames[0]))
        height, width, layers = frame.shape

        # Save the video to avi format
        video = cv2.VideoWriter(outfile, 0, fps, (width, height))
        for frame in frames:
            img = cv2.imread(os.path.join(capture_folder, frame))
            video.write(img)
        video.release()


class PVCamImageControl(ImageControl):
    """GUI will read an image (recentImage). Uses PVCAM drivers.

    If the program is having difficulties loading the camera. Open the camera using PVCAM test. Make sure you can
    snap an image there. If so exit out and restart the GUI.

     """
    cam = None  # PV camera object
    exposure = 50  # ms exposure time
    contrast_exposure = [2, 98]  # Low and high percintiles for contrast exposure
    rotate = 90
    img = None  # Copy of the raw image before processing
    process_time = 0 # time it takes to process a single image for live feed
    name = 'None'
    serial_num = 'None'
    live_running=threading.Event()
    save_sequence = threading.Event()
    sequence_filepath = os.getcwd()
    sequence_prefix = "IMGS"
    capture_folder = os.path.join(sequence_filepath, 'Capture')
    sequence_start_time = time.perf_counter()
    _frame_num = 0
    _capture_ref=[]
    buffer_time = 30 # time to buffer images in seconds
    _capture_lock = threading.Lock()
    def __init__(self, lock = threading.RLock()):
        self.lock = lock
        self.open()
        # Clear the camera buffer
        self._clear_buffer()

    def open(self):
        """Opens the MMC resources"""
        try:
            pvc.init_pvcam()
        except RuntimeError:
            pvc.uninit_pvcam()
            pvc.init_pvcam()
        with self.lock:
            self.cam = next(Camera.detect_camera())
            self.cam.open()
            self.serial_num = self.cam.serial_no
            self.name = self.cam.name
            time.sleep(1)


    def close(self):
        self.cam.close()
        self.live_running.clear()
        pvc.uninit_pvcam()

    def camera_state(self):
        """ Returns the camera state True is open, false is closed"""
        return self.cam.is_open

    def stop_video_feed(self):
        if self.camera_state():
            with self.lock:
                self.cam.stop_live()
        self.live_running.clear()

    def get_single_image(self):
        """Snaps single image, returns image, for when live feed is not runniing"""
        with self.lock:
            image = self.cam.get_frame(self.exposure)
        return image

    def save_feed(self, filepath, prefix='IMGS'):
        self.sequence_filepath = filepath
        self.sequence_prefix = prefix
        self.sequence_start_time = time.perf_counter()
        with self.lock:
            self.save_sequence.set()

    def start_video_feed(self):
        """ starts continuous video feed  """
        with self.lock:
            self.cam.start_live(self.exposure)
            self.live_running.set()

    def get_recent_image(self, size=0.5, rotation=0):
        """Returns most recent image from the camera"""

        img = self._get_image()
        st = time.perf_counter() # Record when the picture was acquired

        # keep a copy of the original for debugging ( you could remove this )
        self.img = img.copy()
        # adjust size, rotation, brightness and contrast
        img = self._adjust_size(img, size)
        img = self._rotate_img(img, rotation)
        img = self.image_conversion(img)
        # convert to 8 bit image (with proper rescaling)
        img = img_as_ubyte(img)
        self.process_time = time.perf_counter()-st
        self.capture_save(img, st)
        return img

    def _get_image(self):
        """ Returns singe image when camera is in live feed """
        with self.lock:
            img = self.cam.get_live_frame()
        return img


class MicroManagerControl(ImageControl):
    """GUI will read an image (recentImage). In mmc use Continuous sequence Acquisition
    Default uses micromanager (mmc). Instead you can use PVCAM shown below if using a PVCAM compatiable camera
    like the coolnap hq2
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
                cfg = r'C:\KivyBarracuda\BarracudaQt\BarracudaQt\config\PVCAM.cfg'
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
            new_ims = [0, 0]
            new_ims[0] = ims[0] / 4
            new_ims[1] = ims[1] / 4
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
        io.imsave(filename, img)

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


if __name__ == "__main__":
    ic = PVCamImageControl()
