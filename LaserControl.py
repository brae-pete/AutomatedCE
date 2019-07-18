# Standard Library Modules
import logging
import threading

# Installed Modules
import serial  # PySerial


class Laser:
    _safety_pfn_limit = 95

    def __init__(self, com="COM6", baudrate=9600, stopbits=1, timeout=0.5, lock=None, home=False):
        self.serial = serial.Serial()
        self.serial.timeout = timeout
        self.serial.baudrate = baudrate
        self.serial.stopbits = stopbits
        self.serial.port = com

        self.start_time = None
        self.end_time = None

        self.lock = lock
        if not lock:
            self.lock = threading.Lock()

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

    def _read_buffer(self):
        response = self.serial.readlines()
        if response:
            response = response[0].rsplit('\r'.encode())[0].decode()
        return response

    def check_status(self):
        logging.info('** LASER SYSTEM STATUS **\n')
        with self.lock:
            self.serial.write(self.commands['SYSTEM_STATUS']().encode())
            response = self._read_buffer()
        if response == 'ok':
            logging.info('\t System OK!')
            return

        response = '{:024b}'.format(int(response))

        is_not = 'not ' if response[23] == 1 else ''
        logging.info('\tThe coolant flow interlock is {}satisfied.'.format(is_not))

        is_not = '' if response[22] == 1 else 'not '
        logging.info('\tThe laser has {}overheated.'.format(is_not))

        is_not = 'not ' if response[21] == 1 else ''
        logging.info('\tThe external interlock is {}satisfied.'.format(is_not))

        is_not = 'not ' if response[20] == 1 else ''
        logging.info('\tThe workpiece interlock is {}satisfied.'.format(is_not))

        is_not = '' if response[19] == 1 else 'not '
        logging.info('\tThe laser power supply is {}enabled'.format(is_not))

        is_not = '' if response[18] == 1 else 'not '
        logging.info('\tThe laser is {}firing.'.format(is_not))

        is_not = '' if response[17] == 1 else 'not '
        logging.info('\tThe laser is {}in its startup state.'.format(is_not))

        is_not = '' if response[16] == 1 else 'not '
        logging.info('\tThe laser is {}in RS232 Mode'.format(is_not))

        is_not = '' if response[15] == 1 else 'not '
        logging.info('\tThe Q-Switch is {}set to external trigger mode.'.format(is_not))

        is_not = '' if response[14] == 1 else 'not '
        logging.info('\tThe flashlamp is {}set to external trigger mode.'.format(is_not))

        is_not = '' if response[13] == 1 else 'not '
        logging.info('\tThe laser is {}in single-shot mode.'.format(is_not))

        is_not = '' if response[12] == 1 else 'not '
        logging.info('\tThe laser is {}in continuous fire mode.'.format(is_not))

        is_not = '' if response[11] == 1 else 'not '
        logging.info('\tThe laser is {}in burst fire mode.'.format(is_not))

        is_not = 'not ' if response[10] == 1 else ''
        logging.info('\tThe Q-Switch is {}enabled.'.format(is_not))

        is_not = '' if response[9] == 1 else 'not '
        logging.info('\tThe laser is {}in fixed repetition rate mode.'.format(is_not))

        is_not = '' if response[8] == 1 else 'not '
        logging.info('\tThe laser is {}firing in warm-up mode.'.format(is_not))

        is_not = 'not' if response[7] == 1 else ''
        logging.info('\tThe closed loop control system can{} meet current energy target.'.format(is_not))

        # print('Unused Bit: {}'.format(response[6]))  # Bit at [6] is unused according to manufacturer documentation.

        is_not = '' if response[5] == 1 else 'not '
        logging.info('\tThe laser is {}initializing the position of one or more motor-driven accessories.'.format(is_not))

        is_not = '' if response[4] == 1 else 'not '
        logging.info('\tThe coolant level is {}low.'.format(is_not))

        is_not = 'An accessory motor' if response[3] == 1 else 'No accessory motor'
        logging.info('\t{} is moving.'.format(is_not))

        is_not = '' if response[2] == 1 else 'not '
        logging.info('\tThe laser is {}OK to start.'.format(is_not))

        is_not = '' if response[1] == 1 else 'not'
        logging.info('\tThe laser can{} be fired.'.format(is_not))

        is_not = '' if response[0] == 1 else 'not '
        logging.info('\tA reset fault has {}occurred.\n'.format(is_not))

    def check_parameters(self):
        with self.lock:
            logging.info('** LASER SETTINGS **\n')
            self.serial.write(self.commands['WAVELENGTH']('?').encode())
            response = self._read_buffer()
            logging.info('\tWavelength set to: {}'.format(response))

            self.serial.write(self.commands['ATTENUATION']('?').encode())
            response = self._read_buffer()
            logging.info('\tAttenuation set to: {}'.format(response))

            self.serial.write(self.commands['BURST_COUNT']('?').encode())
            response = self._read_buffer()
            logging.info('\tBurst Count set to: {}'.format(response))

            self.serial.write(self.commands['LASER_MODE']('?').encode())
            response = self._read_buffer()
            logging.info('\tLaser Mode set to: {}'.format(response))

            # self.serial.write(self.commands['PULSE_MODE']('?')) # fixme unrecognized command?
            # response = self._read_buffer()
            # print('\tPulse Mode set to: {}'.format(response))

            self.serial.write(self.commands['PFN_VOLTAGE']('?').encode())
            response = self._read_buffer()
            logging.info('\tPFN Voltage set to: {}'.format(response))

            self.serial.write(self.commands['ACCESSORY_CONFIGURATION']('?').encode())
            response = self._read_buffer()
            logging.info('\tConfiguration: {0:08b}\n'.format(int(response)))

    def set_pfn(self, value):
        try:
            int(value)
        except ValueError:
            logging.error('VE:Invalid PFN value provided - {}. Must be integer between 0 and {}'.format(value, self._safety_pfn_limit))
            return False

        if len(str(value)) != 3 or 0 > int(value) or int(value) > self._safety_pfn_limit:
            logging.info(len(str(value)) != 3)
            logging.info(0 > int(value))
            logging.info(int(value) > self._safety_pfn_limit)
            logging.error('VL:Invalid PFN value provided - {}. Must be integer between 0 and {}'.format(value, self._safety_pfn_limit))
            return False

        with self.lock:
            self.serial.write(self.commands['PFN_VOLTAGE'](value).encode())
            response = self._read_buffer()

        if response != 'ok':
            logging.warning('Failed to set PFN. Laser Response : {}'.format(response))
            return False
        else:
            logging.info('Successfully set PFN to {}'.format(value))
            return True

    def set_attenuation(self, value):
        try:
            int(value)
        except ValueError:
            logging.error('VE:Invalid Attenuation value provided - {}. Must be integer between 000 and 255'.format(value))
            return False

        if len(str(value)) != 3 or 0 > int(value) or int(value) > 255:
            logging.error('VL:Invalid Attenuation value provided - {}. Must be integer between 000 and 255'.format(value))
            return False

        with self.lock:
            self.serial.write(self.commands['ATTENUATION'](value).encode())
            response = self._read_buffer()

        if response != 'ok':
            logging.warning('Failed to set attenuation. Laser Response: {}'.format(response))
            return False
        else:
            logging.info('Successfully set attenuation to {}'.format(value))
            return True

    def set_burst(self, value):
        try:
            int(value)
        except ValueError:
            logging.error('Invalid Burst value provided - {}. Must be integer between 0001 and 4000'.format(value))
            return False

        if len(str(value)) != 3 or 1 > int(value) or int(value) > 4000:  # fixme (len)
            logging.error('Invalid Burst value provided - {}. Must be integer between 0001 and 4000'.format(value))
            return False

        with self.lock:
            self.serial.write(self.commands['BURST_COUNT'](value).encode())
            response = self._read_buffer()

        if response != 'ok':
            logging.warning('Failed to set burst count. Laser Response: {}'.format(response))
            return False
        else:
            logging.info('Successfully set burst count to {}'.format(value))
            return True

    def set_mode(self, value):
        try:
            int(value)
        except ValueError:
            logging.error('Invalid mode provided - {}. Must be either 0, 1 or 2'.format(value))
            return False

        if int(value) not in [0, 1, 2]:
            logging.error('Invalid mode provided - {}. Must be either 0, 1 or 2'.format(value))
            return False

        with self.lock:
            self.serial.write(self.commands['LASER_MODE'](value).encode())
            response = self._read_buffer()

        if response != 'ok':
            logging.warning('Failed to set mode. Laser Response: {}'.format(response))
            return False
        else:
            logging.info('Successfully set mode to {}'.format(value))
            return True

    def poll_status(self):
        # You must periodically (once every 2 seconds) send either LASER_STATUS or SYSTEM_STATUS command to poll the
        # laser status while it is enabled or it will shutdown automatically.
        with self.lock:
            self.serial.write(self.commands['LASER_STATUS']().encode())
            response = self._read_buffer()
        return response

    def set_parameters(self, pfn, attenuation, mode):
        parameter_set = self.set_pfn(pfn)
        if not parameter_set:
            return False

        parameter_set = self.set_attenuation(attenuation)
        if not parameter_set:
            return False

        parameter_set = self.set_mode(mode)
        if not parameter_set:
            return False

        return True                 

    def start(self):
        with self.lock:
            logging.warning('Starting laser system.')

            self.serial.write(self.commands['SERIAL_MODE']('?').encode())
            response = self._read_buffer()

            if response != 'ok':
                logging.info('Enabling serial mode for laser.')
                self.serial.write(self.commands['SERIAL_MODE']('1').encode())
                response = self._read_buffer()
                logging.info('Laser Response is {}'.format(response))

            self.serial.write(self.commands['SYSTEM_STATUS']().encode())
            response = self.serial.readlines()
            response = '{:024b}'.format(int(response[0].rsplit('\r'.encode())[0]))
            if response[0] == 1 or response[3] == 1 or response[4] == 1 or response[5] == 1 or response[7] == 1 or \
                response[8] == 1 or response[17] == 1 or response[18] == 1 or response[20] == 1 or response[21] == 1 or \
                    response[22] == 1 or response[23] == 1:
                logging.error('Check system status for problems. Laser Response: {}'.format(response))
                return False

            self.serial.write(self.commands['LASER_ON']().encode())
            logging.info('Laser on standby for 10 minutes.')
            return True

    def fire(self):
        with self.lock:
            self.serial.write(self.commands['FIRE']().encode())
            response = self._read_buffer()

        if response != 'ok':
            logging.warning('Laser failed to fire. Laser Response: {}'.format(response))
            bool_state = self.off()
            return bool_state

        logging.info('Laser fired.')
        return True

    def stop(self):
        logging.info('Stopping laser.')
        with self.lock:
            self.serial.write(self.commands['STOP_FIRING']().encode())
            response = self._read_buffer()

        if response != 'ok':
            logging.warning('Laser Response: {}'.format(response))
            logging.warning('Failed to stop laser firing.')
            bool_state = self.off()
            return bool_state

        logging.info('Laser firing stopped.')
        return True

    def off(self):
        with self.lock:
            logging.info('Turning off laser.')
            self.serial.write(self.commands['LASER_OFF']().encode())

            response = self._read_buffer()

            if response != 'ok':
                logging.fatal('Laser Response: {}'.format(response))
                logging.fatal('Failed to turn off laser. Manually shut down laser. (Turn the key)')
                return False

            logging.info('Laser turned off.')
            return True
