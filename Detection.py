import os
import random
import threading

import cv2
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib import patches
import skimage
from PIL import Image
from skimage import filters
from skimage.morphology import watershed, erosion,square,diamond, dilation, remove_small_holes, remove_small_objects
from skimage.measure import label, regionprops
from skimage.feature import peak_local_max
from scipy import ndimage as ndi
from scipy.spatial import distance
import logging
import numpy as np
import time

try:
    from BarracudaQt import CESystems
except ModuleNotFoundError:
    import CESystems

CENTER = [3730, -1957]
RADIUS = 5000
LASER = [ 760,442] # x, y


def get_blobs(img, fl_img=None, scale=1):
    """ This is the main function for getting cell objects from an image. You can test this function against
    test images to see if the blobs you are getting out match up with the cells.
    Adjust the scale and threshold as you see fit to get good cell sucess.

    Scales is according to CoolSnap Hq, 20x objective. Scale of 1 assumes no scaling

    """
    # Adjust the local threshold spread, must be odd
    spread = round(51*scale)
    if spread%2 ==0:
        spread += 1

    # Subtract the background
    img = np.asarray(img)
    thresh = filters.threshold_local(img, spread)
    filt_img = (img - thresh)

    # Get the edges
    edges = filters.sobel(filt_img)

    # Threshold mask on edges
    thresh = filters.threshold_mean(edges)
    bw_mask = (edges > thresh)

    # Dilation
    dilated = dilation(bw_mask, square(1))

    # Remove small holes
    filled = remove_small_holes(dilated, 2000 * scale)

    # Remove small objects
    eroded = erosion(filled, diamond(2))
    thinned = remove_small_objects(eroded, 2000 * scale)

    # Watershed
    distance = ndi.distance_transform_edt(thinned)
    area = round(scale * 20)
    local_maxi = peak_local_max(distance, indices=False, footprint=np.ones((area, area)),
                                labels=thinned)
    markers = ndi.label(local_maxi)[0]
    labels = watershed(-distance, markers, mask=thinned)

    if fl_img is not None:
        try:
            props = regionprops(labels, np.asarray(fl_img))
        except ValueError:
            logging.error("{} and {} are shapes of BF and FL".format(labels.shape, np.asarray(fl_img).shape))
            props = regionprops(labels)
    else:
        props = regionprops(labels)

    return props
