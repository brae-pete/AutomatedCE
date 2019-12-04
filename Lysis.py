import CESystems
import time
import logging
from numpy import abs


class Lysis():
    cell_z = 0  # Objective focal plane for the cell

    def __init__(self, cap_control=None, cell_detection=None, hardware=CESystems.BarracudaSystem()):
        self.hardware = hardware

        # Initialize the capillary focus class if not passed
        if cap_control is None:
            cap_control = CapillaryControl(hardware)
        self.cap_control = cap_control

    def record_cell_focus(self):
        """ Records the focal point of the cell """
        self.cell_z = self.hardware.get_objective()

    def start_camera_acquisition(self, file_path=r"C:\Users\Barracuda\Pictures\Lysis"):
        """ Records images from the camera (flag?) """
        self.hardware.image_control.save_feed(file_path, 'Lysis')

    def laser_init(self, pfn=200, attn=100):
        # Check if laser is on/ Turn it on
        sleep = self.hardware.restart_laser_run_time()

        # Adjust laser settings
        self.hardware.set_laser_parameters(pfn, attn)
        if not sleep:
            time.sleep(9.5)

    def fire_laser_pulse(self):
        # Send Fire command
        self.hardware.laser_fire()

    def post_movement_lysis(self, pfn=200, attn=100):
        # Move to for points around the cell
        positions = [[50, 50], [0, -50], [-50, 50], [+25, -25]]
        self.laser_init(pfn, attn)
        self.start_camera_acquisition()
        self.hardware.set_outlet(rel_h=-8)
        time.sleep(1)
        self.fire_laser_pulse()
        for pos in positions:
            time.sleep(0.01)
            self.hardware.set_xy(rel_xy=pos)
            time.sleep(0.01)
            self.fire_laser_pulse()
        time.sleep(1.5)
        self.hardware.set_outlet(rel_h=8)


    def lower_capillary(self):
        # Lower capillary to position above the cell
        self.cap_control.move_cap_above_cell()


class CapillaryControl:
    last_cap_height = None  # Last capillary position above the cell
    last_obj_height = None  # Last cell focus position
    units_above = 50
    obj2cap = 1/1000

    def __init__(self, hardware=CESystems.BarracudaSystem()):
        self.hardware = hardware

    def record_cell_height(self):
        """ Records the previous cell position from manual acquisition"""
        self.last_obj_height = self.hardware.get_objective()

    def record_cap_height(self):
        """ Records previous cap height, 50 obj units above, from manual
        focusing
        """
        self.last_cap_height = self.hardware.get_z()

    def calculate_cap_difference(self):
        """ if the objective is lower by 5 units, the capillary must also
        be lower by 5 units (which corresponds to increasing the distance from
        home by 0.005). Units of objective ~ um, Units of cap ~ mm"""
        cap_adjust = (self.hardware.get_objective() - self.last_obj_height) * self.obj2cap + self.last_cap_height
        return cap_adjust

    def move_cap_above_cell(self):
        """
        Move the capillary above the cell according to the calculate_cap_difference equation

        :return:
        """
        if self.last_cap_height is None or self.last_obj_height is None:
            logging.warning("You have not set the capillary or cell focal planes")
            return False
        total = self.calculate_cap_difference()
        #self.hardware.set_z(total+0.5)
        #while abs(total - self.hardware.get_z()) >0.505:
        #    time.sleep(0.2)
        #time.sleep(1)
        self.hardware.jog_z(total - self.hardware.get_z())
        while abs(total - self.hardware.get_z()) > 0.03:
            time.sleep(0.2)
        return True


if __name__ == "__main__":
    import threading

    hardware = CESystems.BarracudaSystem()
    hardware.start_system()
    m = Lysis(hardware=hardware)
    hardware.image_control.live_view()
