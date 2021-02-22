
$fs = 0.1;
tolerance = 1; //gap between parts

//main body parameters
window_size = [55,65];
interior_depth = 25;
flat_width = 10;
wall_thickness = 3;
tube_length = 85;

hole_offset = 20;
hole_pad_dia = 8;
hole_dia = 3.2;
tab_thickness = 5;

window_fillet = 3;
interior_fillet = 3;

//lid
lid_slot = [10, 15]; //diameter, length
lid_lip = 5;

//retainer
retainer_lip = 10;

//platform
platform_size = [50,60];
standoff_dia = 4;
platform_hole = [2.2,4.4,1.6]; //diameter, countersink diameter, countersink depth

pitch = 5.3;
grid = [8,12];

//computed parameters
exterior_fillet = interior_fillet+wall_thickness;
box_size = [window_size.x + 2*flat_width, window_size.y + 2*flat_width, interior_depth + 2*wall_thickness];
tube_size = [window_size.x+2*flat_width,interior_depth+2*wall_thickness,tube_length];

lid_size = [tube_size.x + 2*wall_thickness + tolerance, tube_size.y + 2*wall_thickness + tolerance, lid_lip + wall_thickness];
lid_fillet = exterior_fillet + wall_thickness + tolerance/2;

module square_rounded(size, radius, center = false) {
    offset(r = radius) {
        offset(delta = -radius) {
            square(size,center);
        }
    }
}

//from https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Other_Language_Features
function circle_edges(r) = ($fn>0?($fn>=3?$fn:3):ceil(max(min(360/$fa,r*2*PI/$fs),5)));

module circle_outer(radius) {
    //number of edges
    n = circle_edges(radius);
    circle(r=radius/cos(180/n),$fn=n);
}

module cylinder_outer(height,radius) {
    n = circle_edges(radius);
    cylinder(h=height,r=radius/cos(180/n),$fn=n);
}

module cube_rounded(size, radius) {
    dx = size.x/2 - radius;
    dy = size.y/2 - radius;
    dz = size.z/2 - radius;
    hull() {
        translate([-dx,-dy,-dz]) sphere(radius);
        translate([ dx,-dy,-dz]) sphere(radius);
        translate([-dx, dy,-dz]) sphere(radius);
        translate([ dx, dy,-dz]) sphere(radius);
        translate([-dx,-dy, dz]) sphere(radius);
        translate([ dx,-dy, dz]) sphere(radius);
        translate([-dx, dy, dz]) sphere(radius);
        translate([ dx, dy, dz]) sphere(radius);
    };
}

module window_box_shell(size, radius) {
    hull() {
        dx = size.x/2 - radius;
        dy = size.y/2 - radius;
        dz = size.z/2 - radius;
        translate([-dx,-dy,-dz]) sphere(radius);
        translate([ dx,-dy,-dz]) sphere(radius);
        translate([-dx, dy,-dz]) rotate([90,0,0]) cylinder(2*radius,r=radius,center=true);
        translate([ dx, dy,-dz]) rotate([90,0,0]) cylinder(2*radius,r=radius,center=true);
        translate([-dx,-dy, dz]) cylinder(2*radius,r=radius,center=true);
        translate([ dx,-dy, dz]) cylinder(2*radius,r=radius,center=true);
        translate([-dx, dy, dz]) rotate([90,0,0]) cube(2*radius,center=true);
        translate([ dx, dy, dz]) rotate([90,0,0]) cube(2*radius,center=true);
    };    
}


module window_box() {
    difference() {
        //outer shell
        window_box_shell(box_size, interior_fillet + wall_thickness);
        
        //cut away interior to leave walls
        translate([0,wall_thickness,0])
        cube_rounded(box_size - [2*wall_thickness,0,2*wall_thickness], interior_fillet);
        
        //cut the window out
        translate([0,0,box_size.z/2 - 0.5*wall_thickness])
        linear_extrude(1.1*wall_thickness,center=true) {
           square_rounded(window_size,window_fillet,true);
        }
    }
}

module mount_tab(x) {
    translate([x,0,0])
    difference() {
    //rounded triangle
        linear_extrude(tab_thickness) {
            translate([-hole_pad_dia,0,0])
            minkowski() {
                circle(d=hole_pad_dia);
                circle(d=2*hole_pad_dia, $fn=3);
            }
        }
        translate([0,0,-0.05])
        cylinder_outer(1.1*tab_thickness,hole_dia/2);
    }
}