USER = os.getcwd()
class CellDetector:
    """
    Detects cells using morphological filters
    Compares againts previous lysis points
    Moves to first cell outside threhold of excluded points
    """
    excluded_xy = []
    excluded_minimum = 100  # distance from previous laser lysis spot
    move_distance = 250
    img_shape = [250, 250]  # This will change to whatever the image shape is
    blob_exclusion_image = r"recentImg.png" # Path to empty image (no cells, just the dust and noise on the lens)
    max_diameter = 200  # Maximum radius in ums, anything larger will be excluded.
    min_diameter = 15
    debug = False
    thresh = 0.1
    scale = 1
    last_blob_xy = None
    current_blob = None
    fl_threshold = 195

    def __init__(self, hardware, pix2um=0.4329, laser_spot = LASER):
        """

        :param pix2um: float, conversion scalar from scaled image to um
        :param laser_spot: xy position in um
        :param hardware: xy and image control required
        """
        self.pix2um = pix2um
        # Laser spot is recorded in X (column) and Y (row)
        self.laser_spot = laser_spot
        self.hardware = hardware

        if USER.find('NikonEclipse')>0:
            self.blob_exclusion_image = r"C:\Users\NikonEclipseTi\Documents\Barracuda\EasyAccess\Background.png"



        if self.debug:
            self._start_plots()
        self.background_blobs = self._get_background_blobs()

    def _start_plots(self):
        self.fig, self.axes = plt.subplots()
        return

    def mover_find_cell(self, mover,xy = None, fl=None):
        """
        Automated cell finding algorithm
        :param mover: Mover Object, moves to random locations
        :return:
        """
        if xy is None:
            xy = self.hardware.get_xy()
        cell = self.find_cell(fl)
        starting = 0
        while not cell and starting < 10:
            xy = mover.move_random(xy)
            self.hardware.set_xy(xy)
            time.sleep(0.5)
            cell = self.find_cell()
        return cell

    def find_cell(self, fl=None):
        """
        Find and move to a cell using a morphological process outlined in the get_blobs
        function
        fl = Tuple of [Filter_Channel, Exposure Setting] for fluorescence image
        :return: True if a cell was found, False if a cell was not found
        """
        if fl is not None:
            img = self.hardware.get_image()
            img = self.hardware.get_raw_image()
            fl = self.hardware.get_fl_image(fl[1],fl[0])

        else:
            img = self.hardware.get_image()
        self.img_shape = img.shape

        blobs = get_blobs(img, fl)
        # blobs = self.check_background(blobs)
        blobs = self.check_excluded(blobs)
        blobs = self.check_edges(blobs)
        blobs = self.check_radius(blobs)
        if fl is not None:
            blobs = self.check_fluor(blobs)

        if len(blobs) > 0:

            # for debugging we can plot what we see
            if self.debug:
                self.axes.clear()
                cv2.circle(img, (int(blobs[0].centroid[1]), int(blobs[0].centroid[0])), int(blobs[0].major_axis_length),
                           (0, 0, 255), 5)
                plt.imshow(img)

            # Shuffle the cells around, better random movement
            random.shuffle(blobs)
            self.move_blobs(blobs[0])
            # Save this blob as a reference
            self.current_blob = blobs[0]
            return True
        else:
            return False

    @staticmethod
    def _get_centroid(centroid):
        """ Because skimage is switching from x,y to row, column for centroid measurements
         this is to make sure stuff doesn't break when it does

         """
        if skimage.__version__ >= "0.16":
            return centroid  # Centroid is already Row, Column
        else:
            #logging.warning("Skimage will be changing soon to row, column, but we should be okay! XD")
            return [centroid[1], centroid[0]]  # Change centroid to row, columnn

    def move_blobs(self, cell):
        """ Moves a blob to the laser_spot location """
        c, r = self._get_centroid(cell.centroid)
        laser_r = self.laser_spot[1]
        laser_c = self.laser_spot[0]
        dr = (laser_r - r) * self.pix2um
        dc = (laser_c - c) * self.pix2um
        logging.warning("{},{} is laser spot".format(laser_c, laser_r))
        logging.warning("{},{} is cell spot".format(c, r))
        logging.warning("{},{} is laser dx (column), dy (row)".format(dc / self.pix2um, dr / self.pix2um))
        # A higher row is equal to a lower y so invert the relative request on the Y axis
        xy = self.hardware.get_xy()
        self.hardware.set_xy(rel_xy=[dc, -dr])
        xy = [xy[0] + dc, xy[1] - dr]
        self.excluded_xy.append(self.get_absolute(cell.centroid))
        return xy

    def check_background(self, blobs):
        """ Checks the background of the image to make sure no blobs are just dust on the lens. References image
        located at blob_exclusion_image (class variables above init) """
        new_blobs = []
        for i, blob in enumerate(blobs):
            verified = True
            for old_cell in self.background_blobs:
                dist = distance.euclidean(blob.centroid, old_cell.centroid)
                if dist < 10:
                    verified = False
            if verified:
                new_blobs.append(blob)
        return new_blobs

    def _get_background_blobs(self):
        """ Get blobs in the background image found at blob_exclusion_image"""
        img = Image.open(self.blob_exclusion_image)

        return get_blobs(img, scale = self.scale)

    def check_edges(self, blobs):
        """ If a blob is too close to the edge, remove it from possible cells"""
        new_blobs = []
        edge_buffer = 50  # How close from the edge to exclude blobs
        for i, blob in enumerate(blobs):
            verified = True
            for l, m in enumerate(blob.centroid):
                if m < edge_buffer or m > self.img_shape[l] + edge_buffer:
                    verified = False
            if verified:
                new_blobs.append(blob)
        return new_blobs

    def check_radius(self, blobs):
        """ Excludes cells with a diameter larger than the maximum"""
        new_blobs = []
        for i, blob in enumerate(blobs):
            verified = True
            if self.min_diameter > blob.major_axis_length*self.pix2um > self.max_diameter:
                verified = False
            if verified:
                new_blobs.append(blob)
        return new_blobs

    def check_fluor(self,blobs):
        """ Check if the mean intensity of a blob is above the threshold"""
        new_blobs = []
        for i, blob in enumerate(blobs):
            verified = True
            if blob.mean_intensity < self.fl_threshold:
                verified = False
            if verified:
                new_blobs.append(blob)
        return new_blobs
    def check_excluded(self, blobs):
        """
        Checks list of already lysed locations to see if blob overlaps
        if blobs overlaps it is removed from the list of viable blobs

        :param blobs: region prop list
        :return: blobs: region prop list of qualified blobs
        """
        new_blobs = []
        for i, blob in enumerate(blobs):
            abs_xy = self.get_absolute(blob.centroid)
            if len(self.excluded_xy) == 0:
                new_blobs.append(blob)
            else:
                verified = True
                for old_cell in self.excluded_xy:
                    dist = distance.euclidean(abs_xy, old_cell)
                    #logging.warning("{} is dist to add".format(dist))
                    if dist < self.excluded_minimum:
                        verified = False
                if verified:
                    new_blobs.append(blob)
        return new_blobs

    def get_absolute(self, centroid):
        """

        :param centroid: row column (xy) for image
        :return:
        """
        x, y = self._get_centroid(centroid)

        xy = self.hardware.get_xy()
        abs_x = xy[0] + x * self.pix2um
        abs_y = xy[1] - y * self.pix2um
        return [abs_x, abs_y]


