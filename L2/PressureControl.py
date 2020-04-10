# Implement a Factory for the pressure control.
from abc import ABC, abstractmethod
from L2.Utility import UtilityControl, UtilityFactory


class PressureAbstraction(ABC):
    """
    Utility class for applying pressure and vacuum to the outlet vial of a CE apparatus.

    Pressure control consists of a few main functions:
    rinse_pressure = Applies a pressure to the outlet
    rinse_vacuum = Applies a vacuum to the outlet
    release = Opens the outlet to atmospheric pressure
    seal = Closes the outlet, sealing it from all pressure sources
    """

    def __init__(self, controller):
        self.controller = controller
        self.state ='Sealed'

    @abstractmethod
    def rinse_pressure(self):
        pass

    @abstractmethod
    def rinse_vacuum(self):
        pass

    @abstractmethod
    def release(self):
        pass

    @abstractmethod
    def seal(self):
        pass



class ArduinoPressure(PressureAbstraction, UtilityControl):
    """
    Arduino control class for the Outlet pressure control (Not designed for microchip pressure control).
    Arduino uses TTL MOSFET switches to turn on/off normally closed solenoid valves. Each valve is connected to a common
    tube to the outlet. The other ends of the valves are connected to air (release), pressure line (pressure), vacuum
    line (vacuum).

    It also incorporates the UtilityControl class for basic utility functions (shutdown, startup, get status, etc...)
    """

    def __init__(self, controller):
        super().__init__(controller)

    def startup(self):
        """
        On start up we want pressure and vacuum off while the outlet is kept at room pressure.
        :return:
        """
        self._default_state()

    def get_status(self):
        return self.state

    def shutdown(self):
        """
        When shutting down we want pressure and vacuum off while the outlet is kept at room pressure
        :return:
        """
        self._default_state()

    def _default_state(self):
        self.seal()
        self.release()

    def rinse_pressure(self):
        self.controller.send_command('P0R\n')
        self.state = 'Pressure'

    def rinse_vacuum(self):
        self.controller.send_command('P0V\n')
        self.state = 'Vacuum'

    def release(self):
        self.controller.send_command('P0S\n')
        self.state = 'Release'

    def seal(self):
        self.controller.send_command('P0C\n')
        self.state = 'Seal'


class SimulatedPressure(PressureAbstraction, UtilityControl):
    """
    Simulated pressure class. Uses the same ArduinoPressure class which should function as a simulated class
    when a SimulatedController object is used.
    """

    def __init__(self, controller):
        super().__init__(controller)
        # some private properties for the simulation
        self._pressure_valve = False
        self._vacuum_valve = False
        self._release_valve = False

    def _default_state(self):
        """ To get to default state, shut all valves then open the release valve"""
        self.seal()
        self.release()

    def startup(self):
        """ Sets valves to default state """
        self._default_state()

    def shutdown(self):
        """ Returns valves to default state """
        self._default_state()

    def get_status(self):
        """ Returns the status of the three solenoid valves"""
        return "Pressure: {}, Vacuum: {}, Release: {}".format(self._pressure_valve,
                                                              self._vacuum_valve,
                                                              self._release_valve)

    def rinse_pressure(self):
        """ Open the rinse pressure solenoid"""
        self._pressure_valve = True

    def rinse_vacuum(self):
        """ Open the vacuum pressure solenoid"""
        self._vacuum_valve = True

    def release(self):
        """ Open the release solenoid"""
        self._release_valve= True

    def seal(self):
        """Close all solenoid valves """
        self._release_valve = False
        self._vacuum_valve = False
        self._pressure_valve = False

class PressureControlFactory(UtilityFactory):
    """ Determines the type of pressure utility object to return according to the controller id"""

    def build_object(self, controller):
        if controller.id == 'arduino':
            return ArduinoPressure(controller)
        elif controller.id == 'simulator':
            return SimulatedPressure(controller)
        else:
            return None


if __name__ == "__main__":
    from L1.Controllers import SimulatedController
    controller = SimulatedController()
    pressure = SimulatedPressure(controller)



