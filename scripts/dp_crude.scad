$fn=48;
module drillpress_crude(w,d,h){
  base=min(w,d);
  translate([0,0,0.03]) cube([base*0.9,d*0.9,0.06],center=true);
  translate([0,-d*0.15,0]) cylinder(h=h*0.92,r=base*0.09);
  translate([0,0,h*0.45]) cube([base*0.7,d*0.6,0.04],center=true);
  translate([0,d*0.05,h*0.82]) cube([base*0.85,d*0.75,h*0.16],center=true);
  translate([0,d*0.25,h*0.72]) cylinder(h=h*0.12,r=0.02);
}
color([0.62,0.64,0.68]) drillpress_crude(0.5,0.5,1.55);
