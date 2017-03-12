import serial as _s
import time
import sys

class Nextorr():

    def __init__(self, port=None):
        print "Now initializing"
        try:
            print "Trying hard"
            if port is None:
                self._serial = _s.Serial(port = 'COM6', baudrate = 19200, parity = _s.PARITY_NONE, stopbits = _s.STOPBITS_ONE, bitesize = _s.EIGHTBITS, timeout =0.1)
                print self._serial.name
            else:
                print "tried, could not connect"
        except:
            self._serial.close()
            raise RuntimeError('Could not open serial connection')

        if self._serial is None:
            raise RuntimeError('Could not open serial connection')
            print "did not work"
        print('NexTorr Controller initialized on port %s' %self._serial.name)
        self._serial.write('V\r')
        print('Firmware Version: ' + self._serial.readline())
        self._serial.write('TS\r')
        print('Status: ' + self._serial.readline())
        
        

    def _pressure(self):
        transmission = 'Tb\r'
        
            # TB = expression in mbar
            # Tb = expression in mbar (only value)
            # TT = expression in Torr
            # Tt = expression in Torr (only value)
            # TP = expression in Pa
            # Tp = expression in Pa (only value)
        
        self.pressure = self._serial.write(transmission)
        print self.pressure
        
    def _currentreadout(self):
        # sends a report of the Output IP current, e.g. "Current 52.1 uA"
        transmission = 'TI\r'
        self._serial.write(transmission)
        self.current = self._serial.readline()
        print self.current
        
        


