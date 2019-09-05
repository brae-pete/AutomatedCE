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


if __name__ == "__main__":
    hd = CESystems.BarracudaSystem()
    hd.start_system()
    hd.start_feed()
    time.sleep(2)
    frame = hd.get_image()

    fig = plt.figure()
    im = plt.imshow(frame, cmap='gist_gray')
    anim = animation.FuncAnimation(fig, animate, init_func=init, interval=50)