class Mover:
    max_radius = RADIUS
    rand_radius = 1000
    exclusion_list = []
    exclusion_length = 250

    def __init__(self, center=CENTER):
        self.center = center

    def move_random(self, current_xy):
        xy = self.verify_random(current_xy)
        return xy

    def verify_random(self, current_xy):
        all_clear = False
        # Give the computer 1000 attempts to find a new random location
        max_xy = [0, 0]
        max_dist = 0
        for i in range(1000):
            dx = np.random.randint(self.rand_radius) + self.exclusion_length
            dy = np.random.randint(self.rand_radius) + self.exclusion_length
            # Random chance to go above or below
            if np.random.randint(2) == 1:
                dx = -dx
            if np.random.randint(2) == 1:
                dy = -dy
            dx = dx + current_xy[0]
            dy = dy + current_xy[1]

            all_clear = True
            # Ensure distance is not overlapping with previous locations
            for old_xy in self.exclusion_list:
                new_dist = distance.euclidean([dx, dy], old_xy)
                if new_dist < self.exclusion_length:
                    all_clear = False
                    # Record the distance that overlaps the least as a backup location
                    if max_dist < new_dist:
                        max_dist = new_dist
                        max_xy = [dx, dy]
                big_dist = distance.euclidean([dx, dy], self.center)
                # Reject if its outside the bounds
                if big_dist > self.max_radius:
                    all_clear = False
            # if the random point doesnt have an issue with any of the spots continue outside the loop
            if all_clear:
                max_xy = [dx, dy]
                break
        self.exclusion_list.append(max_xy)
        return max_xy


