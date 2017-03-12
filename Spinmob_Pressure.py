#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
from spinmob import egg
import serial as _s
import pyqtgraph.examples
import time
import tweepy
import datetime
import pigpio
import DHT22
degree = str('\xb0'.decode('latin-1').encode('utf-8'))
import numpy as _np


#enter the corresponding information from your Twitter application:
CONSUMER_KEY = 'Z0I3rTSi5CcDwuNCbSYgqhQ7o'#keep the quotes, replace this with your consumer key
CONSUMER_SECRET = 'MmN8hpT7HK95OqFSyNpfwJD3kx7QrUQYFlIi5KdCy9jOB6T2u3'#keep the quotes, replace this with your consumer secret key
ACCESS_KEY = '4242707233-9sC2HkWKFZobdQDqyil4t8en3UYFGwceDNX6EOS'#keep the quotes, replace this with your access token
ACCESS_SECRET = 'eLkFMZam9Kp2tF6N3METpzLgq4KFB9gb1k8SHrUvZQ0Wu'#keep the quotes, replace this with your access token secret
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)


class MKS():  
    
    def __init__(self, port=None):
        print "Now initializing"
        try:
            print "Trying hard"
            if port is None:
                print 'here1'
                self._serial = _s.Serial(port = 'COM8', baudrate = 9600,bytesize=_s.EIGHTBITS, parity = _s.PARITY_NONE, xonxoff = False, stopbits = _s.STOPBITS_ONE, timeout = 0.1)
                print 'here2'                
                print self._serial.name
            else:
                print "tried, could not connect"
        except:
            self._serial.close()
            raise RuntimeError('Could not open serial connection')

        if self._serial is None:
            raise RuntimeError('Could not open serial connection')
            print "did not work"
        print("initialized")
#        print('NexTorr Controller initialized on port %s' %self._serial.name)
#        self._serial.write('V\r')
#        print('Firmware Version: ' + self._serial.readline())
#        self._serial.write('TS\r')
#        print('Status: ' + self._serial.readline())    


    def measure(self):
        stri="@253"+"PRZ?"+";FF\r\n"
        self.pressure = self._serial.write(stri)
        pressure = self._serial.readline()
        print pressure # This normally gives a return in the form of @253ACK2.10E-09 NOGAUGE 4.50E-07 NOGAUGE LO<E-03 LO<E-03;FF
        pressure = pressure.replace("@253ACK","") # remove it from the string
        pressure = pressure.replace(";FF","") # remove it from the string
        self.pressure = pressure.split(" ")
        print self.pressure #where self.pressure[0], [2] are the pressures of the ion gauges and self.pressure[4] and [5] are the ones from the Pirani
        if self.pressure[4] == "LO<E-03":
            try:
                self.pressure_main = float(self.pressure[0])
            except (RuntimeError,TypeError,NameError,ValueError): 
                self.pressure_main = -1.0
                print "Can't read out the pressure of the Main Chamber"
        else:
            try:
                self.pressure_main = float(self.pressure[4])
            except (RuntimeError,TypeError,NameError,ValueError):
                self.pressure_main = -1.1
                print "Can't read out the pressure of the Main Chamber"
        if self.pressure[5] == "LO<E-03":
            try:
                self.pressure_loadlock = float(self.pressure[2])
            except (RuntimeError,TypeError,NameError,ValueError): 
                self.pressure_loadlock = -2.0
                print "Can't read out the pressure of the Load Lock"
        else:
            try:
                self.pressure_loadlock = float(self.pressure[5])
            except (RuntimeError,TypeError,NameError,ValueError): 
                self.pressure_loadlock = -2.2
                print "Can't read out the pressure of the Load Lock"
        w.process_events()
        
        

        

