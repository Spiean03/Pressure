# -*- coding: utf-8 -*-

import time
try:
    import serial
except:
    pass
import Tool
import random
from numpy import power
#!/usr/bin/env python  
#import string, os, sys, time  
#import io
param={'P1':'mbar','P3':'mbar','P5':'mbar','P6':'mbar'}

class Instrument(Tool.MeasInstr):  
    def __init__(self, port=u'ASRL4::INSTR', debug=False,**keyw):  
        super(Instrument, self).__init__("COM4",'MKS937B',debug,communication_protocole="serial",baud_rate=9600,term_chars="\r\n",timeout=2,bytesize=8, parity ='N', stopbits=1, xonxoff=False, dsrdtr=False,**keyw)       
        
        self.debug = debug
#        self.ID_name='MKS_gauge'
        if not self.debug:
         

            self.channels=[]
            self.units=[]
            for p,unit in param.items():
                self.channels.append(p)
                self.units.append(unit)
        
            #initializes the first measured value to 0 and the channels' names 
            for chan in self.channels:
                self.last_measure[chan]=0
                self.channels_names[chan]=chan

    def measure(self,channel):
        print "youhou",channel
        if self.last_measure.has_key(channel):
            if not self.debug: 
                answer=self.get_pressure(channel)
            else:
                print "the channel " +channel
                answer=random.random()
            self.last_measure[channel]=answer
        else:
            print "you are trying to measure a non existent channel : " +channel
            print "existing channels :", self.channels
            answer=None
        return answer  
  
    def get_pressure(self, chan):
        #take the number in front the 'P' for the channel number
        chan=int(chan[1])
       
        if not self.debug:
            print("inside get pres",chan)
            answer=self.askert("Pr%i?"%(chan))
            print answer
            if answer=="ACKNOGAUGE":
                answer=-1
            elif answer[0:6]=="ACKLO<":
                answer=power(10,float(answer[-3:]))
            else:
                answer=float(answer[3:])#ACK5.30E-08
        else:
            answer=random.random()
        print answer
        return answer
            
    def askert(self, stri):
        print "yaya"
        if not self.debug: 
            stri="@253"+stri+";FF"
            print stri
            #overload the parent class ask method to add the instrument name
            answer=super(Instrument,self).ask(stri)
            print answer[0:3],answer[-3:]
            if answer[0:4]=="@253":
                answer=answer[4:]
#                print answer
            else :
#                print answer
                print "MSK937B : error in return value, it doesn't start with @253"
                
            if answer[-3:]==";FF":
                answer=answer[:-3]
#                print answer
            else :
#                print answer
                print "MSK937B : error in return value, it doesn't finish with ;FF"
                
        else:
        
            print("MKS973B debug ask command : %s"%(stri))
        
        return answer

    

#    def readline(self):
#        if not self.debug:     
#            return self.readline()
    
#    def read2(self):
#         if not self.debug:     
#             sio = self.
#             time.sleep(0.1)
#             out=''  
#             while sio.inWaiting() > 0:
#                 out += sio.read(1)
#             return (out)

    #initialization should open it already    
#    def reopen(self):
#         if not self.debug:
#             self.connexion.open()
        
#    def close(self):  
#         if not self.debug:
#             self.sio.close() 

if (__name__ == '__main__'):  
    
    
#    for j in range(15):
#        i=Instrument("COM%i"%(j))

        
    i=Instrument("COM%i"%(2))
    print i
    
    
    for c in param:
        print i.measure(c)
    i.close()
