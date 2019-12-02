
from tlc5955 import tlc5955, to_hex
import serial, time

#        RGB-A      UV-A       RGB-B      UV-C       RGB-C
chips = [tlc5955(i) for i in range(2*5)] #one for each chip

chips_rgb = [chips[i] for i in (0,2,4,5,7,9)]
chips_uv = [chips[i] for i in (1,3,6,8)]

#set up the buffers
rgb_max_current = [11.2, 11.2, 8] #[R,G,B] mA
uv_max_current = [8.0, 8.0, 8.0] #[x,V,UV] mA

#set display repeat and enhanced spectrum pwm
for c in chips:
    c.set_mode(dsprpt=True, espwm=True)

for c in chips_rgb:
    c.max_current = [8.0, 8.0, 3.2]
    c.brightness = [0.42, 0.58, 0.5]
    c.dot_correct = [0.635]*48
    c.pixels = [0.5, 0.5, 0.5]*16

for c in chips_uv:
    c.max_current = [15.9, 15.9, 15.9]
    c.brightness = [0.81, 0.81, 0.81] #V, v/UV, UV
    c.dot_correct = [0.51,0.51,0.79,0.51,0.79,0.79]*8
    c.pixels = [0.0]*48

def pb(x):
    print(str(x, 'UTF-8'))

def clear_error(port):
    port.write(b';')
    pb(port.read_until(b';'))

def update_config(port):
    for c in chips:
        port.write(bytes('Wc{:04X} '.format(c.config_addr),'utf-8'))
        port.write(bytes(to_hex(c.config_bytes(),2),'utf-8'))
        port.write(b';')
        pb(port.read_until(b';'))

def update_pixels(port):
    for c in chips:
        port.write(bytes('Wp{:04X} '.format(c.pixel_addr),'utf-8'))
        port.write(bytes(to_hex(c.pixel_bytes(),2),'utf-8'))
        port.write(b';')
        pb(port.read_until(b';'))

def update_pixel(port, c, pi, val):
    c.pixels[pi] = val
    addr = c.pixel_addr + pi
    port.write(bytes('Wp{:04X} '.format(addr),'UTF-8'))
    port.write(bytes('{:04X}'.format(tlc5955.pixel_to_code(val)),'UTF-8'))
    port.write(b';')
    pb(port.read_until(b';'))

def send_config(port):
    port.write(b'C');
    pb(port.read_until(b';'))

def send_pixels(port):
    port.write(b'P');
    pb(port.read_until(b';'))

def init(port):
    """turn off pixel clock, write config data twice, write pixel data"""
    set_clock(port,False)
    send_config(port)
    send_config(port)
    send_pixels(port)

def set_clock(port,enable):
    if enable:
        port.write(b'G1')
    else:
        port.write(b'G0')
    pb(port.read_until(b';'))

with serial.Serial('COM20',19200,parity=serial.PARITY_ODD,rtscts=True,timeout=2) as ser:
    print('Clear:')
    clear_error(ser)
    print('Update config:')
    update_config(ser)
    print('Update pixels:')
    update_pixels(ser)
    print('Initializing controllers')
    init(ser)
    print('Starting pixel clock')
    set_clock(ser,True)
    #TODO: update only the pixel memory for those that changed
    for c in chips_rgb:
        for i in range(0,48):
            update_pixel(ser,c,i,1.0)
            time.sleep(0.2)
            update_pixel(ser,c,i,0.0)
            send_pixels(ser)
    set_clock(ser,False)