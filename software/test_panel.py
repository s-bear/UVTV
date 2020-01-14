# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 15:08:06 2019

@author: 61473
"""

from serial import Serial
from TLC5955 import SCPIProtocol, SCPIException, TLC5955
import numpy as np

import matplotlib as mpl
mpl.use('Qt5Agg') #draw figures in a window
import matplotlib.pyplot as plt
plt.ioff() #do not use "interactive mode" -- ie. plt.show() waits until figures are closed
from matplotlib.colors import to_rgba
from matplotlib.patches import RegularPolygon
from matplotlib.collections import PatchCollection

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

#get x and y coordinates of the hex grid
def draw_pattern(ax, target, distractors):
    grid_x = np.linspace(0,11*np.cos(np.deg2rad(30)),12)
    grid_y = np.linspace(0,7,8)
    
    grid = np.stack(np.meshgrid(grid_x, grid_y, indexing='xy'),-1)
    grid[:,1::2,1] += 0.5 #offset odd y's by half of the y height to get the hex pattern
    colors = np.zeros((96,4))
    colors[...,3] = 1.0
    colors[distractors] = to_rgba('gray')
    colors[target] = to_rgba('green')
    hexes = []
    for ij in np.ndindex(grid.shape[:2]):
        xy = grid[ij]
        hexes.append(RegularPolygon(xy, 6, 0.9/np.sqrt(3), np.pi/2))
    hexes = PatchCollection(hexes)
    hexes.set_color(colors)
    ax.add_collection(hexes, autolim=True)
    ax.set_aspect('equal')
    ax.invert_yaxis()
    ax.autoscale_view()

img = np.zeros((8,12,5))
   
#picking random pixels:
dead_pixels = [7,77,38]
valid_pixels = make_valid_pixels(96,dead_pixels)
#the array is 8x12 = 96 pixels, pick 48 randomly:
n_distractors = 47
pix_idx = np.random.choice(valid_pixels, n_distractors+1, replace=False)
target_idx = pix_idx[0]
distractor_idx = pix_idx[1:]

#convert the indices into coordinates
row, col = np.unravel_index(pix_idx, (8,12))
#img[row,col] has shape (n_distractors,5)

distractor_colors = np.array([[0.5]*5, [0, 0.5, 0, 0, 0], [0, 0, 0.5, 0, 0], [0, 0.5, 0.5, 0, 0], [0.2, 0.2, 0.2, 0, 0]]) #must have shape (n_colors, 5)
color_idx = np.random.choice(distractor_colors.shape[0], n_distractors, replace=True)
img[row[1:],col[1:],:] = distractor_colors[color_idx,:] #(n_distractors,5) 
        

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
#img[3:4,4:5,4] = 0.011

#img[5:6,3:4,0] = 0.7
#img[5:6,3:4,1] = 0.75
#img[5:6,3:4,2] = 0.3
#img[5:6,3:4,3] = 0.0033
#img[5:6,3:4,4] = 0.011

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
        
        scpi.command('disp:spif 3000000',True)
        #load the max current, mode, brightness, and dotcorrect
        scpi.command('disp:load')

        scpi.command(b'disp:pwm:all ' + scpi.format_bytes(img.tobytes()))
        
        #turn on the display
        scpi.command(b'display on')
        
        #draw the layout
        fig,ax = plt.subplots()
        draw_pattern(ax, target_idx, pix_idx[1:])
        plt.show() #wait until the figure is closed
        
        #turn off the display when the figure is closed
        scpi.command(b'display off')
        