class sensor:
   """
   A class to read relative humidity and temperature from the
   DHT22 sensor.  The sensor is also known as the AM2302.

   The sensor can be powered from the Pi 3V3 or the Pi 5V rail.

   Powering from the 3V3 rail is simpler and safer.  You may need
   to power from 5V if the sensor is connected via a long cable.

   For 3V3 operation connect pin 1 to 3V3 and pin 4 to ground.

   Connect pin 2 to a gpio.

   For 5V operation connect pin 1 to 5V and pin 4 to ground.

   The following pin 2 connection works for me.  Use at YOUR OWN RISK.

   5V--5K_resistor--+--10K_resistor--Ground
                    |
   DHT22 pin 2 -----+
                    |
   gpio ------------+
   """

   def __init__(self, pi, gpio, LED=None, power=None):
      """
      Instantiate with the Pi and gpio to which the DHT22 output
      pin is connected.

      Optionally a LED may be specified.  This will be blinked for
      each successful reading.

      Optionally a gpio used to power the sensor may be specified.
      This gpio will be set high to power the sensor.  If the sensor
      locks it will be power cycled to restart the readings.

      Taking readings more often than about once every two seconds will
      eventually cause the DHT22 to hang.  A 3 second interval seems OK.
      """
      
      self.pi = pi
      self.gpio = gpio
      self.LED = LED
      self.power = power

      if power is not None:
         pi.write(power, 1) # Switch sensor on.
         time.sleep(2)

      self.powered = True

      self.cb = None

      atexit.register(self.cancel)

      self.bad_CS = 0 # Bad checksum count.
      self.bad_SM = 0 # Short message count.
      self.bad_MM = 0 # Missing message count.
      self.bad_SR = 0 # Sensor reset count.

      # Power cycle if timeout > MAX_TIMEOUTS.
      self.no_response = 0
      self.MAX_NO_RESPONSE = 2

      self.rhum = -999
      self.temp = -999

      self.tov = None

      self.high_tick = 0
      self.bit = 40

      pi.set_pull_up_down(gpio, pigpio.PUD_OFF)

      pi.set_watchdog(gpio, 0) # Kill any watchdogs.

      self.cb = pi.callback(gpio, pigpio.EITHER_EDGE, self._cb)

   def _cb(self, gpio, level, tick):
      """
      Accumulate the 40 data bits.  Format into 5 bytes, humidity high,
      humidity low, temperature high, temperature low, checksum.
      """
      diff = pigpio.tickDiff(self.high_tick, tick)

      if level == 0:

         # Edge length determines if bit is 1 or 0.

         if diff >= 50:
            val = 1
            if diff >= 200: # Bad bit?
               self.CS = 256 # Force bad checksum.
         else:
            val = 0

         if self.bit >= 40: # Message complete.
            self.bit = 40

         elif self.bit >= 32: # In checksum byte.
            self.CS  = (self.CS<<1)  + val

            if self.bit == 39:

               # 40th bit received.

               self.pi.set_watchdog(self.gpio, 0)

               self.no_response = 0

               total = self.hH + self.hL + self.tH + self.tL

               if (total & 255) == self.CS: # Is checksum ok?

                  self.rhum = ((self.hH<<8) + self.hL) * 0.1

                  if self.tH & 128: # Negative temperature.
                     mult = -0.1
                     self.tH = self.tH & 127
                  else:
                     mult = 0.1

                  self.temp = ((self.tH<<8) + self.tL) * mult

                  self.tov = time.time()

                  if self.LED is not None:
                     self.pi.write(self.LED, 0)

               else:

                  self.bad_CS += 1

         elif self.bit >=24: # in temp low byte
            self.tL = (self.tL<<1) + val

         elif self.bit >=16: # in temp high byte
            self.tH = (self.tH<<1) + val

         elif self.bit >= 8: # in humidity low byte
            self.hL = (self.hL<<1) + val

         elif self.bit >= 0: # in humidity high byte
            self.hH = (self.hH<<1) + val

         else:               # header bits
            pass

         self.bit += 1

      elif level == 1:
         self.high_tick = tick
         if diff > 250000:
            self.bit = -2
            self.hH = 0
            self.hL = 0
            self.tH = 0
            self.tL = 0
            self.CS = 0

      else: # level == pigpio.TIMEOUT:
         self.pi.set_watchdog(self.gpio, 0)
         if self.bit < 8:       # Too few data bits received.
            self.bad_MM += 1    # Bump missing message count.
            self.no_response += 1
            if self.no_response > self.MAX_NO_RESPONSE:
               self.no_response = 0
               self.bad_SR += 1 # Bump sensor reset count.
               if self.power is not None:
                  self.powered = False
                  self.pi.write(self.power, 0)
                  time.sleep(2)
                  self.pi.write(self.power, 1)
                  time.sleep(2)
                  self.powered = True
         elif self.bit < 39:    # Short message receieved.
            self.bad_SM += 1    # Bump short message count.
            self.no_response = 0

         else:                  # Full message received.
            self.no_response = 0

   def temperature(self):
      """Return current temperature."""
      return self.temp

   def humidity(self):
      """Return current relative humidity."""
      return self.rhum

   def staleness(self):
      """Return time since measurement made."""
      if self.tov is not None:
         return time.time() - self.tov
      else:
         return -999

   def bad_checksum(self):
      """Return count of messages received with bad checksums."""
      return self.bad_CS

   def short_message(self):
      """Return count of short messages."""
      return self.bad_SM

   def missing_message(self):
      """Return count of missing messages."""
      return self.bad_MM

   def sensor_resets(self):
      """Return count of power cycles because of sensor hangs."""
      return self.bad_SR

   def trigger(self):
      """Trigger a new relative humidity and temperature reading."""
      if self.powered:
         if self.LED is not None:
            self.pi.write(self.LED, 1)

         self.pi.write(self.gpio, pigpio.LOW)
         time.sleep(0.017) # 17 ms
         self.pi.set_mode(self.gpio, pigpio.INPUT)
         self.pi.set_watchdog(self.gpio, 200)

   def cancel(self):
      """Cancel the DHT22 sensor."""

      self.pi.set_watchdog(self.gpio, 0)

      if self.cb != None:
         self.cb.cancel()
         self.cb = None
    
        

