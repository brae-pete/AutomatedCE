import sys
import os
from L4.TKui import *

sys.path.append(os.getcwd())

if __name__=="__main__":
    root = Tk()
    wn = RootWindow(root)
    root.protocol("WM_DELETE_WINDOW", wn.on_close)
    #wn.system_queue.send_command('system.load_config', r'E:\Scripts\AutomatedCE\config\TestChip.cfg' )
    root.mainloop()
