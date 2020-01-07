# -*- coding: utf-8 -*-
"""
Created on Tue Jan  7 16:07:07 2020

@author: uqspowe6
"""

from PIL import Image
from skimage.morphology import watershed
import numpy as np

red = np.array(Image.open('red.tif'))

def make_flat_field(img, corners):
    """ calculate flat field image
    img: np.array (height, width, 3)
    corners: (x0,y0, x95, y95) -- coordinates of the corner LEDs
    
    returns:
        an (8,12) array of flat field image
        watershed labels for each pixels of img (0 is no label, pixels are 1 to 96)
    """
    #convert to luminance by summing
    img = np.sum(img, -1, float)
    
    #TODO: take new photos so that this doesn't need to be rotated
    #rotate 90 degrees so that the X of the image aligns with X of the LEDs
    img = img.T[:,::-1]
    
    #rescale to 0 to 1
    img = (img - img.min()) / (img.max() - img.min())
    
    #invert the image and convert to uint8 for use by watershed()
    img_inv = (255*(1.0-img)).astype(np.uint8)
    
    #approximate coordinates of the LEDs in the image, to create markers for watershed()
    x0,y0,x95,y95 = corners
    grid_x = np.linspace(x0,x95,12) #x coordinates of the LEDs
    grid_y = np.linspace(y0,y95,16)[::2] #y coordinates of the LEDs, generate double and take every other because of the hex pattern offsetting the lower right corner
    
    grid = np.stack(np.meshgrid(grid_y, grid_x, indexing='ij'),-1)
    grid[:,1::2,0] += np.diff(grid_y[:2])/2 #offset odd y's by half of the y height to get the hex pattern
    grid = grid.astype(int)
    
    #the markers array is all zeros indicating "no label" with the LEDs numbered from 1 at the grid locations
    markers = np.zeros_like(img_inv)
    markers[grid[...,0],grid[...,1]] = 1 + np.arange(96).reshape(grid.shape[:2])
    
    labels = watershed(img_inv, markers)
    labels[img < 0.1] = 0
    
    #take the means of the img image over each watershed area
    means = np.empty(grid.shape[:2])
    for i in range(96):
        means.flat[i] = np.mean(img[labels == (i+1)])
    
    return means, labels


#crop to the active area
#TODO: get the right crop coordinates
crop = (slice(1126,2330),slice(1736,2700))
red = red[crop]

#TODO: get the right corner coordinates
means, labels = make_flat_field(red, (65, 65, 1125, 905))

#TODO: save the means so that flatfield.py can load them
#TODO: also process the other color channel images

#try it out:
dotcorrect = means.min()/means
red_ff = np.sum(red, -1, float).T[:,::-1]
for i in range(96):
    red_ff[labels == (i+1)] *= dotcorrect.flat[i]


#show the images    
import matplotlib.pyplot as plt

fig,ax = plt.subplots(1,2)
ax[0].imshow(red)
ax[1].imshow(red_ff)
plt.show()
