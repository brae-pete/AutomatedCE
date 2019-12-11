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

try:
    from pyvcam import pvc
    from pyvcam.camera import Camera
except ModuleNotFoundError:
    logging.warning("PVCam is not installed")

import threading

try:
    from hardware import MicroControlClient
except:
    sys.path.append(os.path.relpath('..'))
    from hardware import MicroControlClient

"""
Notes for using this outside the Barracuda Repository: 

For Micromanager, you will need to install Python2 and use the Micromanager Communication Client. 
Micromanager is not python3 compatible so we create a separate python process in the communication client
that runs the Micromanager library. This library communicates over a local port specified by the client.

For PVCAM, you will need to follow the install instructions for PVCAM python wrapper at https://github.com/Photometrics/PyVCAM
Be sure you have PVCAM, PVCAM SDK, Misrosoft Visual C++ Build Tools all installed before running the python setup.py install
command. 
Restart the PC after running python setup.py install

python version 3.7
skimage can be installed via 'conda install scikit-image'
cv2 can be installed via python -m pip install opencv_python
"""

io.use_plugin('pil')

# Locate the directory of config files
cwd = os.getcwd()
contents = os.listdir(cwd)

if "config" in contents:
    CONFIG_FOLDER = os.path.join(cwd, "config")
elif "ImageControl.py" in contents:
    CONFIG_FOLDER = os.path.relpath('../config')
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

    contrast_exposure = [0.5, 99]  # Low and high percintiles for contrast exposure
    rotate = 90
    _frame_num = 0
    _capture_ref = []
    buffer_time = 30  # time to buffer images in seconds
    _capture_lock = threading.Lock()
    live_running = threading.Event()
    save_sequence = threading.Event()
    sequence_filepath = os.getcwd()
    sequence_prefix = "IMGS"
    capture_folder = os.path.join(sequence_filepath, 'Capture')
    raw_img = np.array((100, 100))  # Full raw image
    is_live = threading.Event()

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

    def get_exposure(self):
        """ Returns camera exposure in milliseconds as a float"""
        pass

    def set_exposure(self, exp):
        """ Sets the camera exposure. Exp is exposure in milliseconds as a float"""
        pass

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
        #img = img.astype(np.float64)
        img = transform.rotate(img, rotation, resize=True)
        #img = img.astype(np.uint16)
        return img

    @staticmethod
    def rotate_raw_img(img, rotation):
        img = img.astype(np.float64)
        img = transform.rotate(img, rotation, resize=True)
        img = img.astype(np.uint16)
        return img

    def image_conversion(self, img):
        """ Adjusts the contrast and brightness"""
        low, p98 = np.percentile(img, self.contrast_exposure)
        img_rescale = exposure.rescale_intensity(img, in_range=(low, p98))
        return img_rescale

    def modify_img(self,img,  size, rotation):
        # Process image for live feed
        img = self._adjust_size(img, size)
        img = self._rotate_img(img, rotation)
        img = self.image_conversion(img)
        img = img_as_ubyte(img)

        return img

    @staticmethod
    def save_image(img, filename):
        """ Saves PIL image with filename"""
        io.imsave(filename, img)

    def save_raw_image(self, filename):
        """ Saves last raw image"""
        io.imsave(filename, self.raw_img)

    def live_view(self):
        """ Simple window to view the camera feed using matplotlib
         Live update is performed using the animate functionality in matplotlib

         """

        def animate(i):
            # Get an image
            if self.is_live.is_set():
                img = self.get_recent_image()
            else:
                img = None
            if img is not None:
                # put the image into the display data array
                im.set_array(img)
            return im,

        # initialize our matplotlib figure
        fig = plt.figure()
        self.start_video_feed()
        time.sleep(1)
        img = self.get_recent_image()
        im = plt.imshow(img, animated=True)
        self.is_live.set()

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
            filepath = os.path.join(self.capture_folder, '{:09d}.png'.format(self._frame_num))
            self._capture_ref.append([passed_time, filepath])
            self.save_image(frame, filepath)
            self._frame_num += 1

            # Check if first frame in the buffer is older than the buffer period
            # Remove the expired file
            if passed_time - self._capture_ref[0][0] > self.buffer_time:
                _, old_file = self._capture_ref.pop(0)
                try:
                    os.remove(old_file)
                except Exception as e:
                    logging.error("Image Error...{}".format(e))


    def _get_unique_folder(self, parent, folder):
        """ Returns a unique folder name """
        tracker = 0
        folder = folder + ' ({})'.format(tracker)
        while os.path.exists(os.path.join(parent, folder)):
            tracker += 1
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
            capture_folder = os.path.join(out_folder, self._get_unique_folder(out_folder, 'capture_sequence'))
            logging.error("New folder is {}".format(capture_folder))

        if name[-4:] != '.avi':
            logging.error('Image file name {} must end with .avi. Attempting to append'.format(name))
            name = name + '.avi'
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
    contrast_exposure = [0.5, 99]  # Low and high percintiles for contrast exposure
    rotate = 90
    img = None  # Copy of the raw image before processing
    process_time = 0  # time it takes to process a single image for live feed
    name = 'None'
    serial_num = 'None'
    live_running = threading.Event()
    save_sequence = threading.Event()
    sequence_filepath = os.getcwd()
    sequence_prefix = "IMGS"
    capture_folder = os.path.join(sequence_filepath, 'Capture')
    sequence_start_time = time.perf_counter()
    _frame_num = 0
    _capture_ref = []
    buffer_time = 30  # time to buffer images in seconds
    _capture_lock = threading.Lock()
    size = 0.5

    def __init__(self, lock=threading.RLock()):
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
        """Snaps single image, returns image, for when live feed is not running"""

        with self.lock:
            image = self.cam.get_frame(self.exposure)
            self.raw_img = image
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
        st = time.perf_counter()  # Record when the picture was acquired

        # keep a copy of the original for debugging ( you could remove this )
        self.raw_img = img.copy()
        # adjust size, rotation, brightness and contrast
        img = self._adjust_size(img, size)
        img = self._rotate_img(img, rotation)
        img = self.image_conversion(img)
        # convert to 8 bit image (with proper rescaling)
        img = img_as_ubyte(img)
        self.process_time = time.perf_counter() - st
        self.capture_save(img, st)
        return img

    def _get_image(self):
        """ Returns singe image when camera is in live feed """
        with self.lock:
            img = self.cam.get_live_frame()
        return img


