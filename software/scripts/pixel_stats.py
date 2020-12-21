# -*- coding: utf-8 -*-
"""
Created on Tue Jan  7 16:07:07 2020

@author: uqspowe6
"""

import os
import numpy as np
import imageio as iio
from skimage.filters import median
from skimage.measure import moments, regionprops
from skimage.segmentation import flood
from skimage.draw import circle

config_path = 'board 2 data/2'

def path(fname):
    return os.path.abspath(os.path.join(config_path,fname))

def flood_centroid(img, pt, tol=0.5):
    #use a flood fill to find blob of related pixels
    mask = flood(img, pt, tolerance=tol*img[pt])
    #take 1st order moments and scale them by the 0th moment to get centroid
    #TODO: use regionprops instead?
    m = moments(img*mask,1)
    return (m[1,0]/m[0,0], m[0,1]/m[0,0])
    
def align_grid(img):
    # apply a median filter to remove noise
    img_smooth = np.empty_like(img)
    for i in range(img.shape[-1]):
        img_smooth[...,i] = median(img[...,i],np.ones((5,5)))
    #img_smooth = median(img,np.ones((5,5,1)))
    #find maximum on each channel
    imax = np.argmax(img_smooth.reshape((-1,3)),0)
    #convert them back to coordinates
    y, x = np.unravel_index(imax, img_smooth.shape[:2])
    #find centroids of regions rather than use the max
    y,x = np.transpose([flood_centroid(img_smooth[...,i], (y[i],x[i])) for i in range(3)])
    #hex grid coordinates in a 1x1 square
    hx = np.linspace(0,1,12) #x coordinates of the hex grid
    hy = np.linspace(0,1,16)[::2] #y coordinates of the hex grid
    hyx = np.stack(np.meshgrid(hy, hx, indexing='ij'),-1)
    hyx[:,1::2,0] += hy[1]/2
    #we need to transform these coordinates into the image space
    # lstsq solves 'a x = b' for x. a is the grid coordinates, b is the image coordinates
    a = np.concatenate((hyx[[0,0,-1],[0,-1,-1]], [[1.],[1.],[1.]]),1)
    b = np.stack((y,x)).T
    T = np.linalg.lstsq(a, b, rcond=None)[0]
    #apply the transform
    return np.dot(hyx,T[:2]) + T[2]
    
def label_pixels(grid, shape, size=0.9):
    """make a mask for img with a circle stamped on each grid location"""
    #get the pixel radius in pixels
    R = size*0.5*np.hypot(*(grid[1,0]-grid[0,0]))
    
    labels = np.zeros(shape,int)
    
    for i, yx in enumerate(grid.reshape((-1,2))):
        yx = np.round(yx)
        r,c = circle(yx[0],yx[1],R,shape)
        labels[r,c] = i+1
    
    return labels

def segment_by_label(img, labels):
    rps = regionprops(labels)
    pix = []
    for rp in rps:
       pix += [np.array(img[rp.slice],float)] #copy and add to list
       pix[-1][~rp.image] = np.nan #nan for pixels not covered by label
    return np.stack(pix) #assume that the labels all have the same size

def reconstruct_image(labels,pix):
    rps = regionprops(labels)
    img = np.zeros(labels.shape)
    for i, rp in enumerate(rps):
        img[rp.slice][rp.image] = pix[i][rp.image]
    return img
    
### Load images
print(f'Loading images from "{config_path}"... ',end='',flush=True)
corners = iio.imread(path('corners.tif'))
red = iio.imread(path('red.tif'))
green = iio.imread(path('green.tif'))
blue = iio.imread(path('blue.tif'))
violet = iio.imread(path('violet.tif'))
uv = iio.imread(path('uv.tif'))
print('DONE',flush=True)

print('Aligning grid... ',end='',flush=True)
grid = align_grid(corners)
labels = label_pixels(grid, corners.shape[:2])
print('DONE',flush=True)

print('Segmenting pixels... ',end='',flush=True)
red_pix = segment_by_label(red, labels)
green_pix = segment_by_label(green, labels)
blue_pix = segment_by_label(blue, labels)
violet_pix = segment_by_label(violet, labels)
uv_pix = segment_by_label(uv, labels)
print('DONE',flush=True)

def pixel_stats(pix):
    #take mean over all but first dimensions
    pix_mean = np.nanmean(pix, (1,2,3))
    #average spectral channels and normalize to local max
    pix_norm = np.nanmean(pix, -1)
    pix_norm /= np.nanmean(pix_norm,(1,2),keepdims=True)
    
    return pix_mean, pix_norm

