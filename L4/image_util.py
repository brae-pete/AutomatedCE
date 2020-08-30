import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib import cm
from pathlib import Path
import numpy as np
from skimage import io, img_as_float


class Blob(object):
    """
    Data object for standarizing some of the common elements needed to determine a cell location.


    Blob.centroid is the row, column, pixel position of the centroid of the blob in the image. It is in row,column format
    to make image tasks easier.

    Blob.bbox is the bounding box of the blob in pixels, *currently this is in xy* Lx, Ly, w, h

    Blob.xy is the lower left corner of the bounding box

    """

    def __init__(self, xy=(0, 0), mm_per_pixel=1, size=50):
        self.bbox = (xy, size, size)
        self.centroid = xy[0] + size / 2, xy[1] + size / 2
        self.width = size
        self.height = size
        self.xy = xy
        self.label = 'cell'
        self.enable = True

    def add_point(self, region):
        self.centroid = region.centroid[:]
        r1, c1, r2, c2 = region.bbox[:]
        width = c2 - c1
        height = r2 - r1
        self.bbox = [(c1, r1), width, height]
        self.xy = [c1, r1]

    def from_dataframe(self, row):
        self.xy = (row.x, row.y)
        self.width = row.width
        self.height = row.height

    def get_blob_iou(self, blob_2):
        bb2 = blob_2.get_dict()
        bb1 = self.get_dict()
        return get_iou(bb1, bb2)

    def get_dict(self):
        return to_bbx_dict([self.xy, self.width, self.height])

    def get_bbox(self):
        return [self.xy, self.width, self.height]

def image_iterator(parent_dir=r"D:\Scripts\working-at-home\fiji-haesleinhuepf\images\cells"):
    """
    Image generator function, returns a new image from the parent directory every time it is called.
    :param parent_dir: file path to the image parent directory. Reads images using the read_image function.
    :return: scikit image, read as a float and gray value
    :rtype: np.ndarray
    """

    images_dir = Path(parent_dir)
    # Get a collection of images
    types = ('*.jpg', '*.tiff', '*.png')
    image_files = []
    for image_type in types:
        image_files.extend([str(x) for x in images_dir.glob(image_type)])
    images = io.ImageCollection(image_files, load_func=read_image)
    # Create the generator part of the function
    for image, im_file in zip(images, image_files):
        yield image, im_file


def read_image(img):
    """
    Read in the images
    :param img:
    :return: img as float
    """
    return img_as_float(io.imread(img, as_gray=True))


class ResizableBoxes(object):
    """
    Uses matplotlib events to dynamically change Rectangle Patches on a Matplolib axes.
    The patches to be dynamically updated should have 'picker' set to True. Patches without the picker set to true will not
    be dynamically adjusted.

    Example:

    # Create a Resize Object
    resize = ResizableBoxes()

    # Connect the fig events to the Resize methods
    fig, axes = plt.subplots()
    fig.canvas.mpl_connect('pick_event', resize.on_pick)
    fig.canvas.mpl_connect('motion_notify_event', resize.on_motion)
    fig.canvas.mpl_connect('button_release_event', resize.on_release)

    # Create your rectangle Patch
    rect = mpatches.Rectangle((40, 40),30,60, picker = True)
    axes.add_patch(rect)
    """

    def __init__(self):
        self.rect = mpatches.Rectangle((0, 0), 1, 1)
        self.last_picked_event = None
        self.press = None
        self.resize = -1
        self.resize_sensitivity = 20
        self.pan = None

    def on_release(self, event):
        'on release we reset the press data'
        self.press = None
        self.pan = None
        self.last_picked_event = None
        self.resize = -1
        event.inaxes.figure.canvas.draw_idle()

    def on_pick(self, event):
        """
        Update information for when user clicks a box

        IF LMB near a corner, enable resizing
        If they MMB (Middle Mouse), enable center movement
        """

        self.last_picked_event = event
        self.box = rect = event.artist
        x, y = rect.xy
        width, height = rect.get_width(), rect.get_height()
        xpress = event.mouseevent.xdata
        ypress = event.mouseevent.ydata
        self.press = x, y, xpress, ypress, width, height

        if event.mouseevent.button == 1:
            self.resize = self.near_corner(event)
        elif event.mouseevent.button == 2:
            self.pan = True

    def on_motion(self, event):
        'on motion determine if we need to resize or move the box'
        if self.press is None: return
        if event.inaxes != self.last_picked_event.mouseevent.inaxes: return

        if self.resize >= 0:
            return self.resize_box(event)

        if self.pan:
            return self.move_box(event)

    def move_box(self, event):
        'Move the center of the box while user is moving the mouse'
        print("Yolo")
        x0, y0, xpress, ypress, _, _ = self.press
        dx = event.xdata - xpress
        dy = event.ydata - ypress
        print(f"{dx},{dy}")
        self.box.set_x(x0 + dx)
        self.box.set_y(y0 + dy)
        event.inaxes.figure.canvas.draw_idle()

    def resize_box(self, event):
        """
        Resize the bounding box of the rectangle while user is moving the mouse
        """
        xo, yo, xpress, ypress, width, height = self.press

        # Change X Coordinates
        dx = event.xdata - xpress
        dy = event.ydata - ypress
        if self.resize in [0, 1]:  # Left side changes xo and width
            xo += dx
            width -= dx
        else:
            width += dx  # Width will always change with dx

        # Change Y Coordinates
        if self.resize in [0, 2]:  # Bottom side changes yo with dy
            yo += dy
            height -= dy  # Height always changes with dx
        else:
            height += dy

        self.box.set_bounds(xo, yo, width, height)
        event.inaxes.figure.canvas.draw_idle()

    def near_corner(self, event):
        'deterimine if the mouse is near a corner'
        rect = event.artist
        mouse = event.mouseevent
        xn, yn = mouse.xdata, mouse.ydata

        corners = rect.get_bbox().corners()
        radii = self.resize_sensitivity
        idx = 0
        for cx, cy in corners:
            if np.abs(cx - xn) < radii and np.abs(cy - yn) < radii:
                print("Near corner {}".format(idx))
                return idx
            idx += 1
        return -1


