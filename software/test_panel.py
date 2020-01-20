# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 15:08:06 2019

@author: 61473
"""

from serial import Serial
from TLC5955 import SCPIProtocol, SCPIException, TLC5955
import numpy as np
from time import sleep

import matplotlib as mpl
mpl.use('Qt5Agg') #draw figures in a window
import matplotlib.pyplot as plt
plt.ioff() #do not use "interactive mode" -- ie. plt.show() waits until figures are closed

PORTNAME = 'COM8'

mode = {'dsprpt':True, 'espwm':True}
maxcurrent = np.array([8, 8, 3.2, 15.9])
brightness = np.array([0.42, 0.58, 0.5, 0.81])
dotcorrect = np.ones((8,12,5))
mode = TLC5955.mode_code(**mode) #unpack the dict and give it to mode_code as arguments
mcs = [TLC5955.maxcurrent_code(mc) for mc in maxcurrent]
bcs = [int(TLC5955.brightness_code(bc)) for bc in brightness]
dcs = TLC5955.dotcorrect_code(dotcorrect)

img = np.zeros((8,12,5))
img[...,1] = 1

def img_current(img, currents):
    """ img is (...,5), currents is (4,)"""
    currents = np.concatenate((currents,[currents[-1]]))
    return np.sum(img*currents)

#convert to the panel's data format
img = TLC5955.pwm_code(img)

# Connect to panel and set the settings
with Serial(PORTNAME) as port:
    with SCPIProtocol(port) as scpi:
        #first thing, turn off echo because it's annoying
        try:
            resp = scpi.command(b'syst:comm:echo off', True, timeout=1)
        except SCPIException:
            pass
        
        scpi.command('disp:mode {}'.format(mode))
        scpi.command('disp:maxc {}'.format(','.join('{}'.format(mc) for mc in mcs)))
        scpi.command('disp:bri {}'.format(','.join('{}'.format(bc) for bc in bcs)))
        scpi.command(b'disp:dotc:all ' + scpi.format_bytes(dcs.tobytes()))
        scpi.command('disp:spif 30000',True)
        #load the max current, mode, brightness, and dotcorrect
        #scpi.command('disp:load')
        scpi.command(b'disp:pwm:all ' + scpi.format_bytes(img.tobytes()))
        
        #turn on the display
        scpi.command(b'display on')
        sleep(5)
        
        scpi.command('disp off')
        #turn off the display when the figure is closed
        #scpi.command(b'display off')
        
'''
for y in range(8):
            for x in range(12):
                for c in range(3):
                    cmd = 'disp:pwm {}, {}, {}, 65535'.format(y,x,c)
                    print(cmd)
                    scpi.command(cmd)
                    scpi.command('disp:refresh')
                    sleep(0.01)
                    '''