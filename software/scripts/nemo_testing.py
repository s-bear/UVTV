# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 15:08:06 2019

@author: 61473
"""

from serial import Serial
from serial.tools.list_ports import comports
from TLC5955 import SCPIProtocol, SCPIException, TLC5955
import numpy as np

import matplotlib as mpl
mpl.use('TkAgg') #draw figures in a window
import matplotlib.pyplot as plt
plt.ioff() #do not use "interactive mode" -- ie. plt.show() waits until figures are closed
from matplotlib.colors import to_rgba
from matplotlib.patches import RegularPolygon
from matplotlib.collections import PatchCollection

## Set PORTNAME = None to auto-detect
PORTNAME = None

if PORTNAME is None:
    print('Detecting Serial ports... ',end='',flush=True)
    target_hwid = 'VID:PID=16C0:04'
    for port in comports():
        if port.hwid.find(target_hwid) > 0:
            PORTNAME = port.device
            print(f'Found Teensy on {PORTNAME}')
            break
if PORTNAME is None:
    print('Could not find Teensy USB!')
    exit(1)

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
#(6, 7)
dead_pixels = [6,37,79]
valid_pixels = make_valid_pixels(96,dead_pixels)
#the array is 8x12 = 96 pixels, pick 48 randomly:
n_distractors = 20
pix_idx = np.random.choice(valid_pixels, n_distractors+1, replace=False)
target_idx = pix_idx[0]
distractor_idx = pix_idx[1:]

#convert the indices into coordinates
row, col = np.unravel_index(pix_idx, (8,12))
#img[row,col] has shape (n_distractors,5)

#distractor_colors = np.array([[0.95,0.395,0.153,0.00141,0.00115],[0.89,0.37,0.143,0.001320,0.001080],[0.633,0.263,0.102,0.000939,0.000776],[0.412,0.171,0.0661,0.000610,0.000600],[0.285,0.118,0.0457,0.000422,0.000394]]) #must have shape (n_colors, 5)
distractor_colors = np.array([[0.95,0.395,0.153,0.00141,0],[0.89,0.37,0.143,0.001320,0],[0.633,0.263,0.102,0.000939,0],[0.412,0.171,0.0661,0.000610,0],[0.285,0.118,0.0457,0.000422,0]]) #must have shape (n_colors, 5)

color_idx = np.random.choice(distractor_colors.shape[0], n_distractors, replace=True)
#img[row[1:],col[1:],:] = distractor_colors[color_idx,:] #(n_distractors,5) 
        
#target_color = [0.1196,0.1281,0.05125,0.0005638,0.00018] #0.94 jnd
#target_color = [0.1196,0.1281,0.05125,0.0005638,0.00025] #1.8 jnd
#target_color = [0.1196,0.1281,0.05125,0.0005638,0.0003] #3.1 jnd
#target_color = [0.1196,0.1281,0.05125,0.0005638,0.00053] #4.1 jnd
#target_color = [0.1195,0.1280,0.05122,0.0005634,0.0006829] #5.1 jnd
#target_color = [0.1194,0.1280,0.05119,0.00056,0.00085] #6.2 jnd
#target_color = [0.1194,0.1279,0.05116,0.0005627,0.001023] #7.1 jnd
#target_color = [0.1176,0.126,0.0504,0.0005546,0.001244] #8.1 jnd
#target_color = [0.1176,0.126,0.0504,0.0005546,0.001490] #9.1 jnd
#target_color = [0.3506,0.1457,0.0512,0.0005199,0.001969] # 10 jnd

target_color = [1,0,0,0,0] # pure red


img[row[:],col[:]] = target_color

#Blue training 

#img[1,7] = [0.3506,0.1457,0.0512,0.0005199,0.001969]
#img[1,1] = [0, 0, 0, 0, 0.2]
#img[1,5] = [0.024, 0.026, 0.95, 0.00011, 0.000079]
#img[3,4] = [0.024, 0.026, 0.95, 0.00011, 0.000079]
#img[5,3] = [0.024, 0.026, 0.95, 0.00011, 0.000079]

# UV training

#img[1,7] = [0.119,0.128,0.051,0.00055618,0.001790]
#img[1,1] = [0.119,0.128,0.051,0.00055618,0.001790]
#img[1,5] = [0.119,0.128,0.051,0.00055618,0.001790]
#img[3,4] = [0.119,0.128,0.051,0.00055618,0.001790]
#img[5,3] = [0.119,0.128,0.051,0.00055618,0.001790]

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
        
        print(scpi.command('*IDN?',True))
        
        #load the max current, mode, brightness, dotcorrect, SPI frequency
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
        