print('Computing stats: Red',end='',flush=True)
red_mean, red_norm = pixel_stats(red_pix)

print(', Green',end='',flush=True)
green_mean, green_norm = pixel_stats(green_pix)

print(', Blue',end='',flush=True)
blue_mean, blue_norm = pixel_stats(blue_pix)

print(', Violet',end='',flush=True)
violet_mean, violet_norm = pixel_stats(violet_pix)

print(', UV... ',end='',flush=True)
uv_mean, uv_norm = pixel_stats(uv_pix)

print(' DONE',flush=True)

#stack the data
means = np.stack((red_mean,green_mean,blue_mean,violet_mean,uv_mean),-1)
#normalize by max mean in each channel
mean_max = np.max(means, (0,1))
means /= mean_max

#threshold dead pixels
means[means < 0.1] = np.nan

print('Calculating intra-channel pixel spatial deviation:')
print('  Red...',flush=True)
red_dev = red_norm - np.nanmean(red_norm,0)

print('  Green...',flush=True)
green_dev = green_norm - np.nanmean(green_norm,0)

print('  Blue...',flush=True)
blue_dev = blue_norm - np.nanmean(blue_norm,0)

print('  Violet...',flush=True)
violet_dev = violet_norm - np.nanmean(violet_norm,0)

print('  UV... ',flush=True)
uv_dev = uv_norm - np.nanmean(uv_norm,0)

print('  DONE',flush=True)


print('Calculating systemic inter-channel spatial deviation:')
print('  Red - Green ...',flush=True)
red_green = np.nanmean(red_norm - green_norm, 0)

print('  Red - Blue ...',flush=True)
red_blue = np.nanmean(red_norm - blue_norm, 0)

print('  Red - Violet ...',flush=True)
red_violet = np.nanmean(red_norm - violet_norm, 0)

print('  Red - UV ...',flush=True)
red_uv = np.nanmean(red_norm - uv_norm, 0)

print('  Green - Blue ...',flush=True)
green_blue = np.nanmean(green_norm - blue_norm, 0)

print('  Green - Violet ...',flush=True)
green_violet = np.nanmean(green_norm - violet_norm, 0)

print('  Green - UV ...',flush=True)
green_uv = np.nanmean(green_norm - uv_norm, 0)

print('  Blue - Violet ...',flush=True)
blue_violet = np.nanmean(blue_norm - violet_norm, 0)

print('  Blue - UV ...',flush=True)
blue_uv = np.nanmean(blue_norm - uv_norm, 0)

print('  Violet - UV ...',flush=True)
violet_uv = np.nanmean(violet_norm - uv_norm, 0)
print('  DONE',flush=True)

spatial_dev = np.stack((red_green,red_blue,red_violet, red_uv, green_blue,
                        green_violet, green_uv, blue_violet, blue_uv, violet_uv),0)

#save all of this data for other scripts
fname = path('pixel_stats.npz')
print(f'Saving {fname}')
np.savez(fname,means=means,spatial_deviation=spatial_dev)

print('Generating figures... ',end='',flush=True)
import matplotlib.pyplot as plt
import matplotlib.cm as cm

#intra-channel pixel variation (spot dead/messy pixels)
fig,ax = plt.subplots(2,3,sharex=True,sharey=True,
                      subplot_kw={'xticks':[],'yticks':[]})

fig.suptitle('In-pixel spatial deviation')
ax[0,0].set_title('Red')
ax[0,1].set_title('Green')
ax[0,2].set_title('Blue')

ax[1,0].set_title('Violet')
ax[1,1].set_title('UV')
ax[1,2].remove()

red_dev_img = reconstruct_image(labels, red_dev)
L = 3*np.nanstd(red_dev)
ax[0,0].imshow(red_dev_img,vmin=-L,vmax=L,cmap=cm.bwr)

green_dev_img = reconstruct_image(labels, green_dev)
L = 3*np.nanstd(green_dev)
ax[0,1].imshow(green_dev_img,vmin=-L,vmax=L,cmap=cm.bwr)

blue_dev_img = reconstruct_image(labels, blue_dev)
L = 3*np.nanstd(blue_dev)
ax[0,2].imshow(blue_dev_img,vmin=-L,vmax=L,cmap=cm.bwr)

