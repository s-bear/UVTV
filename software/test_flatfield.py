# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 15:08:06 2019

@author: 61473
"""

from serial import Serial
from TLC5955 import SCPIProtocol, SCPIException, TLC5955
import numpy as np

PORTNAME = 'COM4'

mode = {'dsprpt':True, 'espwm':True}
maxcurrent = np.array([8, 8, 3.2, 15.9])
brightness = np.array([0.42, 0.58, 0.5, 0.81])

means = np.load('mean_flatfield_brightness.npz')
red_means = means['red']

flat_field = np.ones((8, 12, 5))
flat_field[..., 0] = red_means
dotcorrect = np.nanmin(flat_field, (0,1))/flat_field


mode = TLC5955.mode_code(**mode) #unpack the dict and give it to mode_code as arguments
maxcurrent = [TLC5955.maxcurrent_code(mc) for mc in maxcurrent]
brightness = [int(TLC5955.brightness_code(bc)) for bc in brightness]
dotcorrect = TLC5955.dotcorrect_code(dotcorrect)

# Connect to panel and set the settings
port = Serial(PORTNAME)
scpi = SCPIProtocol(port)
scpi.start()

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

#red only        
img = np.zeros((8,12,5))
img[0,0,0] = 1

img = TLC5955.pwm_code(img)
scpi.command(b'disp:pwm:all ' + scpi.format_bytes(img.tobytes()))

scpi.command(b'display on')