class Labeler(object):
    """
    Draw Rectangle bounding boxes over an axes shaded according to their labels.

    """

    def __init__(self, axes: plt.axes, labels: list, ):
        """

        :param axes: axes to plot the labels onto
        :param labels: list of strings that contain the labels
        """
        self.label_colors = self.get_label_colors(labels, axes)
        self.labels = labels
        self.axes = axes
        self.resize = resize = ResizableBoxes()
        self.patches = {}

        # Make Event Connections to the figure
        fig = axes.figure
        fig.canvas.mpl_connect('pick_event', resize.on_pick)
        fig.canvas.mpl_connect('motion_notify_event', resize.on_motion)
        fig.canvas.mpl_connect('button_release_event', resize.on_release)
        # fig.canvas.mpl_connect('pick_event', self.on_pick_label)
        fig.canvas.mpl_connect('button_press_event', self.on_click_label)
        fig.canvas.mpl_connect('scroll_event', self.on_click_label)

    @staticmethod
    def get_label_colors(labels: list, axes: plt.axes):
        """
        'Get colors for labels and add them to the legend'

        :param labels: list of strings containing labels for the blobs in the image
        :param axes: axes to plot the label legend to
        :return: dictionary of labels and their corresponding colors
        :rtype: dict
        """

        cmap = cm.get_cmap('Paired')
        label_colors = {}
        legend_patches = []
        for idx, key in enumerate(labels):
            color = cmap(idx)
            legend_patches.append(mpatches.Patch(color=color, label=key))
            label_colors[key] = color
        axes.legend(handles=legend_patches, loc='center left', bbox_to_anchor=(1, 0.5))
        return label_colors

    def _add_rectangle(self, blob: Blob):
        'Adds a new rectangle to the plot '
        xy, w, h = blob.bbox
        rect = mpatches.Rectangle(xy, w, h, picker=True, color=self.label_colors[blob.label],
                                  alpha=0.4)
        self.axes.add_patch(rect)
        self.axes.add_patch(rect)
        self.patches[rect] = [blob]
        return

    def draw_labels(self, blobs: list):
        'iterate through a list of Blob objects and plot each one to the axes'
        self.patches = {}
        for blob in blobs:
            self._add_rectangle(blob)
        self.axes.figure.canvas.draw_idle()

    def remove_patches(self):
        'Remove patches from the plot and make them not pickable'
        for rect in self.patches.keys():
            rect.set_picker(None)
            rect.set_picker(False)

    def _on_pick_label(self, event, artist):
        '''Add changes to the label:
        double right click to enable or disable the label
        scroll the mouse wheel to change labels

        '''
        mouse = event  # Get the mouse event that brought us here
        blob = self.patches[artist][0]
        print(mouse.button, mouse.button == 'up')
        #  Right Click Toggle Enable
        if mouse.dblclick and mouse.button == 3:
            blob.enable = not blob.enable
            print("blob enable: {}".format(blob.enable))
            # Shade gray when disabled
            if blob.enable:
                print("hey all")
                artist.set_color(self.label_colors[blob.label])
                artist.set_alpha(0.4)
            else:
                artist.set_color('gray')
                artist.set_alpha(0.05)

        # Change label if scrolling up or down
        elif mouse.button == "up" or mouse.button == 'down':
            up_down = {'up': +1, 'down': -1}
            new_label = self.labels[(self.labels.index(blob.label) + up_down[mouse.button]) % len(self.labels)]
            artist.set_color(self.label_colors[new_label])
            blob.label = new_label
        self.patches[artist][0] = blob
        self.axes.figure.canvas.draw_idle()

    def on_click_label(self, event):
        " add a new rectangle and blob object "

        # Send overlapping objects the the on_pick function
        for rect in self.patches:
            if rect.contains_point((event.x, event.y)):
                self._on_pick_label(event, rect)
                return

        # Create new label blob on right click
        if event.button == 3:
            # Initialize a new blob
            size = 50
            xy = (event.xdata, event.ydata)
            blob = Blob(xy)

            # Add a rectangle
            self._add_rectangle(blob)

            self.axes.figure.canvas.draw_idle()
        return

    def get_labels(self):
        """
        Return a dictionary of labels from the labeler.
        :return:
        """
        labels = {'label': [], 'x': [], 'y': [], 'width': [], 'height': []}
        for rect, blob in self.patches.items():
            blob = blob[0]
            if blob.enable:
                labels['label'].append(blob.label)
                bbox = rect.get_bbox()
                x, y = bbox.min
                w = bbox.width
                h = bbox.height
                labels['x'].append(x)
                labels['y'].append(y)
                labels['width'].append(w)
                labels['height'].append(h)
        return labels


