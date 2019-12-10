# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 15:08:06 2019

@author: 61473
"""

from serial import Serial
from TLC5955 import SCPIProtocol, SCPIException, TLC5955
import numpy as np

PORTNAME = 'COM3'

# Load settings
with np.load('panel_settings.npz') as settings:
    maxcurrent = settings['maxcurrent']
    brightness = settings['brightness']
    dotcorrect = settings['dotcorrect']
    mode = settings['mode'][()]
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
        #img[np.random.uniform(size=(12,8)) < 0.25]
       # img[...,:3] = np.random.uniform(0.0, 0.75, (12,8,3))
        #img[...,3:] = np.random.uniform(0.0,0.001,(12,8,2))
        img[0:1,2:3,0] = 0.5
        
        img = TLC5955.pwm_code(img)
        scpi.command(b'disp:pwm:all ' + scpi.format_bytes(img.tobytes()))
        
        scpi.command(b'display on')