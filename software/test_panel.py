# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 15:08:06 2019

@author: 61473
"""

from serial import Serial
from TLC5955 import SCPIProtocol, SCPIException, TLC5955

PORTNAME = 'COM3'

with Serial(PORTNAME) as port:
    with SCPIProtocol(port) as scpi:
        #first thing, turn off echo because it's annoying
        try:
            resp = scpi.command(b'syst:comm:echo off',timeout=1)
        except SCPIException:
            pass
        
        scpi.command('disp:mode {}'.format(TLC5955.mode(dsprpt=True,espwm=True)),False)