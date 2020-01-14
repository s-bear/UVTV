# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 12:16:11 2019

@author: Laurie
"""
import numpy as np
means = np.load('mean_flatfield_brightness.npz')
red_means = means['red']
green_means = means['green']
blue_means = means['blue']
violet_means = means['violet']
uv_means = means['uv']

flat_field = np.ones((8, 12, 5))

flat_field[..., 0] = red_means
flat_field[..., 1] = green_means
flat_field[..., 2] = blue_means
flat_field[..., 3] = violet_means
flat_field[..., 4] = uv_means

dotcorrect = np.nanmin(flat_field, (0,1))/flat_field

#the other settings:
mode = {'dsprpt':True, 'espwm':True}
maxcurrent = np.array([8, 8, 3.2, 15.9])
brightness = np.array([0.42, 0.58, 0.5, 0.81])

np.savez('panel_settings.npz', dotcorrect=dotcorrect, mode=mode, maxcurrent=maxcurrent, brightness=brightness)


#save the flatfield settings to the control board's memory:

from serial import Serial
from TLC5955 import SCPIProtocol, SCPIException, TLC5955

########################################### SET PORT NAME ###############################################
PORTNAME = 'COM4'

#convert to what the controller wants
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
        #set the settings
        scpi.command('disp:mode {}'.format(mode))
        scpi.command('disp:maxc {}'.format(','.join('{}'.format(mc) for mc in maxcurrent)))
        scpi.command('disp:bri {}'.format(','.join('{}'.format(bc) for bc in brightness)))
        scpi.command(b'disp:dotc:all ' + scpi.format_bytes(dotcorrect.tobytes()))
        #save the settings
        scpi.command('disp:save')