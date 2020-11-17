import json
import logging
import random
import threading
import time
import numpy as np
import matplotlib.pyplot as plt
import uuid
import os
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.signal import convolve2d
from PIL import Image
from L3 import SystemsBuilder

''' Fill the two functions below with their actual implementations would probably be easiest. '''


class PlaneFocus:

    def __init__(self, ce_system: SystemsBuilder.CESystem):
        self.system = ce_system
        self._plane_vectors = []
        self._plane_coefficients = [0, 0, 0, 0]
        self.um = []
        self.fm = []
        self.last_z = None
        self.continue_flag = threading.Event()
        self.stop_flag = threading.Event()

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
        p1, p2, p3 = np.array(self._plane_vectors[-3:])

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

    def get_three_points(self, travel=2):
        # Move Up
        def threaded_function(step):
            self.system.xy_stage.set_rel_x(step)
            self.wait_for_response()
            self.add_focus_point()

            self.system.xy_stage.set_rel_y(step)
            self.wait_for_response()
            self.add_focus_point()

            self.system.xy_stage.set_rel_x(step)
            self.wait_for_response()
            self.add_focus_point()

            self.find_a_plane()

        th = threading.Thread(target=threaded_function, args=(travel,))
        th.start()

    def wait_for_response(self):
        self.continue_flag.set()
        while self.continue_flag.is_set():
            time.sleep(0.2)
            if self.stop_flag.is_set():
                raise RuntimeError

    def give_response(self):
        self.continue_flag.clear()

    def add_focus_point(self):
        """
        Add points to the _plane_vectors list.
        The points are ordered as xyz and use
        the CESystems class to get the XY and Z points
        from their respective controllers
        :return:
        """
        # Get XY from the XY stage
        x, y = self.system.xy_stage.read_xy()

        # Get z from the objective (focus)
        z = self.system.objective.read_z()

        self._plane_vectors.append([x, y, z])
        self.last_z = z

    def get_plane_focus(self):
        # If spline is not set up, keep the objective at the same position

        xy = self.system.xy_stage.read_xy()
        a, b, c, d = self._plane_coefficients
        z = (d - (a * xy[0]) - (b * xy[1])) / c
        logging.info("Focus position is {} ".format(z))
        self.system.objective.set_z(z)
        self.last_z = z


