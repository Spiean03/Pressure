# -*- coding: utf-8 -*-
"""
Created on Wed Aug 28, 2013
"Instrument"-like implementation of a client to talk to the Fridgemonitor program
@author: Ben

"""
import Tool
from fridgemonitor import data_server
from collections import OrderedDict

param = OrderedDict([('LS1','ohms'), ('LS2', 'ohms'),( 'LS3','ohms'), ('LS4', 'ohms'), 
         ('LS5','ohms'), ('LS9','ohms'), ('CMN', 'mK')])
         
class Instrument(Tool.MeasInstr):  
        
    def __init__(self, resource_name, debug=False): 
        super(Instrument, self).__init__(resource_name,'FridgeClient',debug)   

    def __del__(self):
        super(Instrument, self).__del__()      


    #overload the connect() method so that no real connection is made 
    # a client socket is generated and destroyed for each request in measure()
    def connect(self, resource_name = None):
        pass
        

    def measure(self,channel='LS1'):
        if self.last_measure.has_key(channel):
            answer = data_server.get_fridge_data(str(channel))
        else:
            print "you are trying to measure a non existent channel : " +channel
            print "existing channels :", self.channels
            answer=None
        self.last_measure[channel]=answer
        return answer
    