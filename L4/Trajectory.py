"""
More of a Functional Programming style here...

Pathfinder -> Finds the path a motor will take when moving from point A to point B.

Calc_Delay -> User gives lists of

"""
import logging
import time
import numpy as np
from scipy import optimize
from L3.SystemsBuilder import CESystem
from L4 import AutomatedControl
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod

class Move(ABC):
    def __init__(self, system, template, xyz0, xyz1, simulated=False, path_information=[]):
        self.system = system
        self.template = template
        self.xyz0 = xyz0
        self.xyz1 = xyz1
        self.simulated = simulated
        self.path_information = path_information
    @abstractmethod
    def move(self):
        """
        Logic to move from one location to the next in a CE run should be called here
        """
        pass

class StepMove(Move):

    def __init__(self, system, template, xyz0, xyz1, simulated, path_information):
        super().__init__(system, template, xyz0, xyz1, simulated,  path_information)

    def move(self):
        """
        Moves the XY Stage and Inlet Z stage in a systematic way. It caclulates the highest ledge on the template
        and uses that as the safe transfer height

        Move in this order:
        Move the Z Stage up
        Move the XY Stage across
        Move the Z Stage Down
        """

        x0,y0,z0 = self.xyz0
        x1,y1,z1 = self.xyz1
        transfer_height = self.template.get_max_ledge()

        # Move the Z stage, wait for the target height to be reached
        self.path_information.append(f"Moving capillary Z stage to {transfer_height} mm")
        if not self.simulated:
            self.system.inlet_z.set_z(transfer_height)
            if not self.system.inlet_z.wait_for_target(transfer_height):
                return False

        # Move the XY Stage
        self.path_information.append(f"Moving Stage to {x1},{y1} mm")
        if not self.simulated:
            self.system.xy_stage.set_xy([x1,y1])
            # Return false if the stage did not move
            if not self.system.xy_stage.wait_for_xy_target([x1, y1]):
                return False

        # Move the Z Stage back down
        self.path_information.append(f"Moving capillary Z stage to {z1}")
        if not self.simulated:
            self.system.inlet_z.set_z(z1)
        return True