class MicroControl(ImageControl):
    """GUI will read an image (recentImage). In mmc use Continuous sequence Acquisition
    Default uses micromanager (mmc). Instead you can use PVCAM shown below if using a PVCAM compatiable camera
    like the coolnap hq2
     """
    state = False
    device_name = 'CoolCam'  # Updated after configuation has been loaded
    size = 0.5
    raw_img = np.ndarray((512,512))

    def __init__(self, mmc=None, port = 6412, config_file='CoolSnap.cfg', lock = threading.Lock()):
        self.mmc = mmc
        self.lock = lock
        self.config = os.path.join(CONFIG_FOLDER, config_file)
        self._open_client(port)
        self.open()

    def _open_client(self,port):
        """Opens the micromanager communicator client"""
        if self.mmc is None:
            self.mmc = MicroControlClient.MicroControlClient(port=port)

        self.mmc.open()

    def _close_client(self):
        """ Closes the client resources, called when program exits"""
        self.mmc.close()

    def open(self):
        """ Opens the camera resources """
        # Load the Config
        with self.lock:
            self.mmc.send_command('core,load_config,{}'.format(self.config))
            response = self.mmc.read_response()
            msg = "Could not open Camera"
            state = self.mmc.ok_check(response, msg)
            if not state:
                return state

            # Get Camera Name
            self.mmc.send_command('camera,get_name\n')
            self.device_name = str(self.mmc.read_response().decode())
            self.state = True
        return self.mmc.ok_check(response, msg)

    def close(self):
        """Closes the camera resources
        """
        with self.lock:
            self.mmc.send_command('core,unload_device,{}\n'.format(self.device_name))
            response = self.mmc.read_response()
            msg = "Could not close camera resources"
            self.state = False
        return self.mmc.ok_check(response, msg)

    def _snap_image(self):
        """Sends command to snap single image to the camera. """
        with self.lock:
            self.mmc.send_command('camera,snap\n')
            response = self.mmc.read_response()
        msg = 'Failed to Snap Image'
        state = self.mmc.ok_check(response, msg)
        return state

    def get_single_image(self):
        """Snaps single image, returns image"""
        with self.lock:
            st = time.perf_counter()
            state = self._snap_image()
            if not state:
                return self.raw_img
            self.mmc.send_command('camera,get_image\n')
            img = self.mmc.read_response()
            if type(img) is not np.ndarray:
                logging.error("Could not get image {}".format(img))
                return img
            # todo add image processing
            self.raw_img = img.copy()
        img = self.modify_img(img,0.5,270)
        self.capture_save(img, st)
        return img

    def set_exposure(self, exp=10):
        """ Sets the camera exposure im milliseconds"""
        with self.lock:
            self.mmc.send_command('camera,set_exposure,{}\n'.format(exp))
            response = self.mmc.read_response()
        msg = "Could not set camera exposure"
        return self.mmc.ok_check(response, msg)

    def get_exposure(self):
        with self.lock:
            self.mmc.send_command('camera,get_exposure\n')
            exp = self.mmc.read_response()
        if type(exp) is not float:
            logging.error("Could not get exposure: {}".format(exp))
            return 10
        return exp

    def start_video_feed(self):
        """ Starts a live video feed, typicall using camera circular buffer """
        self.is_live.set()
        with self.lock:
            self.mmc.send_command('camera,start_continuous\n')
            response = self.mmc.read_response()
        msg = "Could not start live video feed"
        return self.mmc.ok_check(response, msg)

    def stop_video_feed(self):
        """Stops the live video feed"""
        self.is_live.clear()
        with self.lock:
            self.mmc.send_command('camera,stop_continuous\n')
            response = self.mmc.read_response()
        msg = "Could not stop live video feed"

        return self.mmc.ok_check(response, msg)

    def get_recent_image(self, size=0.5, rotation=270):
        """Returns most recent image from the camera circular buffer (live feed)
        performs image processing. Returns PIL image
        """
        with self.lock:
            self.mmc.send_command('camera,get_last\n')
            st = time.perf_counter()
            img = self.mmc.read_response()
            if type(img) is not np.ndarray:
                logging.error("Could not get image {}".format(img))
                time.sleep(0.3)
                return None
        # Preserve the original picture (this is saved for Tiff files)
            self.raw_img = img.copy()
        # Process image for live feed
            img = self._adjust_size(img, size)
            img = self._rotate_img(img, rotation)
            img = self.image_conversion(img)
            img = img_as_ubyte(img)
            self.process_time = time.perf_counter() - st
        self.capture_save(img, st)
        return img

    def camera_state(self):
        """ Returns the camera state True is open, false is closed"""
        return self.state


class TestImageControl(ImageControl):
    """
    Image control testing for a given signal. It uses randomly generated spheres (circles) over a grid. Depending on the
    XY coordinates given, TestImageControl will return the corresponding set of spheres. This is Test class is for
    testing object movements and cell finding logic.
    >>>ic=TestImageControl()
    >>>img = ic.get_single_image()
    >>>img.shape == ic.camera_shape
    True
    """
    def __init__(self):
        self.camera_shape = [720, 1280]


if __name__ == "__main__":
    ic = MicroControl()