_m = MKS()


## HERE STARTS THE SPINMOB GUI            

# Create the window and two tab areas
w = egg.gui.Window("Pressure and Temperature Recording", autosettings_path = 'w.cfg')
tabs1 = w.place_object(egg.gui.TabArea(autosettings_path='tabs1.cfg'))
tabs2 = w.place_object(egg.gui.TabArea(autosettings_path='tabs2.cfg'), alignment=0)


# add some tabs
t_setup  = tabs1.add_tab("Setup")
t_connect = tabs1.add_tab("Connect")
t_plot       = tabs2.add_tab("Overview")
t_pressure = tabs2.add_tab("Pressure")
t_temperature = tabs2.add_tab("Temperature&Humity")



# load previous settings (i.e. the active tab) if present
tabs1.load_gui_settings()
tabs2.load_gui_settings()


# Setup tab
settings = t_setup.place_object(egg.gui.TreeDictionary('settings.cfg'))
settings.add_parameter('Recording/TimeInterval', 5, type='float', step=5, limits=[1,1e5], suffix='s', siPrefix=True)
settings.add_parameter('Recording/TwitterUpdate', 900, type= 'float', step = 60, suffix= 's',siPrefix=True)

# Connect tab
button_pressure = t_connect.place_object(egg.gui.Button("Pressure").set_checkable(True))
button_temperature = t_connect.place_object(egg.gui.Button("Temperature").set_checkable(True))
button_twitter = t_connect.place_object(egg.gui.Button("Twitter").set_checkable(True))
t_connect.new_autorow()
button_start = t_connect.place_object(egg.gui.Button("Start").set_checkable(True))



# Plot tab
plotbox = t_plot.place_object(egg.gui.DataboxPlot('*.txt', 'd_raw.cfg'), alignment = 0)
temperaturebox = t_temperature.place_object(egg.gui.DataboxPlot('*.txt', 'd_temp.cfg'), alignment = 0)
pressurebox = t_pressure.place_object(egg.gui.DataboxPlot('*.txt', 'd_press.cfg'), alignment = 0)





