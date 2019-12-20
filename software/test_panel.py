# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 15:08:06 2019

@author: 61473
"""

from serial import Serial
from TLC5955 import SCPIProtocol, SCPIException, TLC5955
import numpy as np

PORTNAME = 'COM3'

# Open settings file and close it at the end of the with block
with np.load('panel_settings.npz', allow_pickle=True) as settings:
    maxcurrent = settings['maxcurrent']
    brightness = settings['brightness']
    dotcorrect = settings['dotcorrect']
    #settings['mode'] is a 0D array containing a dict of options for mode_code. use [()] to get the dict
    mode = settings['mode'][()]

print(dotcorrect[...,0])

mode = TLC5955.mode_code(**mode) #unpack the dict and give it to mode_code as arguments
maxcurrent = [TLC5955.maxcurrent_code(mc) for mc in maxcurrent]
brightness = [int(TLC5955.brightness_code(bc)) for bc in brightness]
dotcorrect = TLC5955.dotcorrect_code(dotcorrect)

# Connect to panel and set the settings
with Serial(PORTNAME) as port:
    with SCPIProtocol(port) as scpi:
        #first thing, turn off echo because it's annoying
        try:
            resp = scpi.command(b'syst:comm:echo off', True, timeout=1)
        except SCPIException:
            pass
        
        scpi.command('disp:spif 3000000',True)
        scpi.command('disp:mode {}'.format(mode))
        scpi.command('disp:maxc {}'.format(','.join('{}'.format(mc) for mc in maxcurrent)))
        scpi.command('disp:bri {}'.format(','.join('{}'.format(bc) for bc in brightness)))
        scpi.command(b'disp:dotc:all ' + scpi.format_bytes(dotcorrect.tobytes()))
        
        img = np.zeros((8,12,5))
        
       
        
        
        #select random pixels:
        #img[np.random.uniform(size=(8,12)) < 0.25]
        #img[...,:3] = np.random.uniform(0.0, 0.75, (12,8,3))
        #img[...,3:] = np.random.uniform(0.0,0.001,(8,12,2))
        
        #all grey
        
        img[ : ,: , 0] = 1
        #img[ : , : , 1] = 1
        #img[ : , : , 2] = 1
        #img[ : , : , 3] = 0.2
        #img[ : , : , 4] = 0.25
        
        #Blue training 
      
        #img[1:2,7:8,0] = 0.024
        #img[1:2,7:8,1] = 0.026
        #img[1:2,7:8,2] = 0.95
        #img[1:2,7:8,3] = 0.00011
        #img[1:2,7:8,4] = 0.000079
    
        #img[1:2,1:2,0] = 0.024
        #img[1:2,1:2,1] = 0.026
        #img[1:2,1:2,2] = 0.95
        #img[1:2,1:2,3] = 0.00011
        #img[1:2,1:2,4] = 0.000079
        
        #img[1:2,5:6,0] = 0.024
        #img[1:2,5:6,1] = 0.026
        #img[1:2,5:6,2] = 0.95
        #img[1:2,5:6,3] = 0.00011
        #img[1:2,5:6,4] = 0.000079
        
        #img[3:4,4:5,0] = 0.024
        #img[3:4,4:5,1] = 0.026
        #img[3:4,4:5,2] = 0.95
        #img[3:4,4:5,3] = 0.00011
        #img[3:4,4:5,4] = 0.000079
        
        #img[5:6,3:4,0] = 0.024
        #img[5:6,3:4,1] = 0.026
        #img[5:6,3:4,2] = 0.95
        #img[5:6,3:4,3] = 0.00011
        #img[5:6,3:4,4] = 0.000079
    
       # UV training
        
        #img[1:2,7:8,0] = 0.7
        #img[1:2,7:8,1] = 0.75
        #img[1:2,7:8,2] = 0.3
        #img[1:2,7:8,3] = 0.0033
        #img[1:2,7:8,4] = 0.011
        
        #img[1:2,1:2,0] = 0.7
        #img[1:2,1:2,1] = 0.75
        #img[1:2,1:2,2] = 0.3
        #img[1:2,1:2,3] = 0.0033
        #img[1:2,1:2,4] = 0.011
    
        #img[1:2,5:6,0] = 0.7
        #img[1:2,5:6,1] = 0.75
        #img[1:2,5:6,2] = 0.3
        #img[1:2,5:6,3] = 0.0033
        #img[1:2,5:6,4] = 0.011
        
        #img[3:4,4:5,0] = 0.7
        #img[3:4,4:5,1] = 0.75
        #img[3:4,4:5,2] = 0.3
        #img[3:4,4:5,3] = 0.0033
        #img[3:4,4:5,4] = 0.5
        
        #img[5:6,3:4,0] = 0.7
        #img[5:6,3:4,1] = 0.75
        #img[5:6,3:4,2] = 0.3
        #img[5:6,3:4,3] = 0.0033
        #img[5:6,3:4,4] = 0.011
        
        
        img = TLC5955.pwm_code(img)
        scpi.command(b'disp:pwm:all ' + scpi.format_bytes(img.tobytes()))
        
        scpi.command(b'display on')
        
        #from numpy import load
        #data=load('panel_settings.npz')
        #lst = data.files
        #for item in lst:
            #print(item)
            #print(data[item])