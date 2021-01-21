import unittest
import sys
import os
import time
sys.path.insert(0,os.pardir)
from hardware import ZStageControl
from hardware import ObjectiveControl
from hardware import XYControl

class ZStageTestCase(unittest.TestCase):

    def setUp(self):
        self.z_stage = ZStageControl.ZStageControl()

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
        self.obj = ObjectiveControl.ObjectiveControl(com="COM8", home=False)

    def tearDown(self):
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