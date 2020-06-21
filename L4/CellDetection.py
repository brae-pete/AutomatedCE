"""
Functions and classes needed to detect a cell.

Cells are recorded as blobs defined by the class Blob, and contain standardized information.

Several utility functions could be of use for cell detection, including find_blob, draw_blob_outline,
remove_blob_outline, and get_rel_xy_to_blob

"""
from pathlib import Path
import numpy as np
from scipy.ndimage import label, distance_transform_edt
from skimage import io, img_as_float, filters, morphology
from skimage.feature import peak_local_max
from skimage.measure import regionprops
from skimage.morphology import watershed


class Blob(object):
    """
    Data object for standarizing some of the common elements needed to determine a cell location.


    Blob.rc is the row, column, pixel position of the centroid of the blob in the image. It is in row,column format
    to make image tasks easier.

    Blob.bbox is the bounding box of the blob in pixels, *currently this is in xy*
    """

    def __init__(self, mm_per_pixel=1):
        self.rc = [0, 0]  # should be the position in pixels, (row[y], column[x])
        self.bbox = [0,0,0,0]  # Bounding box in pixels, [min_row, min_col, max_row, max_col]


def get_blobs(image, algorithm, *args, **kwargs):
    """
    This is a flexible find_blob function. User can select the algorithm they wish to use followed by the required
    arguments and keyword arguments.

    Two options are available initially, although custom blob/cell detection scripts can be used and plugged in here.

    scikit_threshold -> Uses a thresholding and watershed algorithm to locate blobs. It also requires the location
    of 20-50 background images (no cells) that can be used to remove background noise from the image.

    image_j_macro -> Uses an image J macro (file defined by user) to locate blobs. Use should make sure the macro
    has all the necessary variables passed via the *args parameter only. The macro should output a

    :param image:
    :param algorithm: which algorithm to use to find all the blobs
    :param args:
    :param kwargs:
    :return:
    """
    if algorithm == 'scikit_threshold':
        labels = scikit_threshold(image, *args, **kwargs)

    elif algorithm == 'image_j_macro':
        labels = []

    else:
        return []

    # Get the region properties for the image
    regions = regionprops(labels)
    blobs = []
    for region in regions:
        new_blob = Blob()
        new_blob.rc = region.rc[:]
        new_blob.bbox = region.bbox[:]
        blobs.append(new_blob)
    return blobs

def read_image(img):
    """
    Read in the images
    :param img:
    :return: img as float
    """
    return img_as_float(io.imread(img, as_gray=True))


def get_background_image(directory: str):
    """
    Calculates the median value of a stack of images to get the background. Assumes images are in the same format
    as the image being taken (same byte depth, grayscale, etc..)

    :param directory: filepath to directory of images
    :return: array, median background of the image directory
    :rtype: np.ndarray
    """
    images_dir = Path(directory)

    # Get a collection of images
    types = ('*.jpg', '*.tiff', '*.png')
    background_files = []
    for image_type in types:
        background_files.extend(images_dir.glob(image_type))
    background_images = io.ImageCollection(background_files, load_func=read_image)

    # Calculate the median of the image collection
    median_background = np.median(background_images, axis=0)
    return median_background


def scikit_threshold(image:np.ndarray, background:np.ndarray):
    """
    Finds all the blobs in a given image. Image and background should be the same type (float, uint16, etc...)

    :param image: image array
    :param background: background of the image
    :return: labeled image
    :rtype: np.ndarray
    """

    # Make sure types are the same
    input_image = img_as_float(image)

    # Subtract background
    signal_image = input_image - background

    # Normalize between 0 and 1
    normalized_image = (signal_image - signal_image.min()) / (signal_image.max() - signal_image.min())

    # Filter Image
    filtered_image = filters.median(normalized_image, behavior='ndimage')

    # Edge Detection
    edge_sobel = filters.sobel(filtered_image)

    # Threshold
    thresh = filters.threshold_otsu(edge_sobel)
    binary_otsu = edge_sobel > thresh

    # Binary Morphology Operations
    structure_element = morphology.disk(11)
    closed_image = morphology.binary_closing(binary_otsu, structure_element)
    structure_element = morphology.disk(7)
    opened_image = morphology.binary_opening(closed_image, structure_element)

    # Watershed
    distance = distance_transform_edt(opened_image)
    local_maxi = peak_local_max(distance, indices=False, footprint=np.ones((11, 11)), labels=opened_image)
    markers = label(local_maxi)[0]
    labels = watershed(-distance, markers, mask=opened_image)

    return labels
