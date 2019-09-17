from PIL import Image
import matplotlib.pyplot as plt
import skimage
from PIL import Image
from skimage import filters
from skimage.morphology import square, dilation, remove_small_holes, remove_small_objects
from skimage.measure import label, regionprops
from scipy.spatial import distance
import logging
import numpy as np
import time


def get_blobs(img, thresh=0.07, scale=0.25):
    # Edge Filter
    edges = filters.sobel(img)

    # Threshold mask on edges
    bw_mask = edges > thresh

    # Dilation
    dilated = dilation(bw_mask, square(1))

    # Remove small holes
    filled = remove_small_holes(dilated, 1000 * scale)

    # Remove small objects
    thinned = remove_small_objects(filled, 4000 * scale)

    # Get blob info
    labels = label(thinned)
    props = regionprops(labels)

    return props


class CellDetector:
    """
    Detects cells using morphological filters
    Compares againts previous lysis points
    Moves to first cell outside threhold of excluded points
    """
    excluded_xy = []
    excluded_minimum = 100  # distance from previous laser lysis spot
    move_distance = 250

    def __init__(self, hardware, pix2um=0.4900852, laser_spot=(128, 58)):
        """

        :param pix2um: float, conversion scalar from scaled image to um
        :param laser_spot: xy position in um
        :param hardware: xy and image control required
        """
        self.pix2um = pix2um
        self.laser_spot = laser_spot
        self.hardware = hardware

    def mover_find_cell(self, mover):
        """
        Automated cell finding algorithm
        :param mover: Mover Object, moves to random locations
        :return:
        """
        cell = self.find_cell()
        starting = 0
        while not cell and starting < 10:
            xy = mover.move_random(self.hardware.get_xy())
            self.hardware.set_xy(xy)
            time.sleep(0.5)
            cell = self.find_cell()
        return cell

    def find_cell(self):
        """
        Find and move to a cell using a morphological process outlined in the get_blobs
        function


        :return: True if a cell was found, False if a cell was not found
        """
        img = self.hardware.get_image()
        blobs = get_blobs(img)
        blobs = self.check_excluded(blobs)

        if len(blobs) > 0:
            self.move_blobs(blobs[0])
            return True
        else:
            return False

    def move_blobs(self, cell):
        x = cell.centroid[1] * self.pix2um
        y = cell.centroid[0] * self.pix2um
        laser_x = self.laser_spot[0] * self.pix2um
        laser_y = self.laser_spot[1] * self.pix2um
        dx = laser_x - x
        dy = laser_y - y
        logging.warning("{},{} is laser dx, dy".format(dx,dy))
        xy = self.hardware.get_xy()
        xy = [xy[0]-dx, xy[1]-dy]


        self.hardware.set_xy(xy)
        self.excluded_xy.append(self.get_absolute(cell.centroid))
        return xy

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
            if len(self.excluded_xy)==0:
                new_blobs.append(blob)
            else:
                verified = True
                for old_cell in self.excluded_xy:
                    dist = distance.euclidean(abs_xy, old_cell)
                    logging.warning("{} is dist to add".format(dist))
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
        if skimage.__version__ != "0.15.0":
            logging.warning("Check that region props centroid is row, column")

        xy = self.hardware.get_xy()
        abs_x = xy[0] + centroid[1] * self.pix2um
        abs_y = xy[1] + centroid[0] * self.pix2um
        return [abs_x, abs_y]


class Mover:
    center = [0, 0]
    max_radius = 7500
    rand_radius = 1000
    exclusion_list = []
    exclusion_length = 250

    def __init__(self, center):
        self.center = center

    def move_random(self, currentxy):
        xy = self.verify_random(currentxy)
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
                max_dist = distance.euclidean([dx, dy], self.center)
                # Reject if its outside the bounds
                if max_dist > self.max_radius:
                    all_clear = False
            # if the random point doesnt have an issue with any of the spots continue outside the loop
            if all_clear:
                max_xy = [dx, dy]
                break
        self.exclusion_list.append(max_xy)
        return max_xy


if __name__ == "__main__":
    import CESystems

    hardware = CESystems.BarracudaSystem()
    hardware.start_system()
    hardware.image_control.live_view()
    hardware.set_objective(5000)
    det = CellDetector(hardware)
