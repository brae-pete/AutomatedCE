import sys
import os
from L4.TKui import *

sys.path.append(os.getcwd())

if __name__=="__main__":
    root = Tk()
    wn = RootWindow(root)
    root.protocol("WM_DELETE_WINDOW", wn.on_close)
    root.mainloop()