class SafeMove(Move):

    def __init__(self, system, template, xyz0, xyz1, simulated, path_information, visual=False):
        super().__init__(system, template, xyz0, xyz1, simulated, path_information)
        self.visual = visual
        self.display_data = {}

    def move(self):
        """
        Moves the XY stage and Inlet Z stage in a way as to prevent any collisions with the template ledges defined
        by the user.
        :return:
        """
        # Get information about the move
        x0, y0, z0 = self.xyz0
        x1, y1, z1 = self.xyz1
        # Get the ledge heights at the start and end point
        ledge_1 = self.template.get_intersection([x1], [y1])[0]

        # Get the max ledge height on the template for the path the stage will take
        [xx, yy] = _get_motor_path([x0, y0], [x1, y1], self.system.xy_stage)
        ledge_z = self.template.get_intersection(xx, yy)

        # The end point should be at least the ledge height
        z1 = max(z1, ledge_1)

        # Determine the max height over the entire range
        mid_max = max(ledge_z.max(), z0, z1)
        zz = [0]
        # Determine the increase move step (moving from start point to max point)
        xy_stage_delay = 0
        if mid_max > z0:
            # Move the Z inlet first then the XY stage after delay
            st = time.time()
            self.system.inlet_z.set_z(mid_max)

            # Calculate the xy delay
            zz = _get_motor_path([z0], [mid_max], self.system.inlet_z)[0]
            xy_stage_delay = self.get_delay(ledge_z, zz, increasing=True)
            while time.time() - st < xy_stage_delay:
                time.sleep(0.01)

        # Move the XY stage (only after the capillary has increased its height sufficiently)
        st = time.time()
        self.path_information.append(f"Moving xy stage to {x1},{y1} mm")
        if not self.simulated:
            self.system.xy_stage.set_xy([x1, y1])
        zz_decrease = [0]
        # Determine the decrease move step delay (moving down from our max point to final point)
        z_stage_down_delay = 0
        if mid_max > z1:
            zz_decrease = _get_motor_path([mid_max], [z1], self.system.inlet_z)[0]
            z_stage_down_delay = self.get_delay(ledge_z, zz_decrease, increasing=False)
            while time.time() - st < z_stage_down_delay:
                time.sleep(0.01)
            self.path_information.append(f"Moving capillary Z stage to {z1}")
            if not self.simulated:
                self.system.inlet_z.set_z(z1)

        # We may have to lower the outlet if the user overrode the ledge height for the current location
        if z1 != self.xyz1[2]:
            time_xy = len(xx) / 1000
            while time.time() - st < time_xy:
                time.sleep(0.01)
            self.path_information.append(f"Moving capillary Z stage to {self.xyz1[2]}")
            if not self.simulated:
                self.system.inlet_z.set_z(self.xyz1[2])

        # Record data if necessary
        if self.visual:
            self.visualize(xx, yy, ledge_z, zz, zz_decrease, xy_stage_delay, z_stage_down_delay)

        return True

    def visualize(self, xx, yy, ledge_z, zz, zz_decrease, xy_delay, z_delay):
        self.display_data['xx'] = xx
        self.display_data['yy'] = yy
        self.display_data['zz_ledge'] = ledge_z
        self.display_data['z_incr'] = zz
        self.display_data['z_decr'] = zz_decrease
        tt_time = np.linspace(0,xx.shape[0]/1000, xx.shape[0])
        plt.plot(tt_time,xx, label = 'X-Motor')
        plt.plot(tt_time, yy, label='Y-motor')
        plt.plot(tt_time, ledge_z, label ='Ledges')
        if len(zz)>1:
            logging.info(f"Increase Delay: {xy_delay}")
            tt_time = np.linspace(-xy_delay, -xy_delay+len(zz)/1000, len(zz))
            plt.plot(tt_time, zz, label ='Increasing Inlet')
        if len(zz_decrease)>1:
            logging.info(f"Decrease Delay: {z_delay}")
            tt_time = np.linspace(z_delay, z_delay+ len(zz_decrease)/1000, len(zz_decrease))
            plt.plot(tt_time, zz_decrease, label = "Decreasing Inlet")
        plt.legend()
        plt.show()

    @staticmethod
    def get_delay(ledge, zz, increasing=True, tolerance=0.5):
        ledge = ledge - tolerance
        ledge, zz = _normalize_paths([ledge, zz])
        # Get the delay time_data needed between the stages
        delay = 0
        collision = zz - ledge
        # Move our zz array forward one (increase delay it will reach the ledge), do the opposite for decreasing
        while (collision < 0).any():
            if increasing:
                zz[:-1] = zz[1:]
            else:
                zz[1:] = zz[0:-1]
            delay += .001
            collision = zz - ledge
        return delay


def _get_ledge_heights(template, xx, yy):
    """
    Calculates the ledge height values for a path given by xx,yy. Can be thought of as z = z(x,y) so calculate z
    for every value of xx, yy.
    :param template: template object from L4.AutomatedControl
    :param xx: np.array # XX path values
    :param yy: np.array # YY path values
    :return zz: np.array # the height of ledges along the path given by xy
    """
    zz = np.zeros(xx.shape[0])
    for _, ledge in template.ledges.items():
        zz += ledge.get_intersection(xx, yy)
    return zz


def _get_motor_path(xy1, xy2, motor):
    """
    Returns an XY path given the start (xy1) and stop (xy2) coordinates.
    :param xy1: [float, float] # start coordinates
    :param xy2: [float, float] # stop coordinates
    :param system: # CE System object with XY_stage
    :return: [np.array, np.array] # Containing the XX and YY values for the path
    """
    v, a, j = motor.velocity_max, motor.acceleration, motor.jerk
    xy_path = []


    for start, stop in zip(xy1, xy2):

        if start > stop:
            diff = start-stop
            invert =-1
        else:
            diff = stop-start
            invert=1

        if j == 0:
            # For now assume very high J, but should go back and write new function
            j = a * 500

        path_arr = _get_path(diff, v, a, j)*invert
        path_arr += start
        xy_path.append(path_arr)

    return _normalize_paths(xy_path)


def _normalize_paths(xyz):
    """
    Make the paths the same length by padding 0's to the end of shorter arrays
    :param xyz: [np.array...]
    :return: [np.array]
    """
    sizes = [p.shape[0] for p in xyz]
    new_size = max(sizes)
    new_xyz = [np.pad(p, (0, new_size - p.shape[0]), 'edge') for p in xyz]
    return new_xyz


