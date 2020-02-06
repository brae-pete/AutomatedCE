import threading
import logging
import time
try:
    from hardware import ArduinoBase
except ModuleNotFoundError:
    import ArduinoBase

class LED:
    """
    Controls the LED next to the capillary used for brightfield images
    Assumes a RGB LED, but if only a single LED is present, (single white LED for example),
    use the R channel as it is assumed to be the default channel


    """

    channel_states = {'R': True, 'G': False, 'B': False}
    dance_stop = threading.Event()


    def open(self):
        """User initializes whatever resources are required
         (open ports, create MMC + load config, etc...)
         """
        return

    def reset(self):
        """Resets the resources for the stage"""
        self.close()
        self.open()

    def close(self):
        """Closes the resources for the stage"""
        for chnl in 'RGB':
            self.stop_led(chnl)
        return

    def start_led(self, channel='R'):
        """
        Turns on the specified LED channel
        :param channel: 'R', 'G', or 'B' char.
        :return:
        """
        self.channel_states[channel] = True

    def stop_led(self, channel='G'):
        """
        Turns off the specified LED
        :param channel: 'R', 'G', or 'B' char
        :return:
        """
        self.channel_states[channel] = False

    def dance_party(self):
        """
        Just for fun lets change the light colors
        :return:
        """
        channels = ['R', 'G', 'B']
        i = 2
        self.dance_stop.clear()
        while not self.dance_stop.is_set():
            time.sleep(0.5)
            self.start_led(channels[i % 3])
            time.sleep(0.5)
            self.stop_led(channels[(i - 1) % 3])
            i += 1
        for chnl in channels:
            self.stop_led(chnl)

class CapillaryLED(LED):
    """
    Controls the LED next to the capillary used for brightfield images
    Assumes a RGB LED, but if only a single LED is present, (single white LED for example),
    use the R channel as it is assumed to be the default channel


    """

    channel_states = {'R':True, 'G':False, 'B':False}
    dance_stop = threading.Event()

    def __init__(self, com="COM9", arduino = -1, lock=threading.Lock(), home= True):
        self.home = home
        self.com = com
        self.have_arduino = True
        self.arduino = arduino
        self.lock = lock

        if arduino == -1:
            self.check = False
            self.arduino = ArduinoBase.ArduinoBase(self.com, self.home)

    def open(self):
        """User initializes whatever resources are required
         (open ports, create MMC + load config, etc...)
         """
        self.arduino.open()

    def close(self):
        """Closes the resources for the stage"""
        if self.home:
            return
        for chnl in 'RGB':
            self.stop_led(chnl)

        self.arduino.close()

    def start_led(self, channel='R'):
        """

        :param channel: 'R', 'G', or 'B' char.
        :return:
        """
        with self.lock:
            self.arduino.serial.write('L{}1\n'.format(channel).encode())
        self.channel_states[channel]=True

    def stop_led(self, channel = 'G'):

        """
        :param channel: 'R', 'G', or 'B' char
        :return:
        """
        with self.lock:
            self.arduino.serial.write('L{}0\n'.format(channel).encode())
        self.channel_states[channel]=False

if __name__ == "__main__":
    led = CapillaryLED(com="COM7", home = False)
    led.dance_party()