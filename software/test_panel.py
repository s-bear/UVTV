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
mode = TLC5955.mode_code(**mode) #unpack the dict and give it to mode_code as arguments
maxcurrent = [TLC5955.maxcurrent_code(mc) for mc in maxcurrent]
brightness = [int(TLC5955.brightness_code(bc)) for bc in brightness]

def make_valid_pixels(n,dead_pixels=[]):
    start = 0
    vp = []
    for dp in sorted(dead_pixels):
        vp.extend(range(start,min(dp,n)))
        if dp >= n: return vp
        start = dp + 1
    vp.extend(range(start,n))
    return vp

# Connect to panel and set the settings
with Serial(PORTNAME) as port:
    with SCPIProtocol(port) as scpi:
        #first thing, turn off echo because it's annoying
        try:
            resp = scpi.command(b'syst:comm:echo off', True, timeout=1)
        except SCPIException:
            pass
        
        scpi.command('disp:spif 3000000',True)
        
        #scpi.command('disp:mode {}'.format(mode))
        #scpi.command('disp:maxc {}'.format(','.join('{}'.format(mc) for mc in maxcurrent)))
        #scpi.command('disp:bri {}'.format(','.join('{}'.format(bc) for bc in brightness)))
        
        #load the max current, mode, brightness, and dotcorrect
        scpi.command('disp:load')
        
        img = np.zeros((8,12,5))
        
        #select random pixels:
        #img[np.random.uniform(size=(8,12)) < 0.25]
        #img[...,:3] = np.random.uniform(0.0, 0.75, (12,8,3))
        #img[...,3:] = np.random.uniform(0.0,0.001,(8,12,2))
        
        
        #picking random pixels:
        dead_pixels = [7,77]
        valid_pixels = make_valid_pixels(96,dead_pixels)
        #the array is 8x12 = 96 pixels, pick 48 randomly:
        n_distractors = 47
        pix_idx = np.random.choice(valid_pixels, n_distractors, replace=False)
        #convert the indices into coordinates
        row, col = np.unravel_index(pix_idx, (8,12))
        #img[row,col] is shape (n_distractors,5)
        
        distractor_colors = ([0] = 1, [1] = 1, [2] = 1, [0:3] = 0.5, [1:2] = 0.5) #something that's shape (n_colors, 5)
        color_idx = np.random.choice(distractor_colors.shape[0], n_distractors, replace=True)
        img[row,col,:] = distractor_colors[color_idx,:]) #(n_distractors,5)
        
        img[row, col, :] = np.random.uniform(0.0, 0.25, (n_distractors,5)) #or anything that's shape (10,3)
        #img[row, col, :3] = np.random.uniform(0.0, 1.0, (n_distractors,3)) #or anything that's shape (10,3)
        
        # All on
        #img[: , :, 4] = 0.2
        
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
        