module tube() {
    difference() {
        union() {
            //tube body
            linear_extrude(tube_size.z)
            square_rounded([tube_size.x,tube_size.y],exterior_fillet,center=true);
    
            translate([0, tube_size.y/2, tube_length - hole_offset]) rotate([90,0,0]) {
                mount_tab(tube_size.x/2 + hole_pad_dia/2);
                mirror([1,0,0]) mount_tab(tube_size.x/2 + hole_pad_dia/2);
            }
        }
        //remove tube interior
        translate([0,0,-0.05])
        linear_extrude(tube_size.z+0.1)
        square_rounded([tube_size.x - 2*wall_thickness,tube_size.y-2*wall_thickness],interior_fillet,center=true);
        }
}

module body() {
    union() {
        rotate([90,0,0])
        window_box();

        translate([0,0,0.5*window_size.y+flat_width])
        tube();
    }
}

module lid() {
    difference() {
        linear_extrude(lid_size.z)
        square_rounded([lid_size.x,lid_size.y],lid_fillet,true);
        
        translate([0,0,wall_thickness])
        linear_extrude(lid_size.z)
        square_rounded([lid_size.x-2*wall_thickness,lid_size.y-2*wall_thickness],lid_fillet-wall_thickness,true);
        
        translate([0,0,-0.05])
        hull() {
            dx = (lid_slot.y - lid_slot.x)/2;
            translate([dx,0,0]) cylinder(1.1*wall_thickness,d=lid_slot.x);
            translate([-dx,0,0]) cylinder(1.1*wall_thickness,d=lid_slot.x);
        }
    }
}

module retainer() {
    retainer_size = [box_size.x + 2*wall_thickness + tolerance, box_size.y + wall_thickness + tolerance/2, wall_thickness + retainer_lip];
    
    shell_size = [retainer_size.x, retainer_size.y, box_size.z];
    difference() {
        translate([0, 1.25*tolerance-wall_thickness, 0])
        window_box_shell(shell_size, interior_fillet + 2*wall_thickness + tolerance/2);
        
        translate([0,0,-retainer_size.z])
        scale([1.1,1.1,1])
        cube(shell_size,true);
        
        //cut the window box out
        color("orange")
        translate([0,0,-wall_thickness])
        window_box_shell([box_size.x+tolerance,box_size.y+tolerance,box_size.z], interior_fillet + wall_thickness + tolerance/2);
        
        //cut the window out
        translate([0,0,box_size.z/2 - 0.5*wall_thickness])
        linear_extrude(1.1*wall_thickness,center=true) {
           square_rounded(window_size,window_fillet,true);
        }
    }
}

module standoff(h, d, off,slope) {
    r = d/2;
    union() {
        cylinder(h,r,r);
        cylinder(h-off,r+slope*(h-off),r);
    }
}

module countersink(depth,drill_dia,sink_dia,sink_depth) {
    union() {
        cylinder_outer(depth,drill_dia/2);
        cylinder_outer(sink_depth,sink_dia/2);
    }
}

module platform() {
    pitch_y = pitch*cos(30);
    cell_h = pitch/cos(30);
    
    t = wall_thickness;
    d = standoff_dia;
    
    led_origin = [-(grid.x-0.5)*pitch/2, -(grid.y - 1)*pitch_y/2];
    hole_offsets = [
        [pitch/2, 3*pitch_y + 0.5*cell_h],
        [pitch/2, 7*pitch_y + 0.5*cell_h],
        [7*pitch, 0.5*cell_h],
        [7*pitch, 10*pitch_y + 0.5*cell_h]
    ];
    
    difference() {
        union() {
            linear_extrude(t)
            square_rounded(platform_size,interior_fillet,center=true);
        
            translate([led_origin.x, led_origin.y, t]) {
                for(xy = hole_offsets) translate(xy) standoff(t,d,1,1);
            }
        }
        translate(led_origin) {
            for(xy = hole_offsets) translate(xy) countersink(2*t,platform_hole.x,platform_hole.y,platform_hole.z);
        }
    }
}

body();

translate([0,0, 0.5*window_size.y + flat_width + tube_length + wall_thickness])
rotate([180,0,0])
lid();

translate([0,-wall_thickness,0])
rotate([90,0,0])
retainer();

rotate([90,0,0])
platform();