
$fs = 0.1;

pitch = 5.3;
grid = [12,8];
wall = 0.8;
height = 10;

hole_dia = 1.5;
hole_depth = 5;

pitch_x = pitch*cos(30);
cell_w = pitch/cos(30);

hole_offsets = [
        [3*pitch_x + 0.5*cell_w, pitch/2],
        [7*pitch_x + 0.5*cell_w, pitch/2],
        [0.5*cell_w, 7*pitch],
        [10*pitch_x + 0.5*cell_w, 7*pitch]
    ];

module cylinder_outer(height,radius) {
    n = ($fn>0?($fn>=3?$fn:3):ceil(max(min(360/$fa,radius*2*PI/$fs),5)));
    cylinder(h=height,r=radius/cos(180/n),$fn=n);
}

module hex(h,w) {
    //w is across flats
    r = w*0.5773502691896257; // 1/(2*cos(180/6))
    cylinder(h,r,r,$fn=6);
}

module cell() {
    difference() {
        hex(height,pitch+wall);
        hex(height,pitch-wall);
    }
}

difference() {
    union() {
        for(ix = [0 : 2 : grid.x - 1]) {
            for(iy = [0 : grid.y - 1]) {
                translate([pitch_x*ix, pitch*iy]) cell();
                translate([pitch_x*(ix+1),pitch*(iy+0.5)]) cell();
            }
        }
    }

    for(xy = hole_offsets) {
        translate(xy)
        cylinder_outer(hole_depth,hole_dia/2);
    }
}