class FindFocus:

    def __init__(self, system):

        self.image_index = 0
        self.measures = None
        self.brenner = None
        self.range_hist = None
        self.entropy_hist = None
        self.sobel = None
        self.variance = None
        self.power = None
        self.system = system

    def move_z(self, distance):
        self.system.objective.set_rel_z(distance)
        time.sleep(0.2)

    def snap_image(self, auto_shutter=True):
        img = self.system.camera.snap()
        return img

    def search_fibonacci(self, z_multiplier=0.002):
        """
        Helpful short video on fibonacci search: https://www.youtube.com/watch?v=GAafWFRGP7k
        The step size and direction between each image is based on the current iteration (we step through the
        fibonacci numbers), whether we moved towards or away from focus, and whether he camera was previously at
        position 'c' or 'd' (you will have to watch the video for that to make sense or see example below).
        This method while often very accurate can be extremely sensitive to the quality of the focus measure results.
        Ideas:
        1) The only part of this algorithm we can really change (as opposed to the step search below) is how we calculate
            whether we moved towards or away from focus. Currently we calculate a weighted difference between several
            different focus measures that statistically gave the best results.
        :return:Nothing, when the function completes the microscope should be 'in focus.' Possibly return how far we moved
            from the initial position when the function was called.
        Example:
        Using the sequence [1, 1, 2, 3, 5, 8]
        / = where we take an image
        -z                        z ->                        +z
        a                    c            d                    b   a->c is 5, c->b is 8, c->d is the difference (3)
        |--------------------/------------/--------------------|
        We will start at position c, take an image, move to d, take an image.
        We determine c is closer to focus then d so now we only consider the following subsection
        a            c       d            b   a->c is 3, c->b is 5, c->d is the difference (2)
        |------------/-------|------------|
        We are at position d, we move to position c, take an image.
        We determine d is closer to focus then c so now we only consider the following subsection
                     a       c     d      b   a->c is 2, c->b is 3, c->d is the difference (1)
                     |-------|-----/------|
        We are at position a, we move to position d, take an image (we already have position c image from position d above)
        We determine c is closer to focus then d so now we only consider the following subsection
                     a     c d     b   a->c is 1, c->b is 2, c->d is the difference (1)
                     |-----/-|-----|
        We are at position d, we move to position c, take an image.
        We determine d is closer to focus then c so now we only consider the following subsection
                             d
                           a c b    a->c is 1, a->b is 1
                           |-|-|
        c now equals d and that is our focus point.
        (A look at the position as we move along, remember / is where we would take an image)
        |--------------------/------------/--------------------|
        |------------/-------|------------|
                     |-------|-----/------|
                     |-----/-|-----|
                           |-|-|
        We use a a longer section of the sequence so we have a couple more iterations.
        If that was hard to follow definitely just take a look at the video, I basically stole their example.
        """

        fibonacci_numbers = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
        max_iterations = len(fibonacci_numbers)

        image_array = self.snap_image()
        c_b, c_r, c_e, c_s, c_v, c_p = get_measures(image_array)

        self.move_z(fibonacci_numbers[-4] * z_multiplier)
        time.sleep(0.4)
        image_array = self.snap_image()
        d_b, d_r, d_e, d_s, d_v, d_p = get_measures(image_array)

        current_camera_position = 'R'
        n = 3
        for _ in range(2, max_iterations - 2):
            measure_difference = is_moving_toward_focus_2(c_b, c_r, c_e, c_s, c_v, c_p,
                                                          d_b, d_r, d_e, d_s, d_v, d_p)

            if measure_difference >= 0 and current_camera_position == 'R':
                self.move_z((fibonacci_numbers[-n] - fibonacci_numbers[-n - 1]) * z_multiplier)
                image_array = self.snap_image()
                c_b, c_r, c_e, c_s, c_v, c_p = d_b, d_r, d_e, d_s, d_v, d_p
                d_b, d_r, d_e, d_s, d_v, d_p = get_measures(image_array)

            elif measure_difference < 0 and current_camera_position == 'R':
                current_camera_position = 'L'
                self.move_z((-fibonacci_numbers[-n]) * z_multiplier)
                image_array = self.snap_image()
                d_b, d_r, d_e, d_s, d_v, d_p = c_b, c_r, c_e, c_s, c_v, c_p
                c_b, c_r, c_e, c_s, c_v, c_p = get_measures(image_array)

            elif measure_difference >= 0 and current_camera_position == 'L':
                current_camera_position = 'R'
                self.move_z((fibonacci_numbers[-n]) * z_multiplier)
                image_array = self.snap_image()
                c_b, c_r, c_e, c_s, c_v, c_p = d_b, d_r, d_e, d_s, d_v, d_p
                d_b, d_r, d_e, d_s, d_v, d_p = get_measures(image_array)

            elif measure_difference < 0 and current_camera_position == 'L':
                self.move_z(-(fibonacci_numbers[-n] - fibonacci_numbers[-n - 1]) * z_multiplier)
                image_array = self.snap_image()
                d_b, d_r, d_e, d_s, d_v, d_p = c_b, c_r, c_e, c_s, c_v, c_p
                c_b, c_r, c_e, c_s, c_v, c_p = get_measures(image_array)
            print(f"Position: {self.system.objective.read_z()}")
            n += 1

    def search_step_global(self, step_size=7, max_iterations=8):
        """
        A total of 'max_iterations' images will be taken with some distance between each image. The camera will initially
        move so that half the images are taken below the current position and half above.
        Using the focus measures calculated from each image (brenner, range, entropy, sobel, variance and power) it
        calculates whether the move from each image to the next is 'towards' or 'away' from focus and stores those values in
        an array.
        This very basic version will just move to the position halfway between the positions where we switched form going
        towards to away from focus.
        Ideas:
        1) A possible refinement stage where we consider a smaller area around the position found by the current algorithm.
            We could even limit the broader one to maybe 4 images and then refine with 4 more images (depending on our
            time constraints).
        2) Consider a different way of using the focus measure values we get. The way we currently do it the function that
            returns whether the move was toward or away focus takes all those values listed above and computes a weighted
            difference that was found to statistically give me the correct answer most of the time (around 90%).
        :return: Nothing, when the function completes the microscope should be 'in focus.' Possibly return how far we moved
            from the initial position when the function was called.
        """

        z_multiplier = 0.001

        self.move_z(step_size * z_multiplier * -(max_iterations // 2))
        time.sleep(0.4)
        image_array = self.snap_image()
        c_b, c_r, c_e, c_s, c_v, c_p = get_measures(image_array)

        differences = []
        for n in range(-(max_iterations // 2) + 2, (max_iterations // 2) + 1):
            self.move_z(step_size * z_multiplier)
            image_array = self.snap_image()
            d_b, d_r, d_e, d_s, d_v, d_p = get_measures(image_array)

            measure_difference = is_moving_toward_focus_2(c_b, c_r, c_e, c_s, c_v, c_p,
                                                          d_b, d_r, d_e, d_s, d_v, d_p)
            print(f'meaure: {measure_difference}, step: {n}, pos= {self.system.objective.read_z()}')
            differences.append(measure_difference)
            c_b, c_r, c_e, c_s, c_v, c_p = d_b, d_r, d_e, d_s, d_v, d_p

        for index, direction in enumerate(differences):
            if 0 < index < len(differences) - 1 and (direction > 0) != (differences[index - 1] > 0) and \
                    (direction > 0) != (differences[index + 1] > 0):
                differences[index] = np.mean([differences[index - 1], differences[index + 1]])

        index = -1
        print(differences)
        try:
            while differences[index] < 0:
                index -= 1
        except IndexError:
            index += 1

        self.move_z(index * step_size * z_multiplier)

    def search_hill_climb(self):
        """
        This one will be just as it sounds, starting where you are at and making one move after the other determining after
        each move if we are 'climbing the hill' towards focus.
        :return:
        """

    def fibonacci(self):
        t_array = []
        n_array = []
        i_array = []
        differences = []

        fibonacci_numbers = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
        max_iterations = len(
            fibonacci_numbers)  # F9 = 55 is the first fibonacci number greater then 50 (max lens positions according to me)
        max_lens_positions = fibonacci_numbers[-1]
        index_difference = 0
        # print(self.image_index + index_difference)

        index_difference += -((fibonacci_numbers[-2] - fibonacci_numbers[-3]) // 2)  # to c
        # print(self.image_index + index_difference)

        c_brenner = self.brenner[self.image_index + index_difference]
        c_range = self.range_hist[self.image_index + index_difference]
        c_entropy = self.entropy_hist[self.image_index + index_difference]
        c_sobel = self.sobel[self.image_index + index_difference]
        c_variance = self.variance[self.image_index + index_difference]
        c_power = self.power[self.image_index + index_difference]

        index_difference += fibonacci_numbers[-4]  # to d
        # print(self.image_index + index_difference)

        d_brenner = self.brenner[self.image_index + index_difference]
        d_range = self.range_hist[self.image_index + index_difference]
        d_entropy = self.entropy_hist[self.image_index + index_difference]
        d_sobel = self.sobel[self.image_index + index_difference]
        d_variance = self.variance[self.image_index + index_difference]
        d_power = self.power[self.image_index + index_difference]

        current_camera_position = 'RIGHT'
        n = 3
        diff_array = []
        for _ in range(2, max_iterations - 2):

            focus_measure_difference = is_moving_toward_focus_2(c_brenner, c_range, c_entropy, c_sobel,
                                                                c_variance, c_power,
                                                                d_brenner, d_range, d_entropy, d_sobel,
                                                                d_variance, d_power)
            t_array.append(differences[self.image_index + index_difference])
            n_array.append(n)
            i_array.append(self.image_index + index_difference)
            diff_array.append(focus_measure_difference)

            # print(current_camera_position, focus_measure_difference)

            if focus_measure_difference >= 0 and current_camera_position == 'RIGHT':
                # print('d is greater then c, moving {}'.format(fibonacci_numbers[-n] - fibonacci_numbers[-n-1]))
                index_difference += fibonacci_numbers[-n] - fibonacci_numbers[-n - 1]
                # current_camera_position = 'LEFT'
                c_brenner = d_brenner
                c_range = d_range
                c_entropy = d_entropy
                c_sobel = d_sobel
                c_variance = d_variance
                c_power = d_power
                d_brenner = self.brenner[self.image_index + index_difference]
                d_range = self.range_hist[self.image_index + index_difference]
                d_entropy = self.entropy_hist[self.image_index + index_difference]
                d_sobel = self.sobel[self.image_index + index_difference]
                d_variance = self.variance[self.image_index + index_difference]
                d_power = self.power[self.image_index + index_difference]

            elif focus_measure_difference < 0 and current_camera_position == 'RIGHT':
                # print('d is less then then c, moving {}'.format(-fibonacci_numbers[-n]))
                index_difference += -fibonacci_numbers[-n]
                current_camera_position = 'LEFT'
                d_brenner = c_brenner
                d_range = c_range
                d_entropy = c_entropy
                d_sobel = c_sobel
                d_variance = c_variance
                d_power = c_power
                c_brenner = self.brenner[self.image_index + index_difference]
                c_range = self.range_hist[self.image_index + index_difference]
                c_entropy = self.entropy_hist[self.image_index + index_difference]
                c_sobel = self.sobel[self.image_index + index_difference]
                c_variance = self.variance[self.image_index + index_difference]
                c_power = self.power[self.image_index + index_difference]

            elif focus_measure_difference >= 0 and current_camera_position == 'LEFT':
                # print('d is greater then c, moving {}'.format(fibonacci_numbers[-n]))
                index_difference += fibonacci_numbers[-n]
                current_camera_position = 'RIGHT'
                c_brenner = d_brenner
                c_range = d_range
                c_entropy = d_entropy
                c_sobel = d_sobel
                c_variance = d_variance
                c_power = d_power
                d_brenner = self.brenner[self.image_index + index_difference]
                d_range = self.range_hist[self.image_index + index_difference]
                d_entropy = self.entropy_hist[self.image_index + index_difference]
                d_sobel = self.sobel[self.image_index + index_difference]
                d_variance = self.variance[self.image_index + index_difference]
                d_power = self.power[self.image_index + index_difference]

            elif focus_measure_difference < 0 and current_camera_position == 'LEFT':
                # print('d is less then c, moving {}'.format(-(fibonacci_numbers[-n] - fibonacci_numbers[-n-1])))
                index_difference += -(fibonacci_numbers[-n] - fibonacci_numbers[-n - 1])
                # current_camera_position = 'RIGHT'
                d_brenner = c_brenner
                d_range = c_range
                d_entropy = c_entropy
                d_sobel = c_sobel
                d_variance = c_variance
                d_power = c_power
                c_brenner = self.brenner[self.image_index + index_difference]
                c_range = self.range_hist[self.image_index + index_difference]
                c_entropy = self.entropy_hist[self.image_index + index_difference]
                c_sobel = self.sobel[self.image_index + index_difference]
                c_variance = self.variance[self.image_index + index_difference]
                c_power = self.power[self.image_index + index_difference]

            # print(self.image_index + index_difference)

            n += 1
        t_array.append(differences[self.image_index + index_difference])
        n_array.append(n)
        i_array.append(self.image_index + index_difference)
        diff_array.append(0)

        return i_array, t_array, n_array, self.image_index + index_difference, n - 3, diff_array

    def hill_climb(self):
        pass

    def step_global(self, differences=[]):
        t_array = []
        n_array = []
        i_array = []

        max_iterations = 8

        diff_array = []
        separation = 7
        index_difference = -(max_iterations // 2) * separation if -(max_iterations // 2) * separation >= 0 else 0

        c_brenner = self.brenner[self.image_index + index_difference]
        c_range = self.range_hist[self.image_index + index_difference]
        c_entropy = self.entropy_hist[self.image_index + index_difference]
        c_sobel = self.sobel[self.image_index + index_difference]
        c_variance = self.variance[self.image_index + index_difference]
        c_power = self.power[self.image_index + index_difference]
        # print(self.image_index + index_difference, self.image_index)

        for n in range(-(max_iterations // 2) + 2, (max_iterations // 2) + 1):
            index_difference = n * separation

            d_brenner = self.brenner[self.image_index + index_difference]
            d_range = self.range_hist[self.image_index + index_difference]
            d_entropy = self.entropy_hist[self.image_index + index_difference]
            d_sobel = self.sobel[self.image_index + index_difference]
            d_variance = self.variance[self.image_index + index_difference]
            d_power = self.power[self.image_index + index_difference]

            focus_measure_difference = is_moving_toward_focus_2(c_brenner, c_range, c_entropy, c_sobel,
                                                                c_variance, c_power,
                                                                d_brenner, d_range, d_entropy, d_sobel,
                                                                d_variance, d_power)

            c_brenner = d_brenner
            c_range = d_range
            c_entropy = d_entropy
            c_sobel = d_sobel
            c_variance = d_variance
            c_power = d_power

            t_array.append(differences[self.image_index + index_difference])
            n_array.append(n)
            i_array.append(self.image_index + index_difference)
            diff_array.append(focus_measure_difference)

        guess_index = 0

        # print(diff_array)
        for index, direction in enumerate(diff_array):
            if 0 < index < len(diff_array) - 1 and (direction > 0) != (diff_array[index - 1] > 0) and (
                    direction > 0) != (
                    diff_array[index + 1] > 0):
                diff_array[index] = np.mean([diff_array[index - 1], diff_array[index + 1]])

        # print(diff_array)
        # print(i_array, t_array, n_array, guess_index, max_iterations)
        index = -1

        try:
            while diff_array[index] < 0:
                index -= 1
        except IndexError:
            index += 1

        guess_index = int((i_array[index] + i_array[index + 1]) / 2)
        t_array.append(differences[int(guess_index)])
        diff_array.append(np.mean(diff_array[index] + diff_array[index + 1]))
        i_array.append(guess_index)
        return i_array, t_array, n_array, guess_index, max_iterations, diff_array


def refine_global():
    pass


def successive_approximation():
    pass


def _get_image_focus():
    pass


def _get_image_direction():
    pass


def contrast_siavash(image_array) -> float:
    """
    See (1) pg. 3
    :param image_array:
    :return: Contrast measure as float
    """

    max_pixel_value = np.max(image_array)
    min_pixel_value = np.min(image_array)
    return float((max_pixel_value - min_pixel_value) / (max_pixel_value + min_pixel_value))


def variance_siavash(image_array) -> float:
    """
    See (1) pg. 3
    :param image_array:
    :return: Variance measure as float
    """

    mean = np.mean(image_array)
    return float(np.sum(np.power(np.subtract(image_array, mean), 2)) / mean)


def threshold_gradient_santos(image_array) -> float:
    """
    See (2) pg. 2
    :param image_array:
    :return:
    """

    gradient_threshold = 16000
    pixel_distance = 3
    image_array_difference = np.subtract(image_array, np.roll(image_array, pixel_distance, axis=1))
    return float(np.sum(image_array_difference, where=np.abs(image_array_difference) >= gradient_threshold))


def squared_gradient_santos(image_array) -> float:
    """
    See (2) pg. 2
    :param image_array:
    :return:
    """
    gradient_threshold = 16000
    pixel_distance = 3
    image_array_difference = np.subtract(image_array, np.roll(image_array, pixel_distance, axis=1))
    return float(
        np.sum(np.power(image_array_difference, 2), where=np.abs(image_array_difference) >= gradient_threshold))


def brenner_gradient_santos(image_array) -> float:
    """
    See (2) pg. 2
    :param image_array:
    :return:
    """
    gradient_threshold = np.mean(image_array)
    pixel_comparison_distance = 1
    pixel_difference_distance = 2
    image_array_comparison = np.roll(image_array, pixel_comparison_distance, axis=1)
    image_array_difference = np.subtract(image_array, np.roll(image_array, pixel_difference_distance, axis=1))
    return float(
        np.sum(np.power(image_array_difference, 2), where=np.abs(image_array_comparison) >= gradient_threshold))


def entropy_siavash(image_array) -> float:
    """
    See (1) pg. 3
    :param image_array:
    :return: Entropy measure as float
    """

    num_elements = np.size(image_array)
    histogram, _ = np.histogram(image_array, 65535)
    probabilities = histogram / num_elements
    return float(-np.sum(np.multiply(probabilities, np.log2(probabilities, where=probabilities > 0))))


def fuzzy_entropy_liu(image_array) -> float:
    """
    See (6) pg. 3
    :param image_array:
    :return: Fuzzy entropy measure as a float
    """

    image_array = np.divide(image_array, np.max(image_array))
    w = 3
    w_2 = 1 / (w * w)
    pre_index = -(w - 1) // 2
    post_index = (w - 1) // 2
    height = len(image_array) - post_index
    width = len(image_array[0]) - post_index

    final = 0.0
    for i in range(height):
        for j in range(width):
            gray_value = image_array[i][j]
            window_value = 0.0
            for m in range(pre_index, post_index + 1):
                for n in range(pre_index, post_index + 1):
                    member = 1 / (1 + abs(image_array[i + m][j + n] - gray_value))
                    member = -member * np.log10(member)
                    window_value += member
            f = w_2 * window_value

            final += f

    return final


def brenner_gradient_siavash(image_array) -> float:
    """
    The Brenner gradient is a fast, rudimentary edge detector, measuring the difference
    between a pixel and a neighbor that is typically two pixels away.
    See (1) pg. 3
    :param image_array:
    :return: Brenner gradient measure as float
    """

    pixel_distance = 2
    return float(np.sum(np.power((np.subtract(np.roll(image_array, pixel_distance, axis=1), image_array)), 2)))


def brenner_gradient_vertical_hashim(image_array) -> float:
    """
    See (1) pg. 3
    :param image_array:
    :return: Brenner gradient measure as float
    """

    pixel_distance = 2
    return float(np.sum(np.power((np.subtract(np.roll(image_array, pixel_distance, axis=0), image_array)), 2)))


def compressed_file_size(image_object: Image.Image) -> float:
    """
    See (3) Fig. 23
    :param image_object:
    :return:
    """

    temporary_file_path = os.path.join(os.getcwd(), str(uuid.uuid4()) + '.jpeg')
    image_object.mode = "I"
    image_object.point(lambda i: i * (1. / 256)).convert('L').save(temporary_file_path, "JPEG", quality=60)
    compressed_size = os.path.getsize(temporary_file_path)
    os.remove(temporary_file_path)
    return float(compressed_size)


def brenner(image_array) -> float:
    pixel_distance = 2
    return float(np.sum(np.power((np.subtract(np.roll(image_array, pixel_distance, axis=0), image_array)), 2)))


def squared_gradient(image_array) -> float:
    pixel_distance = 1
    return float(np.sum(np.power((np.subtract(np.roll(image_array, pixel_distance, axis=0), image_array)), 2)))


def difference_by_three(image_array) -> float:
    operator_1 = [[0, 0, 0], [-1, 0, 1], [0, 0, 0]]
    operator_2 = [[0, -1, 0], [0, 0, 0], [0, 1, 0]]
    return float(np.sum(np.power(convolve2d(image_array, operator_1), 2))) + \
           float(np.sum(np.power(convolve2d(image_array, operator_2), 2)))


def sobel_by_three(image_array) -> float:
    operator_1 = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
    operator_2 = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
    return float(np.sum(np.power(convolve2d(image_array, operator_1), 2))) + \
           float(np.sum(np.power(convolve2d(image_array, operator_2), 2)))


def scharr_by_three(image_array) -> float:
    operator_1 = [[-3, 0, 3], [-10, 0, 10], [-3, 0, 3]]
    operator_2 = [[-3, -10, -3], [0, 0, 0], [3, 10, 3]]
    return float(np.sum(np.power(convolve2d(image_array, operator_1), 2))) + \
           float(np.sum(np.power(convolve2d(image_array, operator_2), 2)))


def roberts_by_three(image_array) -> float:
    operator_1 = [[0, 0, 0], [0, 1, 0], [-1, 0, 0]]
    operator_2 = [[0, 0, 0], [0, 1, 0], [0, 0, -1]]
    return float(np.sum(np.power(convolve2d(image_array, operator_1), 2))) + \
           float(np.sum(np.power(convolve2d(image_array, operator_2), 2)))


def prewitt_by_three(image_array) -> float:
    operator_1 = [[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]]
    operator_2 = [[-1, -1, -1], [0, 0, 0], [1, 1, 1]]
    return float(np.sum(np.power(convolve2d(image_array, operator_1), 2))) + \
           float(np.sum(np.power(convolve2d(image_array, operator_2), 2)))


def gaussian(image_array) -> float:  # fixme, see (10) and (9)
    return float(np.sum(np.power(gaussian_filter(image_array, sigma=1), 2)))


def vertical_squared_gradient(image_array) -> float:
    pixel_distance = 1
    return float(np.sum(np.power((np.subtract(np.roll(image_array, pixel_distance, axis=1), image_array)), 2)))


def vertical_brenner(image_array) -> float:
    pixel_distance = 2
    return float(np.sum(np.power((np.subtract(np.roll(image_array, pixel_distance, axis=1), image_array)), 2)))


def sobel_by_five(image_array) -> float:
    operator_1 = [[-1, -2, 0, 2, 1], [-4, -8, 0, 8, 4], [-6, -12, 0, 12, 6], [-4, -8, 0, 8, 4], [-1, -2, 0, 2, 1]]
    operator_2 = [[-1, -4, -6, -4, -1], [-2, -8, -12, -8, -2], [0, 0, 0, 0, 0], [2, 8, 12, 8, 2], [1, 4, 6, 4, 1]]
    return float(np.sum(np.power(convolve2d(image_array, operator_1), 2))) + \
           float(np.sum(np.power(convolve2d(image_array, operator_2), 2)))


def laplacian_of_gaussian(image_array) -> float:
    operator_1 = [[0, 1, 2, 3, 3, 3, 1, 1, 0], [1, 2, 4, 5, 5, 5, 4, 2, 1], [1, 4, 5, 3, 0, 3, 5, 4, 1],
                  [2, 5, 3, -12, -24, -12, 3, 5, 2],
                  [2, 5, 0, -24, -40, -24, 0, 5, 2], [2, 5, 3, -12, -24, -12, 3, 5, 2], [1, 4, 5, 3, 0, 3, 5, 4, 1],
                  [1, 2, 4, 5, 5, 5, 4, 2, 1], [0, 1, 2, 3, 3, 3, 1, 1, 0]]
    return float(np.sum(np.power(convolve2d(image_array, operator_1), 2)))


def vertical_sobel_by_five(image_array) -> float:
    operator_1 = [[1, 0, -2, 0, 1], [4, 0, -8, 0, 4], [6, 0, -12, 0, 6], [4, 0, -8, 0, 4], [1, 0, -2, 0, 1]]
    return float(np.sum(np.power(convolve2d(image_array, operator_1), 2)))


def laplacian_by_five(image_array) -> float:
    operator_1 = [[-1, -3, -4, -3, -1], [-3, 0, 6, 0, -3], [-4, 6, 20, 6, -4], [-3, 0, 6, 0, -3], [-1, -3, -4, -3, -1]]
    return float(np.sum(np.power(convolve2d(image_array, operator_1), 2)))


def cross_sobel_by_five(image_array) -> float:
    operator_1 = [[-1, -2, 0, 2, 1], [-2, -4, 0, 4, 2], [0, 0, 0, 0, 0], [2, 4, 0, -4, -2], [1, 2, 0, -2, -1]]
    return float(np.sum(np.power(convolve2d(image_array, operator_1), 2)))


def cross_sobel_by_three(image_array) -> float:
    operator_1 = [[-1, 0, 1], [0, 0, 0], [1, 0, -1]]
    return float(np.sum(np.power(convolve2d(image_array, operator_1), 2)))


def vertical_sobel_by_three(image_array) -> float:
    operator_1 = [[1, -2, 1], [2, -4, 2], [1, -2, 1]]
    return float(np.sum(np.power(convolve2d(image_array, operator_1), 2)))


def laplacian_by_three(image_array) -> float:
    operator_1 = [[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]]
    return float(np.sum(np.power(convolve2d(image_array, operator_1), 2)))


def horizontal_sobel_by_five(image_array) -> float:
    operator_1 = [[1, 4, 6, 4, 1], [0, 0, 0, 0, 0], [-2, -8, -12, -8, -2], [0, 0, 0, 0, 0], [1, 4, 6, 4, 1]]
    return float(np.sum(np.power(convolve2d(image_array, operator_1), 2)))


def horizontal_sobel_by_three(image_array) -> float:
    operator_1 = [[1, 2, 1], [-2, -4, -2], [1, 2, 1]]
    return float(np.sum(np.power(convolve2d(image_array, operator_1), 2)))


def range_histogram(image_array) -> float:
    histogram, _ = np.histogram(image_array, 65535)
    return float(max(histogram) - min(histogram))


def entropy_histogram(image_array) -> float:
    num_elements = np.size(image_array)
    histogram, _ = np.histogram(image_array, 65535)
    probabilities = histogram / num_elements
    return float(-np.sum(np.multiply(probabilities, np.log2(probabilities, where=probabilities > 0))))


def m_and_g_histogram(image_array) -> float:
    def delta_value(i, j):
        return 2 * (image_array[i][j - 1] - image_array[i][j + 1]) ** 2 + 2 * (
                image_array[i - 1][j] - image_array[i + 1][j]) ** 2 + \
               (image_array[i - 1][j - 1] - image_array[i + 1][j + 1]) ** 2 + (
                       image_array[i - 1][j + 1] - image_array[i + 1][j - 1]) ** 2

    image_array = np.multiply(image_array, 255 / 65535)
    deltas = [[delta_value(j, i) for i in range(len(image_array[0]) - 1)] for j in range(len(image_array) - 1)]
    threshold = np.divide(np.sum([[deltas[i][j] * image_array[i][j]
                                   for i in range(len(image_array) - 2)]
                                  for j in range(len(image_array[0]) - 2)]), np.sum(deltas))

    histogram, _ = np.histogram(image_array, 65535)
    final_value = 0.0
    for i in range(len(histogram)):
        if i > threshold:
            final_value += histogram[i] * (i - threshold)

    return float(final_value)


def m_and_m_histogram(image_array) -> float:
    threshold = int(np.mean(image_array)) + 1
    histogram, _ = np.histogram(image_array, 65535)
    final_value = 0.0

    for i in range(len(histogram)):
        if i > threshold:
            final_value += i * histogram[i]

    return float(final_value)


def normalized_variance(image_array) -> float:
    mean = np.mean(image_array)
    return float(np.sum(np.power(np.subtract(image_array, mean), 2)) \
                 / (len(image_array) * len(image_array[0]) * mean))


def variance(image_array) -> float:
    return float(np.sum(np.power(np.subtract(image_array, np.mean(image_array)), 2)) \
                 / (len(image_array) * len(image_array[0])))


def threshold_pixel_count(image_array) -> float:
    threshold = 150 / 255 * np.max(image_array)
    return float(np.sum([[1 if k < threshold else 0 for k in row] for row in image_array]))


def threshold_content(image_array) -> float:
    threshold = 150 / 255 * np.max(image_array)
    return float(np.sum([[k if k >= threshold else 0 for k in row] for row in image_array]))


def power(image_array) -> float:
    return float(np.sum(np.power(image_array, 2)))


def autocorrelation(image_array) -> float:
    mean = np.mean(image_array)
    vari = variance(image_array)
    k = 2
    rolled_image_array = np.subtract(np.roll(image_array, 2, axis=0), mean)
    image_array = np.subtract(image_array, mean)
    return float((len(image_array) * len(image_array[0]) - k) * vari ** 2 -
                 np.sum(np.multiply(rolled_image_array, image_array)))


def vollaths_f4(image_array) -> float:
    return float(np.sum(np.multiply(image_array, np.roll(image_array, 1, axis=1))) -
                 np.sum(np.multiply(image_array, np.roll(image_array, 2, axis=1))))


def vollaths_f5(image_array) -> float:
    return float(np.sum(np.multiply(image_array, np.roll(image_array, 1, axis=1))) -
                 (len(image_array) * len(image_array[0]) * np.mean(image_array) ** 2))


def get_measures(image_array):
    return brenner(image_array), range_histogram(image_array), entropy_histogram(image_array), \
           sobel_by_three(image_array), variance(image_array), power(image_array)


def is_moving_toward_focus_1(b1, r1, e1, s1, v1, p1, b2, r2, e2, s2, v2, p2):
    d = 0

    if abs(b2 - b1) > 0.01:
        d = d + 1 if b2 - b1 > 0 else d - 1
    if abs(r2 - r1) > 0.0001:
        d = d + 1 if r2 - r1 > 0 else d - 1
    if abs(e2 - e1) > 0.001:
        d = d + 1 if e2 - e1 > 0 else d - 1
    if abs(s2 - s1) > 0.001:
        d = d + 1 if s2 - s1 > 0 else d - 1
    if abs(v2 - v1) > 0.01:
        d = d + 1 if v2 - v1 > 0 else d - 1
    if abs(p2 - p1) > 0.01:
        d = d + 1 if p2 - p1 > 0 else d - 1

    return 1 if d > 0 else 0


def is_moving_toward_focus_2(b1, r1, e1, s1, v1, p1, b2, r2, e2, s2, v2, p2,
                             c1=None, c2=None, c3=None, c4=None,
                             c5=None, c6=None, c7=None, c8=None,
                             c9=None, c10=None, c11=None, c12=None):
    d = 0

    # 50 um
    c1 = 1 if c1 is None else c1
    c2 = -1 if c2 is None else c2
    c3 = -1 if c3 is None else c3
    c4 = -1 if c4 is None else c4
    c5 = 1 if c5 is None else c5
    c6 = -1 if c6 is None else c6
    c7 = 1 if c7 is None else c7
    c8 = -1 if c8 is None else c8
    c9 = 0 if c9 is None else c9
    c10 = 0 if c10 is None else c10
    c11 = 1 if c11 is None else c11
    c12 = -1 if c12 is None else c12

    # 75 um
    # c1 = 1 if c1 is None else c1
    # c2 = -1 if c2 is None else c2
    # c3 = -1 if c3 is None else c3
    # c4 = -1 if c4 is None else c4
    # c5 = 0 if c5 is None else c5
    # c6 = 0 if c6 is None else c6
    # c7 = 1 if c7 is None else c7
    # c8 = -1 if c8 is None else c8
    # c9 = 1 if c9 is None else c9
    # c10 = -1 if c10 is None else c10
    # c11 = 1 if c11 is None else c11
    # c12 = -1 if c12 is None else c12

    d = d + c1 if b2 - b1 > 0 else d + c2
    d = d + c3 if r2 - r1 > 0 else d + c4
    d = d + c5 if e2 - e1 > 0 else d + c6
    d = d + c7 if s2 - s1 > 0 else d + c8
    d = d + c9 if v2 - v1 > 0 else d + c10
    d = d + c11 if p2 - p1 > 0 else d + c12

    return d


"""
References
1) https://www.osapublishing.org/oe/abstract.cfm?uri=oe-16-12-8670
2) http://www2.die.upm.es/im/papers/Autofocus.pdf  
3) https://link.springer.com/article/10.1007/s11214-012-9910-4
4) https://onlinelibrary.wiley.com/doi/epdf/10.1002/cyto.990060202
5) https://www.ncbi.nlm.nih.gov/pmc/articles/mid/NIHMS502898/#R12
6) https://link.springer.com/article/10.1186/s13634-016-0368-5
7) https://cs.uwaterloo.ca/~vanbeek/Publications/spie2014.pdf
8) https://onlinelibrary.wiley.com/doi/epdf/10.1002/cyto.990120302
9) https://www.osapublishing.org/oe/abstract.cfm?uri=oe-27-14-19915
10) https://search.lib.byu.edu/byu/record/edsbyu.edsagr.edsagr.US201300788871?holding=hyelg9bt4wozow5i
11) https://ieeexplore.ieee.org/document/4120927
12) https://search.lib.byu.edu/byu/record/edsbyu.edscal.edscal.5312986?holding=gjbywxrlvvncy545
13) https://www.researchgate.net/publication/229021635_Auto_Focus_Using_Adaptive_Step_Size_Search_and_Zoom_Tracking_Algorithm
Notes
Look at relationship between measures. i.e. when entropy is left is variance right? etc
"""

if __name__ == "__main__":
    pass
