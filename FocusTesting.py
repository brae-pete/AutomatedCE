import CESystems
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation
import time
import logging


def init():
    pass

def animate(i):
    frame = hd.get_image()
    try:
        im.set_data(frame)
    except TypeError:
        logging.warning("Could not load image")
    return im

def record_data(hd_ware,dataset):
    """

    :param hd_ware: CESystems object with all hardware classes
    :param dataset: np.array of positions. Xy, Obj, and Capillary where the capillary was in focus.
    :return: dataset
    """
    if dataset == None:
        dataset=np.zeros((0,4))

    new_data=[0,0,0,0]
    new_data[0:1] = hd_ware.get_xy()
    new_data[2] = hd_ware.get_objective()
    new_data[3] = hd_ware.get_z()

    np.r_[dataset,[new_data]]




if __name__ == "__main__":
    hd = CESystems.BarracudaSystem()
    hd.start_system()
    hd.start_feed()
    time.sleep(2)
    hd.home_z()
    hd.home_objective()
    frame = hd.get_image()

    fig = plt.figure()
    im = plt.imshow(frame, cmap='gist_gray')
    anim = animation.FuncAnimation(fig, animate, init_func=init, interval=50)