class FocusGetter:
    """ Focuses the Cell """



    def __init__(self, detector, mover, laser_spot=(235, 384)):
        self.hardware = detector.hardware
        self.detector = detector
        self.laser_spot = laser_spot
        self.center = mover.center
        self.radius = mover.max_radius
        self.mover = mover
        self._plane_vectors = []
        self._plane_coefficients = [0, 0, 0, 0]
        self.pixel_cell_diameter_min = 20
        self.um = []
        self.fm = []

    def move_focus(self, focal_range, steps):
        """
        Moves the cell up and down 'focal_range' in um, at a number of 'steps'. For example if focal range is 9
        will move the objective up 9 um. If steps is equal to 2, it will perform this in two steps +4.5 um and +9 um.
        It will then move below the original point -4.5 and -9 um.
        It calculates a focus measure at each point and moves to the highest focus after it has completed.

        :param focal_range: float, the range in one direction to test focus
        :param steps: float, the number of steps to check between current position and the focal_range
        :return: [ max_fm, max_fm_objective_position]
        """
        # Get the absolute positions to  move up and down
        starting = self.hardware.get_objective()
        positions = self._get_cell_positions(starting, focal_range, steps)

        # Initialize the focus measure max comparison with our current position
        focus_measure_max = [self._get_focus_measure(self._roi_img(self.hardware.get_image())), starting]
        self.um = [starting]
        self.fm = [focus_measure_max[0]]
        self.um.extend(positions)

        # Cycle through the positions, move the objective, get the focus measure, and compare to old focus measures
        for abs_position in positions:
            self.hardware.set_objective(h=abs_position)
            time.sleep(0.25)
            img = self.hardware.get_image()
            focus_measure = self._get_focus_measure(self._roi_img(img))
            self.fm.append(focus_measure)
            if focus_measure > focus_measure_max[0]:
                focus_measure_max = [focus_measure, abs_position]
        self.hardware.set_objective(h=focus_measure_max[1])
        time.sleep(0.5)
        return focus_measure_max

    @staticmethod
    def _get_cell_positions(starting_pos, focal_range, steps):
        dstep = focal_range / steps
        positions = [(i + 1) * dstep + starting_pos for i in
                     range(steps)]
        positions.extend([-(i + 1) * dstep + starting_pos for i in
                          range(steps)])
        return positions

    @staticmethod
    def _get_focus_measure(roi):
        fm = cv2.Laplacian(np.array(roi), cv2.CV_8U).var()
        return fm

    def _roi_img(self, img):
        """ Returns the ROI from an image
        bbox = [rox_min, col_min, row_max, col_max]
        """
        buffer = 150
        bbox = [self.laser_spot[0] - buffer, self.laser_spot[1] - buffer, self.laser_spot[0] + buffer, self.laser_spot[1] + buffer]
        roi = img[bbox[0]:bbox[2], bbox[1]:bbox[3]]
        return roi

    def cell_check(self):
        """ Checks if the remaining blob is probably a cell"""
        img = self.hardware.get_image()
        roi = self._roi_img(img)
        blob = get_blobs(roi)
        if len(blob) < 1:
            return False
        if self._diameter_check(blob[0]):
            # you can add other true false tests here
            return True
        else:
            return False

    def _diameter_check(self, blob):
        return blob.minor_axis_length > self.pixel_cell_diameter_min

    def find_a_plane(self):
        """
        Calculate the scalar equation of the plane using the cross product of two vectors.
        Requires that 3 points are recorded in the _plane_vectors list before.

        ax + by + cz = d

        a,b,c are coefficients calculated from the cross product of two vectors that lie in the plane.
        d can be calculated by taking the dot product of [a,b,c] and one of the 3 points.

        :return:
        """
        if len(self._plane_vectors) < 3:
            logging.warning("You need to collect 3 points")
            return False

        # Get the 3 points
        p1, p2, p3 = np.array(self._plane_vectors[0:3])

        # Calculate the vectors
        v_1 = p3 - p1
        v_2 = p2 - p1

        # Get the ccross product
        cross_product = np.cross(v_1, v_2)
        a, b, c = cross_product
        d = np.dot(cross_product, p3)

        # Save the coeffecients of the scalar plane equation
        self._plane_coefficients = [a, b, c, d]

        return True

    def add_focus_point(self):
        """
        Add points to the _plane_vectors list.
        The points are ordered as xyz and use
        the CESystems class to get the XY and Z points
        from their respective controllers
        :return:
        """
        # Get XY from the XY stage
        x,y = self.hardware.get_xy()

        # Get z from the objective (focus)
        z = self.hardware.get_objective()

        self._plane_vectors.append([x,y,z])
        self.last_z = z

    def find_plane_focus(self, flag=threading.Event()):
        cell = False
        logging.info("Verision 0.1")
        while not cell and not flag.is_set():
            self.get_plane_focus()
            time.sleep(0.75)
            self.detector.mover_find_cell(self.mover)
            time.sleep(0.5)
            self.move_focus(14,14)
            time.sleep(0.5)
            cell = self.cell_check()

    def get_plane_focus(self):
        # If spline is not set up, keep the objective at the same position
        if len(self._plane_vectors) < 3:
            logging.warning("Adding to the plane")

        xy = self.hardware.get_xy()
        a, b, c, d = self._plane_coefficients
        z = (d - (a * xy[0]) - (b * xy[1])) / c
        logging.info("Focus position is {} ".format(z))
        self.hardware.set_objective(h=z)
        self.last_z = z

    def quickcheck(self, fl_info):
        self.get_plane_focus()
        time.sleep(0.4)
        #self.detector.mover_find_cell(self.mover, fl=fl_info)




if __name__ == "__main__":
    import CESystems

    hardware = CESystems.NikonEclipseTi()
    hardware.start_system()
    hardware.image_control.live_view()
    det = CellDetector(hardware)
    mov = Mover(CENTER)
    fc = FocusGetter(det, mov)
    #fc.gather_plane_points()
