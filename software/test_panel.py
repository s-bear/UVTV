# -*- coding: utf-8 -*-
"""
Created on Tue Nov  3 14:21:13 2020

@author: uqkchene_local
"""

import numpy as np
import os
from tkinter import Tk, messagebox
from serial import Serial
from TLC5955 import SCPIProtocol, SCPIException, TLC5955

########################################### SET PORT NAME ###############################################
PORTNAME = 'COM5'

# Setting reset_config to True will save default settings into panel_config.npz
#  otherwise we'll load panel_config.npz and use the stored settings
reset_config = False

# Setting save_config to True will save the configuration settings to the
#  display panel in addition to panel_config.npz
save_config = False

config_path = 'board 2'

config_file = os.path.join(config_path,'panel_config.npz')

if not os.path.exists(config_file): reset_config = True
if reset_config:
    serial = '2'
    mode = {'dsprpt':True, 'espwm':True}
    maxcurrent = np.array([8, 8, 3.2, 15.9])
    brightness = np.array([0.42, 0.58, 0.5, 0.81])
    dotcorrect = np.ones((8,12,5))
    spif = 3000000
    np.savez(config_file,serial=serial,mode=mode,maxcurrent=maxcurrent,brightness=brightness,dotcorrect=dotcorrect,spif=spif)
else:
    with np.load(config_file,allow_pickle=True) as cfg:
        mode = cfg['mode'][()]
        maxcurrent = cfg['maxcurrent']
        brightness = cfg['brightness']
        dotcorrect = cfg['dotcorrect']
        spif = cfg['spif']

mode = TLC5955.mode_code(**mode)
maxcurrent = [TLC5955.maxcurrent_code(mc) for mc in maxcurrent]
brightness = [int(TLC5955.brightness_code(bc)) for bc in brightness]
dotcorrect = TLC5955.dotcorrect_code(dotcorrect)

img = np.zeros((8,12,5))
def img_bytes(img):
    return scpi.format_bytes(TLC5955.pwm_code(img).tobytes())

# Connect to panel and set the settings
with Serial(PORTNAME) as port:
    with SCPIProtocol(port) as scpi:
        #first thing, turn off echo because it's annoying
        try:
            resp = scpi.command(b'syst:comm:echo off', True, timeout=1)
        except SCPIException:
            pass
        #TODO: scpi.command(f'syst:serial?') to check that serial # matches
        scpi.command('disp:spif {}'.format(spif),True)
        scpi.command('disp:mode {}'.format(mode))
        scpi.command('disp:maxc {}'.format(','.join('{}'.format(mc) for mc in maxcurrent)))
        scpi.command('disp:bri {}'.format(','.join('{}'.format(bc) for bc in brightness)))
        scpi.command(b'disp:dotc:all ' + scpi.format_bytes(dotcorrect.tobytes()))
        
        if save_config:
            scpi.command('disp:save')
        
        #show an alignment image
        # three corners are red, green, blue
        img[[0,0,-1],[0,-1,-1],[0,1,2]] = 0.25
        
        scpi.command(b'disp:pwm:all ' + img_bytes(img))
        scpi.command(b'disp on')
        answer = messagebox.askyesno('LED Panel', 'Alignment. Continue?')
        scpi.command(b'disp off')
        img[:] = 0
        if answer:
            #cycle through the flatfielded images
            for c in range(5):
                img[...,c] = 0.25
                scpi.command(b'disp:pwm:all ' + img_bytes(img))
                scpi.command(b'disp on')
                answer = messagebox.askyesno('LED Panel', 'Continue?')
                scpi.command(b'disp off')
                img[...,c] = 0
                if not answer:
                    break

Tk().mainloop()