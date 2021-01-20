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
from L4.image_util import *
import pandas as pd


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
        new_blob.add_point(region)
        blobs.append(new_blob)
    return blobs


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
        background_files.extend([str(x) for x in images_dir.glob(image_type)])
    background_images = io.ImageCollection(background_files, load_func=read_image)

    # Calculate the median of the image collection
    median_background = np.median(background_images, axis=0)
    return median_background


def scikit_threshold(image: np.ndarray, background: np.ndarray, close_size=11, open_size=7,
                     watershed_footprint=(11, 11)):
    """
    Finds all the blobs in a given image. Image and background should be the same type (float, uint16, etc...)


    :param image: image array
    :param background: background of the image
    :param watershed_footprint: size of NxM Watershed footprint
    :param open_size: size of structure element for binary opening operation
    :param close_size: size of structure element for binary closing operation
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
    structure_element = morphology.disk(close_size)
    closed_image = morphology.binary_closing(binary_otsu, structure_element)
    structure_element = morphology.disk(open_size)
    opened_image = morphology.binary_opening(closed_image, structure_element)

    # Watershed
    distance = distance_transform_edt(opened_image)
    local_maxi = peak_local_max(distance, indices=False, footprint=np.ones(watershed_footprint), labels=opened_image)
    markers = label(local_maxi)[0]
    labels = watershed(-distance, markers, mask=opened_image)

    return labels


def get_avg_score(img_dir, close_size=1, open_size=1):
    # label Images here
    if img_dir is None:
        img_dir = r"D:\Scripts\working-at-home\fiji-haesleinhuepf\images\cells"
    labels = ['cell', 'dust']
    im_background = get_background_image(img_dir)
    average_score = []
    for image, im_file in image_iterator():
        # im_plot=axes.imshow(image)
        blobs = get_blobs(image, 'scikit_threshold', im_background, close_size=close_size, open_size=open_size)

        try:
            in_file = im_file[:-4] + "_labels.csv"
            truth = pd.read_csv(in_file)

        except FileNotFoundError:
            print("The following image is not labeled: {}".format(im_file))
            continue

        truth_blobs = from_df_to_list(truth)
        scores = compare_blobs_iou(blobs, truth_blobs)
        average_score.append(np.sum(scores) / len(truth_blobs))
    average_score = np.median(average_score)
    print("Close_Size: {}, Open Size: {}, Score: {}".format(close_size, open_size, average_score))
    return [close_size, open_size, average_score]
