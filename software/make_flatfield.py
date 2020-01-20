# -*- coding: utf-8 -*-
"""
Created on Tue Jan  7 16:07:07 2020

@author: uqspowe6
"""

from PIL import Image
from skimage.morphology import watershed
import numpy as np
import matplotlib.pyplot as plt


red = np.array(Image.open('red.tif'))
green = np.array(Image.open('green.tif')) 
blue = np.array(Image.open('blue.tif')) 
violet = np.array(Image.open('violet.tif'))
uv = np.array(Image.open('uv.tif')) 

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
    
    #rotate 90 degrees so that the X of the image aligns with X of the LEDs
    #img = img.T[:,::-1]
    
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
    #remove any labels from pixels that are too dark, note, this will completely remove any dead LEDs from the labels
    labels[img < 0.1] = 0
    
    #take the means of the img image over each watershed area
    means = np.empty(grid.shape[:2])
    for i in range(96):
        #n.b. if there are any missing labels (e.g. from dead LEDs) then
        # the corresponding mean will be nan
        means.flat[i] = np.mean(img[labels == (i+1)])
    
    #plot, to see if it's working
    #use nanmin to get the minimum of means, just in case there's a dead LED
    #the dotcorrect coefficient at the dead LED will still be nan
    dotcorrect = np.nanmin(means)/means
    corrected = np.copy(img)
    for i in range(96):
        corrected[labels == (i+1)] *= dotcorrect.flat[i]
    
    fig,ax = plt.subplots(1,2)
    ax[0].imshow(img)
    ax[0].scatter(grid[...,1].flat,grid[...,0].flat,c=np.arange(96))
    ax[1].imshow(corrected)

    return means, labels


#get the right corner coordinates
red_means, red_labels = make_flat_field(red, (491, 376, 4080, 3100))
green_means, green_labels = make_flat_field(green, (491, 376, 4080, 3100))
blue_means, blue_labels = make_flat_field(blue, (491, 376, 4080, 3100))
violet_means, violet_labels = make_flat_field(violet, (491, 376, 4080, 3100))
uv_means, uv_labels = make_flat_field(uv, (491, 376, 4080, 3100))

#save the means so that flatfield.py can load them
np.savez('mean_flatfield_brightness.npz', red=red_means, green=green_means, blue=blue_means, violet=violet_means, uv=uv_means)
