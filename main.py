import CEControl

import sys
try:
    system = sys.argv[1]
    print(sys.argv)
except:
    system = 'CE_TiEclipse'
if __name__ == '__main__':
    from CENetworks import Config
    pc = CEControl.ProgramController(user=system)
