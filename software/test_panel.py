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

# Settings
dot_correct_img = ([[], [], [0.889307709,0.869233563,0.9695549,0.827823079,0.956298347,0.944463239,0.898731121,0.884494548,
                    0.778211382,0.938405087,0.778211382,0.933749547,0.866423565,0.886530828,0.96608801,0.913184507,0.904774765,
                    0.963504069,0.959832684,0.899793194,0.861078983,0.946357448,0.902313555,0.958706539,0.903505933,0.814895894,
                    0.948608319,0.858277399,1,0.903969132,0.936176158,0.95425544,0.912861035,0.960107755,0.788709184,0.896974565,
                    0.891152844,0.937486009,0.814064246,0.858277399,1,0.903969132,0.873539841,0.946945928,0.95425544,0.914380851,
                    0.885148881,0.920258206,0.93547036,0.91221478,0.928496203,0.952762847,0.915030181,0.969162231,0.872606986,
                    0.981427232,0.829380601,0.938116039,0.92569976,0.95463612,0.872447917,0.876969792,0.957856816,0.932969451,
                    0.950950894,0.934896051,0.869571988,0.920359331,0.931698092,0.947749583,0.92569976,0.904750331,0.958295195,
                    0.922208765,0.843390479,0.926160396,0.916908424,0.719312936,0.963642639,0.899044654,0.872334331,0.918492118,
                    0.901391019,0.989193339,0.852121274,0.917385471,0.927057391,0.89198328,0.924703285,0.889945544,0.841505074,
                    0.895823306,0.83494081,0.92508629,0.881538785,0.874337761,], [], []])
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
        img[1:,1:,1] = 0.5
        
        img = TLC5955.pwm_code(img)
        scpi.command(b'disp:pwm:all ' + scpi.format_bytes(img.tobytes()))
        
        scpi.command(b'display on')