def button_start_pressed(*a):   
    deltatime = 0
    time_start = datetime.datetime.now()
    twittertime = 0
    open("temporarystorage.txt", 'w')
    with open("temporarystorage.txt",'a') as f:   
        f.write("Time\tMain\tLL\tTemp\tHum\n")

    if button_temperature.is_checked():
        # this needs to be done before we enter the while loop
        pi = pigpio.pi('169.254.165.63')
        s = DHT22.sensor(pi, 4, LED=16, power=8)
        s.trigger()
        time.sleep(3)
        
    while button_start.is_checked():
        plotbox.clear()

        if button_pressure.is_checked():
            pressurebox.clear()
            _m.measure()
            
            #y_pressuremain.append(_m.pressure_main)
            #y_pressureloadlock.append(_m.pressure_loadlock)
            
            
            
            #plotbox['main'] = y_pressuremain
            #plotbox['loadlock'] = y_pressureloadlock
            
            _data = str("%s\t%s\t%s\t" %(deltatime,_m.pressure_main,_m.pressure_loadlock))
            
        else:
            _data = str("%s\t-99\t-99\t" %(deltatime))
            
        if button_temperature.is_checked():
            temperaturebox.clear()
            s.trigger()
            try:
                humidity = round(float(s.humidity()),1)
                
            except (RuntimeError,TypeError,NameError,ValueError):
                humidity = -1.0
            
            try:
                temperature = round(float(s.temperature()),1)
            except (RuntimeError,TypeError,NameError,ValueError):
                temperature = 999.0
            
            #y_temperature.append(temperature)
            #y_humidity.append(humidity)
                
                
            #plotbox['temperature'] = y_temperature
            #plotbox['humidity'] = y_humidity
            
            print "Temperature = %s degC, Humidity = %s %%" %(temperature, humidity)
            
            _data = _data + str("%s\t%s\n" %(temperature, humidity))
        else:
            _data = _data + str("-99\t-99\n")
        
        with open("temporarystorage.txt",'a') as f:   
            f.write(_data)

            
        if button_twitter.is_checked():
            
            if twittertime == 0:
                now = datetime.datetime.now()
                tima = now.strftime("%H:%M")
                date = now.strftime("%x")
                message = str("UHV Chamber Update on %s as of %s." %(tima,date))
                try:
                    if button_temperature.is_checked():
                        message = message + str(" T: %s" %(temperature)) 
                        message = message + degree 
                        message = message+ str("C, H= %s%%." %(humidity))
                        print amessage
                    if button_pressure.is_checked():
                        message = message + str(" Main: %smbar, LL: %smbar."  %(temperature, humidity))
                        print message
                        
                    api.update_status(message)
                except (RuntimeError,TypeError,NameError,ValueError):
                    print "Could not send tweet."
                twittertime = 0
                twittertime = twittertime + settings['Recording/TimeInterval']
            elif twittertime >= settings['Recording/TwitterUpdate']:
                twittertime = 0
            else:
                twittertime = twittertime + settings['Recording/TimeInterval']

        
        #x_time.append(deltatime)
        #plotbox['time'] = x_time

        plotbox['time'], plotbox['main'], plotbox['loadlock'], plotbox['temperature'], plotbox['humidity'] = _np.loadtxt("temporarystorage.txt", skiprows = 1, delimiter='\t', unpack=True)        

        time_passed = datetime.datetime.now()
        seconds = time_passed - time_start
        
        deltatime = (time_passed - time_start).seconds 
        
        if tabs2.get_current_tab() == 1:
            pressurebox.clear()
            pressurebox['time'] = plotbox['time']
            pressurebox['main'] = plotbox['main']
            pressurebox['loadlock'] = plotbox['loadlock']
            pressurebox.plot()
        elif tabs2.get_current_tab() == 2:
            temperaturebox.clear()
            temperaturebox['time'] = plotbox['time']
            temperaturebox['temperature'] = plotbox['temperature']
            temperaturebox['humidity'] = plotbox['humidity']
            temperaturebox.plot()
        else:
            plotbox.plot()
            
        for i in range(0, settings['Recording/TimeInterval']):
            for i in range(0,2):
                if tabs2.get_current_tab() == 1:
                    pressurebox.clear()
                    pressurebox['time'] = plotbox['time']
                    pressurebox['main'] = plotbox['main']
                    pressurebox['loadlock'] = plotbox['loadlock']
                    pressurebox.plot()
                elif tabs2.get_current_tab() == 2:
                    temperaturebox.clear()
                    temperaturebox['time'] = plotbox['time']
                    temperaturebox['temperature'] = plotbox['temperature']
                    temperaturebox['humidity'] = plotbox['humidity']
                    temperaturebox.plot()
                else:
                    plotbox.plot()
                w.process_events()
                time.sleep(0.4)

    s.cancel()
    pi.stop()



#Pressure.set_checkable(True)     
#w.connect(Pressure.signal_clicked, pressure)



w.connect(button_start.signal_clicked, button_start_pressed)



#databox_pressure = egg.gui.DataboxLoadSave()
#databox_pressure.enable_save()
#t_plot.place_object(databox_pressure)
#t_plot.new_autorow()


w.show()