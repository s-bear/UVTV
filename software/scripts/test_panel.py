# -*- coding: utf-8 -*-
"""
Created on Tue Nov  3 14:21:13 2020

@author: uqkchene_local
"""

import numpy as np
import os
from tkinter import Tk, messagebox
from serial import Serial
from serial.tools.list_ports import comports
from TLC5955 import SCPIProtocol, SCPIException, TLC5955

## Set PORTNAME = None to auto-detect
PORTNAME = None

##configuration file. set to None to use the board's built-in settings
config_file = 'board 4/panel_config.npz'

## Set the operating mode
# reset : save default settings into config_file, write those settings to the board
# test : load settings from config_file, nothing is saved. if config_file is None, switches to test-board
# test-board : load settings from the board, nothing is saved.
# upload : load settings from config_file, write those settings to the board
# download : load settings from the board, write those settings to config_file
mode = 'test'

## default configuration used by 'reset'
class config:
    # the serial number of the board
    serial = '4'
    # operating mode of the control chips: should be 'dsprpt':True, 'espwm': True for best performance
    mode = {'dsprpt':True, 'espwm':True}
    # maximum LED current in mA per channel (V & UV are combined). must be one of [3.2,8,11.2,15.9,19.1,23.9,27.1,31.9]
    maxcurrent = [8, 8, 3.2, 8]
    # channel brightness, from 0.1 to 1.0. (V & UV are combined)
    brightness = [0.42, 0.58, 0.5, 0.5]
    # dotcorrect coefficients
    dotcorrect = np.ones((8,12,5))
    # SPI frequency, in Hz. Should be 3000000  (3 MHz)
    spif = 3000000

all_modes = ('reset','test','test-board','upload','download')

#sanity checking for the various modes:
    
if mode not in all_modes:
    print(f'Unknown script mode "{mode}". mode must be one of {all_modes}')
    exit(1)

if mode in ('reset','download') and os.path.exists(config_file):
    print('f{config_file} already exists!')
    print(f'You must manually delete it before running test_panel.py with mode {mode}')
    exit(1)

if mode == 'test' and config_file is None:
    mode = 'test-board'

if mode in ('test','upload') and not os.path.exists(config_file):
    print(f'could not find config file: {config_file}')
    exit(1)

## functions for dealing with the configuration

def save_config(config_file):
    """save config to file"""
    if os.path.exists(config_file):
        raise RuntimeError(f'Error saving {config_file}: file already exists!')
    items = {name:value for name,value in vars(config).items() if not name.startswith('_')} #get the "public" members of config
    config_path = os.path.split(config_file)[0]
    if config_path: os.makedirs(config_path, exist_ok=True)
    np.savez(config_file, **items)

def load_config(config_file):
    """load config from file"""
    with np.load(config_file, allow_pickle=True) as cfg:
        config.serial = cfg['serial'][()]
        config.mode = cfg['mode'][()]
        config.maxcurrent = cfg['maxcurrent']
        config.brightness = cfg['brightness']
        config.dotcorrect = cfg['dotcorrect']
        config.spif = cfg['spif']

def upload_config(scpi, save=False):
    """upload config settings to board, if save==True, also save to board's internal storage"""
    mode_code = TLC5955.mode_code(**config.mode)
    mc_codes = ','.join(f'{TLC5955.maxcurrent_code(mc)}' for mc in config.maxcurrent)
    bc_codes = ','.join(f'{TLC5955.brightness_code(bc)}' for bc in config.brightness)
    dc_codes = scpi.format_bytes(TLC5955.dotcorrect_code(config.dotcorrect).tobytes())
    scpi.command(f'disp:spif {config.spif}', True)
    scpi.command(f'disp:mode {mode_code}')
    scpi.command(f'disp:maxc {mc_codes}')
    scpi.command(f'disp:bri {bc_codes}')
    scpi.command(f'disp:dotc:all {dc_codes}')
    if save:
        scpi.command('disp:save')

def download_config(scpi):
    serial = scpi.command(b'syst:serial?',True)[0]
    spif = scpi.command(b'disp:spif?',True)[0]
    mode_code = scpi.command(b'disp:mode?',True)[0]
    mc_codes = scpi.command(b'disp:maxc?',True)
    bc_codes = scpi.command(b'disp:bri?',True)
    dc_bytes = scpi.command(b'disp:dotc:all?',True)[0]
    dc_shape = scpi.command(b'disp:geom?',True)
    dc_codes = np.frombuffer(dc_bytes, np.uint8).reshape(dc_shape)
    config.serial = serial
    config.spif = spif
    config.mode = TLC5955.mode(mode_code)
    config.maxcurrent = [TLC5955.maxcurrent_mA(mc) for mc in mc_codes]
    config.brightness = [TLC5955.brightness(bc) for bc in bc_codes]
    config.dotcorrect = TLC5955.dotcorrect_img(dc_codes)
    
if mode == 'reset':
    #save defaults to file
    save_config(config_file)
elif mode in ('test', 'upload'):
    #load settings from file
    load_config(config_file)
    

#dead pixels have dotcorrect == nan
dead_pixels = np.where(np.any(np.isnan(config.dotcorrect),-1).flat)[0]

img = np.zeros((8,12,5))

def img_bytes(img):
    return scpi.format_bytes(TLC5955.pwm_code(img).tobytes())

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

# Connect to panel and set the settings
with Serial(PORTNAME) as port:
    with SCPIProtocol(port) as scpi:
        #first thing, turn off echo so that we don't need to handle unnecessary responses
        try:
            resp = scpi.command(b'syst:comm:echo off', True, timeout=1)
        except SCPIException:
            pass
        mfg,model,serial,rev = scpi.command(b'*IDN?',True)
        print(f'Connected to SCPI device:\n  Model: {model}\n  Maker: {mfg}\n  Serial: {serial}\n  Revision: {rev}')
        
        if str(serial) != str(config.serial):
            print(f'ERROR: Serial number mismatch!\n  config: "{config.serial}"\n  board: "{serial}"')
            exit(1)

        if mode in ('reset','test','upload'):
            upload_config(scpi)
        if mode in ('reset','upload'):
            scpi.command(b'disp:save')
        
        if mode in ('test-board','download'):
            scpi.command(b'disp:load')
        if mode == 'download':
            download_config(scpi)
            save_config(config_file)
            print(f'Downloaded and saved config to {config_file}')
        
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