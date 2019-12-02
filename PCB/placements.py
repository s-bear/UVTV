#Use ctrl+shift+v to paste and run in KiCad pcbnew
import pcbnew
from math import pi,cos,sin

board = pcbnew.GetBoard()

def mm(x):
    return int(x*pcbnew.IU_PER_MM)

def mil(x):
    return int(x*pcbnew.IU_PER_MILS)

def pt(p):
    return pcbnew.wxPoint(mm(p[0]),mm(p[1]))

def add_line(points, w, layer):
    lid = board.GetLayerID(layer)
    try: iter(w)
    except: w = [w]*(len(points)-1)
    for p0,p1,w0 in zip(points[:-1],points[1:],w):
        seg = pcbnew.DRAWSEGMENT(board)
        seg.SetStart(pt(p0))
        seg.SetEnd(pt(p1))
        seg.SetWidth(mm(w0))
        seg.SetLayer(lid)
        board.Add(seg)

def swap_pos(ref1, ref2):
    mod1 = board.FindModuleByReference(ref1)
    mod2 = board.FindModuleByReference(ref2)
    if mod1 is None:
        raise RuntimeError('Could not find ' + ref1)
    if mod2 is None:
        raise RuntimeError('Could not find ' + ref2)
    p1,o1 = mod1.GetPosition(), mod1.GetOrientation()
    p2,o2 = mod2.GetPosition(), mod2.GetOrientation()
    mod1.SetPosition(p2), mod1.SetOrientation(o2)
    mod2.SetPosition(p1), mod2.SetOrientation(o1)


def offset(off, pts):
    return [tuple(o + p for o,p in zip(off,pt)) for pt in pts]

def move(ref, x, y, o):
    mod = board.FindModuleByReference(ref)
    mod.SetPosition(pt((x,y)))
    mod.SetOrientation(10*o)

x0 = 50
y0 = 50
pitch = 5.3
c30 = cos(30*pi/180)
#place LED drivers & decoupling caps
for i,r in enumerate('12345'):
    yi = y0 + i*4*pitch
    for j,c in enumerate(['ABC','DEF']):
        xj = x0 + j*12*pitch*c30
        for k,m in enumerate(c):
            y = yi + 8.8
            x = xj + 7.7 + k*21
            ref = 'U-RGB{}{}'.format(r,m)
            print('{}: {}, {}'.format(ref,x,y))
            move(ref,x,y,180)
    for j,c in enumerate(['AC','DF']):
        xj = x0 + j*12*pitch*c30
        for k,m in enumerate(c):
            y = yi + 16
            x = xj + 18.2 + k*21
            ref = 'U-UV{}{}'.format(r,m)
            print('{}: {}, {}'.format(ref,x,y))
            move(ref,x,y,180)
    for j,c in enumerate(['ABCDE','FGHJK']):
        xj = x0 + j*12*pitch*c30
        for k,m in enumerate(c):
            y = yi + 10.05 + (k%2)*7.2
            x = xj + 1.425 + k*10.5
            ref = 'C{}{}'.format(r,m)
            print('{}: {}, {}'.format(ref,x,y))
            move(ref,x,y,180)

#place RGB LEDs
refs = ['RGB']
offs = [(3.5,1.65,-90)]
for i,r in enumerate('12345'):
    yi = y0 + i*4*pitch
    for j,c in enumerate('ABCDEF'):
        xj = x0 + j*4*pitch*c30
        for k in range(4):
            for l in range(4):
                x = xj + l*pitch*c30
                y = yi + k*pitch + (l%2)*pitch/2
                for m,o in zip(refs,offs):
                    ref = '{}{}{}{}'.format(m,r,c,4*k+l)
                    print('{}: {}, {}'.format(ref,x+o[0],y+o[1]))
                    move(ref, x+o[0], y+o[1], o[2])


#place UV LEDs
refs = ['V','UV']
offs = [(1.65,2.65,-90),(3.5,3.85,180)]
for i,r in enumerate('12345'):
    yi = y0 + i*4*pitch
    for j,c in enumerate('ACDF'):
        xj = x0 + j*6*pitch*c30
        for k in range(4):
            for l in range(4):
                x = xj + 2*l*pitch*c30
                y = yi + k*pitch
                if l > 1:
                    x -= pitch*c30
                    y += pitch/2
                for m,o in zip(refs,offs):
                    ref = '{}{}{}{}'.format(m,r,c,4*k+l)
                    print('{}: {}, {}'.format(ref,x+o[0],y+o[1]))
                    move(ref, x+o[0], y+o[1], o[2])
    for j,c in enumerate('BE'):
        xj = x0 + pitch*c30 + j*12*pitch*c30
        for k in range(4):
            for l in range(4):
                x = xj + 3*l*pitch*c30
                y = yi + k*pitch
                if (l%2) == 0:
                    y += pitch/2
                for m,o in zip(refs,offs):
                    ref = '{}{}{}{}'.format(m,r,c,4*k+l)
                    print('{}: {}, {}'.format(ref,x+o[0],y+o[1]))
                    move(ref, x+o[0], y+o[1], o[2])
#Swap UV LEDs to get them in the right order
swaps = [(2,8),(3,9),(4,2),(5,3),(6,10),(6,12),(7,11),(7,13)]
for r in '12345':
    for c in 'BE':
        for m in ['UV','V']:
            for a,b in swaps:
                r1 = '{}{}{}{}'.format(m,r,c,a)
                r2 = '{}{}{}{}'.format(m,r,c,b)
                swap_pos(r1,r2)


#draw hexagon grid
r = pitch/(2*c30) #radius of circumscribed circle
hex_pts = [(1.5*r,pitch),(2*r,0.5*pitch),(1.5*r,0.0),(0.5*r,0.0),(0.0,0.5*pitch),(0.5*r,pitch),(1.5*r,pitch),(2*r,0.5*pitch)]

rows, cols = 2, 3
cell_rows, cell_cols = 4, 4
layer = 'Eco1.User'
w0, w1 = 0.25, 0.5
for i in range(rows):
    yi = y0 + i*4*pitch
    for j in range(cols):
        xj = x0 + j*4*pitch*c30
        for k in range(cell_rows):
            for l in range(cell_cols):
                x = xj + l*pitch*c30
                y = yi + k*pitch + (l%2)*pitch/2
                pts = hex_pts[1:5]
                w = w0
                if k == 0:
                    if (l%2) == 0:
                        w = w1
                    else:
                        w = [w0,w1,w0]
                if l == 0:
                    pts = hex_pts[1:6]
                    if k > 0:
                        w = [w0,w0,w1,w1,w1]
                elif l == cell_cols-1:
                    pts = hex_pts[2:5]
                    if k == 0 and (l%2) == 1:
                        w = [w1,w0]
                add_line(offset((x,y),pts),w,layer)
                #last column
                if l == cell_cols-1 and j == cols-1:
                    if k == cell_rows - 1 and i == rows-1:
                        pts = hex_pts[1:3]
                    else:
                        pts = hex_pts[0:3]
                    add_line(offset((x,y),pts),w1,layer)
                #last row
                if k == cell_rows-1 and i == rows-1:
                    if (l%2) == 0:
                        pts = hex_pts[5:7]
                    else:
                        pts = hex_pts[4:8]
                    add_line(offset((x,y),pts),w1,layer)
