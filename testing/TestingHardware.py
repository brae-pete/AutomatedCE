import unittest
import sys
import os
import time
sys.path.insert(0,os.pardir)
from hardware import ZStageControl

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
        final_pos = self.z_stage.stage.wait_for_move()
        self.assertEqual(0,final_pos, "Stage did not go to home")


    def test_set_and_read_z(self):
        """
        Test the move function (requires a wait_for_move function) and the read height functions
        Move the stage back to zero for other tests.
        :return:
        """
        self.z_stage.set_z(0)
        self.z_stage.stage.wait_for_move()
        self.z_stage.set_z(1.5)
        final_pos = self.z_stage.stage.wait_for_move()
        self.z_stage.set_z(0)
        self.assertAlmostEqual(1.5,final_pos,1,"Motor did not move to expected location (or is not updating)")


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