def _get_velocity_difference(a_max, j, v_max):
    return v_max - (a_max * a_max / j)


def _derivative_velocity_difference(a_max, j, v_max):
    return -2 * a_max / j


def _get_distance_diff(v_max, xf, a, j, extra=False):
    """
    At the given velocity setting, find out how far we will overshoot the distance and return the difference between
    the desired distance xf, and the calculated distance (integral of the velocity profile)

    You may be able to simplify the acceleration optimization by first assuming constant acceleration, then implementing a
    ramp later.


    """
    divisions = 1000
    vm = _get_velocity_difference(a, j, v_max)

    dt = 0

    # If we overshoot our velocity maximum we must adjust our acceleration
    if vm < 0:
        a = optimize.newton(_get_velocity_difference, 1, fprime=_derivative_velocity_difference, args=(j, v_max))

    else:
        dt = vm / a

        q_c = np.linspace(a, a, int(round(dt * divisions)))

    # Get accel profile

    q1 = np.linspace(0, a, int(round(a / j * divisions)))
    q3 = np.linspace(a, 0, int(round(a / j * divisions)))

    if dt != 0:
        q1 = np.concatenate((q1, q_c))

    accel_profile = np.concatenate((q1, q3))

    x = np.zeros(len(accel_profile))
    # x = np.asarray([ np.trapz(accel_profile[:idx]) for idx in range(len(accel_profile))] # This is much slower (100x)
    step = 1 / (a / j * divisions)
    dx = 0
    for ix, y in enumerate(accel_profile):
        # dx += step*y
        # x[ix] = dx
        x[ix] = np.trapz(accel_profile[:ix] / divisions)  # This is Slower (10x) but more accurate
    xcalc = np.trapz(x / divisions)
    if extra:
        return xf - 2 * xcalc, x, step, accel_profile
    return xf - xcalc * 2


def _slow_optimize(f, var, args=None, tol=.01, iterations=50):
    logging.debug("Optmizing Velocity for Short Distance")
    initial = f(var, *args)
    step = var / 20
    best_initial = np.abs(initial)
    best_var = var
    idx = 0

    solutions = [var]
    errors = [initial]
    abs_initial = best_initial
    while abs_initial > tol and idx < iterations:
        idx += 1

        if abs_initial < best_initial * 0.5 and abs_initial < 8:
            step *= 0.5
            best_var = var
            best_initial = np.abs(initial)

        if initial < 0:
            if var - step < step:
                step = 0.1 * step
            var -= step
        else:
            var += step

        initial = f(var, *args)
        abs_initial = np.abs(initial)
        solutions.append(var)
        errors.append(initial)

        logging.debug(f" Velocity: {var}, Displacement in X: {initial}")
    return var


def _get_path(xf, vmax=10, a=20, j=200, extra=False):
    """
    xf = final distance (assume start at 0)
    vmax = maximum velocity (u/s)
    a = maximum acceleration (u/s/s)
    j = jerk (u/s/s/s)
    """

    xcalc, velocity, step, accel = _get_distance_diff(vmax, xf, a, j, extra=True)

    if xcalc < 0:
        vmax = _slow_optimize(_get_distance_diff, vmax, args=(xf, a, j), tol=0.5)
        xcalc, velocity, step, accel = _get_distance_diff(vmax, xf, a, j, extra=True)
        v_profile = velocity.copy()
        if extra:
            accel = np.concatenate((accel, -accel))

    else:
        extra_t = xcalc / vmax
        extra_v = np.linspace(vmax, vmax, int(round(extra_t * 1000)))
        v_profile = velocity.copy()
        v_profile = np.concatenate((v_profile, extra_v))
        if extra:
            extra_a = np.zeros(int(round(extra_t * 1000)))
            accel = np.concatenate((accel, extra_a, -accel))

    v_profile = np.concatenate((v_profile, np.flip(velocity)))
    x = np.zeros(len(v_profile))
    for i, v in enumerate(v_profile):
        x[i] = np.trapz(v_profile[:i])

    if extra:
        return x / 1000, v_profile, accel
    return x / 1000


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    system = CESystem()
    system.load_config()
    system.open_controllers()
    tm = AutomatedControl.Template()
    xyz0 = [20, 20, 3]
    xyz1 = [100, 35, 10]
    path = SafeMove(system, tm, xyz0, xyz1, visual=True).move()