violet_dev_img = reconstruct_image(labels, violet_dev)
L = 3*np.nanstd(violet_dev)
ax[1,0].imshow(violet_dev_img,vmin=-L,vmax=L,cmap=cm.bwr)

uv_dev_img = reconstruct_image(labels, uv_dev)
L = 3*np.nanstd(uv_dev)
ax[1,1].imshow(uv_dev_img,vmin=-L,vmax=L,cmap=cm.bwr)


#inter-channel pixel variation (potential for spatial-cues)
fig,ax = plt.subplots(4,4,sharex=True,sharey=True,figsize=(4,4),dpi=100,
                      subplot_kw={'xticks':[],'yticks':[],'frameon':False})

fig.suptitle('Inter-channel systemic spatial differences')
ax[0,0].set_title('Red')
ax[0,1].set_title('Green')
ax[0,2].set_title('Blue')
ax[0,3].set_title('Violet')

ax[0,0].set_ylabel('- UV')
ax[1,0].set_ylabel('- Violet')
ax[2,0].set_ylabel('- Blue')
ax[3,0].set_ylabel('- Green')

ax[1,3].remove()
ax[2,2].remove(); ax[2,3].remove()
ax[3,1].remove(); ax[3,2].remove(); ax[3,3].remove()

L = np.max(np.abs([np.nanmax(spatial_dev), np.nanmin(spatial_dev)]))
ax[3,0].imshow(red_green,vmin=-L,vmax=L,cmap=cm.bwr)
ax[2,0].imshow(red_blue,vmin=-L,vmax=L,cmap=cm.bwr)
ax[1,0].imshow(red_violet,vmin=-L,vmax=L,cmap=cm.bwr)
ax[0,0].imshow(red_uv,vmin=-L,vmax=L,cmap=cm.bwr)
ax[2,1].imshow(green_blue,vmin=-L,vmax=L,cmap=cm.bwr)
ax[1,1].imshow(green_violet,vmin=-L,vmax=L,cmap=cm.bwr)
ax[0,1].imshow(green_uv,vmin=-L,vmax=L,cmap=cm.bwr)
ax[1,2].imshow(blue_violet,vmin=-L,vmax=L,cmap=cm.bwr)
ax[0,2].imshow(blue_uv,vmin=-L,vmax=L,cmap=cm.bwr)
im = ax[0,3].imshow(violet_uv,vmin=-L,vmax=L,cmap=cm.bwr)

cbar_ax = fig.add_axes([0.75, 0.15, 0.05, 0.5])
fig.colorbar(im, cax=cbar_ax)


fig,ax = plt.subplots(4,4,sharex=True,sharey=True,figsize=(4,4),dpi=100,
                      subplot_kw={'xticks':[],'yticks':[],'frameon':False})

ax_all = fig.add_subplot(111,xticks=[],yticks=[],frameon=False)
fig.suptitle('Channel mapped to Yellow')
ax[0,0].set_title('Red')
ax[0,1].set_title('Green')
ax[0,2].set_title('Blue')
ax[0,3].set_title('Violet')

ax_all.set_ylabel('Channel mapped to Blue',labelpad=15)
ax[0,0].set_ylabel('UV')
ax[1,0].set_ylabel('Violet')
ax[2,0].set_ylabel('Blue')
ax[3,0].set_ylabel('Green')

ax[1,3].remove()
ax[2,2].remove(); ax[2,3].remove()
ax[3,1].remove(); ax[3,2].remove(); ax[3,3].remove()

def stack_mean_norm(y,b):
    y,b = np.nanmean(y,0),np.nanmean(b,0)
    y /= np.nanmax(y)
    b /= np.nanmax(b)
    return np.stack((y,y,b),-1)

ax[0,0].imshow(stack_mean_norm(red_norm,uv_norm))
ax[1,0].imshow(stack_mean_norm(red_norm,violet_norm))
ax[2,0].imshow(stack_mean_norm(red_norm,blue_norm))
ax[3,0].imshow(stack_mean_norm(red_norm,green_norm))
ax[0,1].imshow(stack_mean_norm(green_norm,uv_norm))
ax[1,1].imshow(stack_mean_norm(green_norm,violet_norm))
ax[2,1].imshow(stack_mean_norm(green_norm,blue_norm))
ax[0,2].imshow(stack_mean_norm(blue_norm,uv_norm))
ax[1,2].imshow(stack_mean_norm(blue_norm,violet_norm))
ax[0,3].imshow(stack_mean_norm(violet_norm,uv_norm))