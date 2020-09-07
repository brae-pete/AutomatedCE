import sys
import os
from L4.TKui import *

sys.path.append(os.getcwd())

if __name__=="__main__":
    root = Tk()
    wn = RootWindow(root)
    root.protocol("WM_DELETE_WINDOW", wn.on_close)
    FILE = r"C:\Users\NikonTE300CE\Desktop\Barracuda\AutomatedCE\var\TE300.cfg"
    wn.system_queue.config = FILE
    #wn.system_queue.send_command('system.load_config', FILE )
    #wn.system_queue.send_command('system.load_config', config_file=FILE)
    #wn.system_queue.send_command('system.open_controllers')
    #wn.system_queue.send_command('system.startup_utilities')
    wn.system_queue.start_process()

    root.mainloop()