def to_bbx_dict(bbx: list):
    """
    Converts bounding box from (XY),w,h to a dictionatry of corners x1, x2, y1, and y2.
    where x1 and y1 are lower in value than x2 and y2

    :param bbx: list containing corner point and width and height of bounding box [(x,y), w,h]
    :return: dictionary of bounding box corners
    :rtype: dict
    """
    xy, w, h = bbx
    x_vals = [xy[0], xy[0] + 2]
    y_vals = [xy[1], xy[1] + h]
    x_vals.sort()
    y_vals.sort()
    new_box = {'x1': x_vals[0], 'y1': y_vals[0], 'x2': x_vals[1], 'y2': y_vals[1]}
    return new_box


def get_iou(bb1, bb2):
    """
    Calculate the Intersection over Union (IoU) of two bounding boxes.

    bb1 is (xy),w,h of bounding box 1, and bb2 is (xy),w,h of bounding box 2

    For axis-aligned bounding boxes it is relatively simple. "Axis-aligned" means that the bounding box isn't rotated;
    or in other words that the boxes lines are parallel to the axes.
    @Martin Thoma, StackOverflow
    https://stackoverflow.com/questions/25349178/calculating-percentage-of-bounding-box-overlap-for-image-detector-evaluation

    Parameters
    ----------
    bb1 : dict
        Keys: {'x1', 'x2', 'y1', 'y2'}
        The (x1, y1) position is at the top left corner,
        the (x2, y2) position is at the bottom right corner
    bb2 : dict
        Keys: {'x1', 'x2', 'y1', 'y2'}
        The (x, y) position is at the top left corner,
        the (x2, y2) position is at the bottom right corner

    Returns
    -------
    float
        in [0, 1]
    """

    assert bb1['x1'] < bb1['x2']
    assert bb1['y1'] < bb1['y2']
    assert bb2['x1'] < bb2['x2']
    assert bb2['y1'] < bb2['y2']

    # determine the coordinates of the intersection rectangle
    x_left = max(bb1['x1'], bb2['x1'])
    y_top = max(bb1['y1'], bb2['y1'])
    x_right = min(bb1['x2'], bb2['x2'])
    y_bottom = min(bb1['y2'], bb2['y2'])

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    # The intersection of two axis-aligned bounding boxes is always an
    # axis-aligned bounding box
    intersection_area = (x_right - x_left) * (y_bottom - y_top)

    # compute the area of both AABBs
    bb1_area = (bb1['x2'] - bb1['x1']) * (bb1['y2'] - bb1['y1'])
    bb2_area = (bb2['x2'] - bb2['x1']) * (bb2['y2'] - bb2['y1'])

    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = intersection_area / float(bb1_area + bb2_area - intersection_area)
    assert iou >= 0.0
    assert iou <= 1.0
    return iou


def from_df_to_list(df):
    """
    Takes bounding box data from a data frame and puts it into a list
    """
    blobs = []
    for index, row in df.iterrows():
        new_blob = Blob()
        new_blob.from_dataframe(row)
        blobs.append(new_blob)
    return blobs


def compare_blobs_iou(blobs_test, blobs_truth):
    """
    Calculates the Intersection over union of a series of test blobs and their corresponding truth blobs
    """
    scores = []
    for true_blob in blobs_truth:
        max_iou = 0

        for blob in blobs_test:
            iou = blob.get_blob_iou(true_blob)
            if iou > max_iou:
                max_iou = iou
        scores.append(max_iou)
    return np.asarray(scores)
