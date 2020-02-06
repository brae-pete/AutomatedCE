
import DAQControl

class PowerSupply:
    """
    Basic powersupply class. Set electrode voltage will change the set value. To
    have the DAC output that voltage, self.apply_changes() needs to be called.

    >>> ps = PowerSupply(channels=[1,2,3])
    >>> ps.set_electrode_voltage(1,2.3) # Set electrode 1 to 2.3 kV
    >>> ps.apply_changes()
    >>> ps.stop_voltage()
    """

    def __init__(self, channels=[1,2,3], dac=None):
        if dac is None:
            self.dac = DAQControl.DAC()
        self.channels=channels

    def set_electrode_voltage(self, chnl, voltage):
        voltage = self.conversion(voltage)
        self.dac.set_voltage(chnl, voltage)

    def apply_changes(self):
        self.dac.load_changes()

    def stop_voltage(self):
        for i in self.channels:
            self.set_electrode_voltage(i,0)
        self.dac.load_changes()

    @staticmethod
    def conversion(voltage):
        return voltage


class BertanSupply(PowerSupply):
    """
    PowerSupply Class specific for the microchip CE Setup using a PMOD DAC and
    Bertan Power Supply. Please enter voltages in kiloVolts (1 for 1kV)

    """
    def __init__(self, channels=None):
        if channels is None:
            channels = [1, 2, 3, 4]
        self.dac=DAQControl.PMOD_DAC(channels=channels)
        self.channels=channels

    @staticmethod
    def conversion(voltage):
        return voltage/5*2.5

class SpellmanSupply(PowerSupply):
    """
    PowerSupply Class specific for the CE system using the Spellman power supply and
    a national instruments DAC. Please enter voltages in kiloVolts (1 for 1kV).
    """

    def __init__(self, channels=None):
        if channels is None:
            channels = ['ao0', 'ao1']
        self.dac = DAQControl.NI_DAC(channels=channels)
        self.channels=channels

    @staticmethod
    def conversion(voltage):
        return voltage/30*10