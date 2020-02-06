import unittest
import sys
import os
path = os.getcwd()
parent_path = path[:path.find('BarracudaQt')+11]
if not parent_path in sys.path:
    sys.path.append(parent_path)
import time
sys.path.insert(0,os.pardir)
from hardware import ZStageControl
from hardware import ObjectiveControl
from hardware import XYControl
from hardware import OutletControl
from hardware import PressureControl

class ZStageTestCase(unittest.TestCase):

    def setUp(self):
        self.z_stage = ZStageControl.ThorLabZStage()

    def tearDown(self):
        self.z_stage.close()

    def test_go_home(self):
        """
        Test the Go Home function. Stage should move to home position and set that position to be zero
        :return:
        """
        self.z_stage.go_home()
        final_pos = self.z_stage.read_z()
        self.assertEqual(0.1,final_pos, "Stage did not go to home")


    def test_set_and_read_z(self):
        """
        Test the move function (requires a wait_for_move function) and the read height functions
        Move the stage back to zero for other tests.
        :return:
        """
        self.z_stage.set_z(0.1)
        self.z_stage.stage.wait_for_move()
        self.z_stage.set_z(1.5)
        final_pos = self.z_stage.stage.wait_for_move()
        self.assertAlmostEqual(1.5,final_pos,1,"Stage did not move to expected location (or is not updating)")

class ObjectiveTesting(unittest.TestCase):
    """ Tests the Objective functions"""

    def setUp(self):
        """ Create the objective control object"""
        self.obj = ObjectiveControl.ObjectiveControl(com="COM8", home=False)

    def tearDown(self):
        """ Close the objective"""
        self.obj.close()

    def test_home(self):
        """ Home function will always move the stage + 5 microns above 0, so we should make sure
         we see that +5 step when we go home
         """
        self.obj.go_home()
        pos = self.obj.read_z()
        self.assertAlmostEqual(5,pos,1,"Objective did not return to Home")
        return

    def test_move(self):
        """
        When the objective moves, the encoder should keep track (within 1 micron). This test
        moves the objective up 100 microns and checks that the position has updated within
        the tolerance (1 micron).

        :return:
        """
        self.obj.set_z(100)
        pos = self.obj.wait_for_move()
        self.assertAlmostEqual(10,pos/10,1,"Objective did not move to desired location (or is not updating from encoder)")

class OutletMotorTesting(unittest.TestCase):
    """
    Tests the Outlet Motor Capability.
    Outlet should be able to return to a home location and recieve an 'OK' signal when home is reached.
    Outlet should be able to move up and down from the Home Position.
    """
    def setUp(self):
        """ Create the objective control object"""
        self.obj = OutletControl.OutletControl(com="COM4", home=False, invt=-1, test=True)

    def tearDown(self):
        """ Close the objective"""
        self.obj.close()

    def test_home(self):
        """ Tests whether the arudino can move to the outlet end stop

         """
        message = """ The outlet did not read the home position.
        The limit switch was not depressed. Verify the following:
        1) Is the outlet moving?
            If not check the power cables. 
        2) The outlet strikes the limit switch but does not stop immediatly. 
            Verify the limit switch is plugged into the Step01 correctly. A wire from TP01 should go to the limit switch
            Additionaly a second wire from ground should go to the limit switch. 
        3) The outlet moves down instead of up.
            Change the invt initialization parameter from 1 to -1. 
        """
        self.obj.go_home()
        pos = self.obj.read_z()
        self.assertAlmostEqual(self.obj.default_pos,pos,1, message)
        return

    def test_move(self):
        """
        Test the movement of the outlet.
        Outlet should be capable of moving to the target distance and report the distance.

        :return:
        """
        message = """ The outlet did not read the correct amount for the set. 
        1. Verify the outlet was moving. 
            If not check that the power is plugged in to the motor. 
        2. Verify the arduino conversion between and set and read is correct. 
        """
        start = self.obj.read_z()
        self.obj.set_rel_z(-2)
        pos = self.obj.wait_for_move()
        self.assertAlmostEqual(start-2,pos,1,message)

class OutletPressureTest(unittest.TestCase):
    """
    Tests the Outlet Pressure/Vacuum Capability.
    Pressure and vacuum lines should be hooked up.
    """
    def setUp(self):
        """ Create the Pressure Control object"""
        self.obj = PressureControl.PressureControl(com="COM4", home=False)

    def tearDown(self):
        """ Close the objective"""
        self.obj.close()

    def test_pressure(self):
        """
        Tests whether the pressure valve is correctly wired.
        :return:
        """
        message = """ Pressure function is not working. 
        1) Check that a pressure line is hooked up to the solenoids. 
        2) Verify the correct digital output pin is going to the pressure solenoid.
            At the time of writing, pin 41 is designated to the pressure valve.         
        """
        self.obj.apply_rinse_pressure()
        pressure = None
        while pressure != 'N' and pressure != 'Y':
            pressure = input("Is a rinse pressure applied to the outlet? (Y/N) ").upper()
            print(pressure)

        self.assertEqual('Y',pressure, msg=message)

    def test_vacuum(self):
        """
        Tests whether the vacuum valve is correctly wired.
        :return:
        """
        message = """ Vacuum function is not working. 
        1) Check that a vacuum line is hooked up to the solenoids. 
        2) Verify the correct digital output pin is going to the vacuum solenoid.
            At the time of writing, pin 43 is designated to the vacuum valve. 
        3) If pressure is applied instead of vacuum, try switching the pressure and vacuum lines.         
        """
        self.obj.apply_vacuum()
        vacuum = None
        while vacuum != 'N' and vacuum != 'Y':
            vacuum = input("Is a vacuum applied to the outlet? (Y/N) ").upper()
        self.assertEqual('Y', vacuum, msg=message)



def wait_for_move(motor):
    prev_pos = self.z_stage.read_z()
    current_pos = prev_pos + 1
    # Update position while moving
    while prev_pos != current_pos:
        time.sleep(0.5)
        prev_pos = current_pos
        current_pos = self.z_stage.read_z()

if __name__ == "__main__":
    unittest.main()