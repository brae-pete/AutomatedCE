import logging

import serial


class Laser:
    _safety_pfn_limit = 95

    def __init__(self, com="COM6", baudrate=9600, stopbits=1, timeout=0.5, home=False):
        self.serial = serial.Serial()
        self.serial.timeout = timeout
        self.serial.baudrate = baudrate
        self.serial.stopbits = stopbits
        self.serial.port = com
        if not home:
            self.serial.open()

        self.commands = {'MANUFACTURERS_DATE': ';LAMD{}\r'.format,  # ?
                         'ATTENUATION': ';LAAT{}\r'.format,  # ? or ### (000 - 255)
                         'BURST_COUNT': ';LABU{}\r'.format,  # ? or #### (0001 - 4000)
                         'ENABLE_Q-SWITCH': ';LADQ{}\r'.format,  # ? or # (0 (enable) or 1 (disable))
                         'ENABLE_COMMAND_ECHO': ';LAEC{}\r'.format,  # ? or # (0 (disable) or 1 (enable))
                         'FIRE': ';LAGO\r'.format,  # no input
                         'WAVELENGTH': ';LAHS{}\r'.format,  # ? or #? or #. #? returns filter configuration byte.
                         'LASER_STATUS': ';LAIS\r'.format,  # no input
                         'LASER_TYPE': ';LALT{}\r'.format,  # ?
                         'LASER_MODE': ';LAMO{}\r'.format,  # ? or # (0 is continuous, 1 is single shot, 2 is burst)
                         'MAXIMUM_REPETITION_RATE': ';LAMR{}\r'.format,  # ?
                         'NUMBER_HOLES': ';LANH{}\r'.format,  # ?
                         'LASER_OFF': ';LAOF\r'.format,  # no input
                         'LASER_ON': ';LAON\r'.format,  # no input
                         'PULSE_MODE': ';LAPM{}\r'.format,  # ? or # (1 enables long pulse, 0 disables it)
                         'ROTATING_POLARIZER': ';LARP{}\r'.format,  # ### (0 to max channel travel)
                         'ROTATING_POLARIZER_POSITION': ';LARP{}\r'.format,  # ? or xxx (measured in motor steps)
                         'ROTATING_POLARIZER_TRAVEL': ';LARPT{}\r'.format,  # ?
                         'ROTATING_POLARIZER_ZERO': ';LARPTZ{}\r'.format,  # ? or xxx!
                         'LASER_REPETITION_RATE': ';LARR{}\r'.format,  # ? or ###
                         'RESET': ';LARS\r'.format,  # no input
                         'LASER_SHOT_COUNT': ';LASC\r'.format,  # no input
                         'SERIAL_MODE': ';LASM{}\r'.format,  # ? or # (0 is off and 1 is on)
                         'SERIAL_NUMBER': ';LASN{}\r'.format,  # ?
                         'SPOT_MARKER_CONTROL': ';LASP{}\r'.format,  # ? or ### (000 - 255)
                         'SHUTTER_ROTATION_CONTROL': ';LASR{}\r'.format,  # ? or T? or +/-##
                         'SYSTEM_STATUS': ';LASS\r'.format,  # no input
                         'STOP_FIRING': ';LAST\r'.format,  # no input
                         'ACCESSORY_CONFIGURATION': ';LASV{}\r'.format,  # ?
                         'PFN_VOLTAGE': ';LAVO{}\r'.format,  # ?  or ### (000 - 255)
                         'VERSION_NUMBER': ';LAVN\r'.format,  # no input
                         'LASER_WARM_UP_MODE': ';LAWU{}\r'.format,  # ? or ####
                         'X_SHUTTER': ';X{}\r'.format,  # S? or T? or S###
                         'Y_SHUTTER': ';Y{}\r'.format}  # S? or T? or S###

    def read_buffer(self):
        response = self.serial.readlines()
        response = response[0].rsplit('\r')[0]
        return response

    def check_status(self):
        print('** LASER SYSTEM STATUS **\n')
        self.serial.write(self.commands['SYSTEM_STATUS']())
        response = self.read_buffer()
        if response == 'ok':
            print('\t System OK!')
            return

        response = '{:024b}'.format(int(response))

        is_not = 'not ' if response[23] == 1 else ''
        print('\tThe coolant flow interlock is {}satisfied.'.format(is_not))

        is_not = '' if response[22] == 1 else 'not '
        print('\tThe laser has {}overheated.'.format(is_not))

        is_not = 'not ' if response[21] == 1 else ''
        print('\tThe external interlock is {}satisfied.'.format(is_not))

        is_not = 'not ' if response[20] == 1 else ''
        print('\tThe workpiece interlock is {}satisfied.'.format(is_not))

        is_not = '' if response[19] == 1 else 'not '
        print('\tThe laser power supply is {}enabled'.format(is_not))

        is_not = '' if response[18] == 1 else 'not '
        print('\tThe laser is {}firing.'.format(is_not))

        is_not = '' if response[17] == 1 else 'not '
        print('\tThe laser is {}in its startup state.'.format(is_not))

        is_not = '' if response[16] == 1 else 'not '
        print('\tThe laser is {}in RS232 Mode'.format(is_not))

        is_not = '' if response[15] == 1 else 'not '
        print('\tThe Q-Switch is {}set to external trigger mode.'.format(is_not))

        is_not = '' if response[14] == 1 else 'not '
        print('\tThe flashlamp is {}set to external trigger mode.'.format(is_not))

        is_not = '' if response[13] == 1 else 'not '
        print('\tThe laser is {}in single-shot mode.'.format(is_not))

        is_not = '' if response[12] == 1 else 'not '
        print('\tThe laser is {}in continuous fire mode.'.format(is_not))

        is_not = '' if response[11] == 1 else 'not '
        print('\tThe laser is {}in burst fire mode.'.format(is_not))

        is_not = 'not ' if response[10] == 1 else ''
        print('\tThe Q-Switch is {}enabled.'.format(is_not))

        is_not = '' if response[9] == 1 else 'not '
        print('\tThe laser is {}in fixed repetition rate mode.'.format(is_not))

        is_not = '' if response[8] == 1 else 'not '
        print('\tThe laser is {}firing in warm-up mode.'.format(is_not))

        is_not = 'not' if response[7] == 1 else ''
        print('\tThe closed loop control system can{} meet current energy target.'.format(is_not))

        # print('Unused Bit: {}'.format(response[6]))

        is_not = '' if response[5] == 1 else 'not '
        print('\tThe laser is {}initializing the position of one or more motor-driven accessories.'.format(is_not))

        is_not = '' if response[4] == 1 else 'not '
        print('\tThe coolant level is {}low.'.format(is_not))

        is_not = 'An accessory motor' if response[3] == 1 else 'No accessory motor'
        print('\t{} is moving.'.format(is_not))

        is_not = '' if response[2] == 1 else 'not '
        print('\tThe laser is {}OK to start.'.format(is_not))

        is_not = '' if response[1] == 1 else 'not'
        print('\tThe laser can{} be fired.'.format(is_not))

        is_not = '' if response[0] == 1 else 'not '
        print('\tA reset fault has {}occurred.\n'.format(is_not))

    def check_parameters(self):
        print('** LASER SETTINGS **\n')
        self.serial.write(self.commands['WAVELENGTH']('?'))
        response = self.read_buffer()
        print('\tWavelength set to: {}'.format(response))

        self.serial.write(self.commands['ATTENUATION']('?'))
        response = self.read_buffer()
        print('\tAttenuation set to: {}'.format(response))

        self.serial.write(self.commands['BURST_COUNT']('?'))
        response = self.read_buffer()
        print('\tBurst Count set to: {}'.format(response))

        self.serial.write(self.commands['LASER_MODE']('?'))
        response = self.read_buffer()
        print('\tLaser Mode set to: {}'.format(response))

        # self.serial.write(self.commands['PULSE_MODE']('?')) # fixme unrecognized command?
        # response = self.read_buffer()
        # print('\tPulse Mode set to: {}'.format(response))

        self.serial.write(self.commands['PFN_VOLTAGE']('?'))
        response = self.read_buffer()
        print('\tPFN Voltage set to: {}'.format(response))

        self.serial.write(self.commands['ACCESSORY_CONFIGURATION']('?'))
        response = self.read_buffer()
        print('\tConfiguration: {0:08b}\n'.format(int(response)))

    def poll_status(self):
        # You must periodically (once every 2 seconds) send either LASER_STATUS or SYSTEM_STATUS command to poll the
        # laser status while it is enabled or it will shutdown automatically.

        self.serial.write(self.commands['LASER_STATUS']())
        response = self.read_buffer()
        response = '{:08b}'.format(int(response))
        return response

    def set_parameters(self, pfn, attenuation, mode):
        # These limits are defined by the manufacturers
        LEN_INPUT = 3
        MAX_ATTENUATION = 255
        LASER_MODES = ['0', '1', '2']  # Continuous, Single, Burst

        if len(pfn) != LEN_INPUT or int(pfn) > self._safety_pfn_limit:
            return False
        self.serial.write(self.commands['PFN_VOLTAGE'](pfn))

        if len(attenuation) != LEN_INPUT or int(attenuation) > MAX_ATTENUATION:
            return False
        self.serial.write(self.commands['ATTENUATION'](attenuation))

        if mode not in LASER_MODES:
            return False
        self.serial.write(self.commands['LASER_MODE'](mode))

        return True                 

    def start_system(self):
        self.serial.write(self.commands['SERIAL_MODE']('?'))
        response = self.read_buffer()
        if response != 'ok':
            logging.info('Enabling serial mode for laser.')
            self.serial.write(self.commands['SERIAL_MODE']('1'))
            response = self.read_buffer()
            logging.info('Laser Response is {}'.format(response))

        self.serial.write(self.commands['SYSTEM_STATUS']())
        response = self.serial.readlines()
        response = '{:024b}'.format(int(response[0].rsplit('\r')[0]))
        if response[0] == 1 or response[3] == 1 or response[4] == 1 or response[5] == 1 or response[7] == 1 or \
            response[8] == 1 or response[17] == 1 or response[18] == 1 or response[20] == 1 or response[21] == 1 or \
                response[22] == 1 or response[23] == 1:
            print('Check system status for problems. Cannot start laser.')

        self.serial.write(self.commands['LASER_ON']())
