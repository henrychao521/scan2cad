// ===== scan2cad 自動重繪: 由 3DGS 點雲量測 + 幾何發掘 + VLM 生成 =====
// 室內淨 8.82(寬) × 10.48(深) × 1.98(高) m  |  模式=prov
// k=0.8592 m/單位  |  來源: lt4_raw.ply + arch + VLM
$fn=40;
use <furniture_lib.scad>;
C_WALL=[0.82,0.80,0.76]; C_FLOOR=[0.60,0.58,0.55]; C_BOARD=[0.16,0.28,0.22];
C_BENCH=[0.42,0.70,0.55]; C_DESK=[0.86,0.74,0.52]; C_CAB=[0.55,0.62,0.70]; C_MACHINE=[0.58,0.61,0.66];
C_LIGHT=[1,0.96,0.75]; C_SCREEN=[0.92,0.92,0.9]; C_AC=[0.9,0.9,0.92]; C_DUCT=[0.85,0.85,0.87];
C_KNOWN=[0.30,0.80,0.40]; C_DISC=[1.0,0.55,0.10]; C_VLM=[0.30,0.55,1.0];

module walls(){ difference(){
  translate([-5.087,-5.221,0]) cube([9.124,10.785,1.980]);
  translate([-4.937,-5.071,-0.01]) cube([8.824,10.485,2.000]);
  translate([-5.107,-4.521,0]) cube([0.190,0.900,1.930]); // 門(推定)
  translate([-5.107,-4.971,0.900]) cube([0.190,1.211,0.980]); // 窗左
  translate([-5.107,0.260,0.900]) cube([0.190,5.054,0.980]); // 窗左
  translate([3.717,-4.971,0.900]) cube([0.190,3.831,0.980]); // 窗右
  translate([3.717,1.310,0.900]) cube([0.190,1.570,0.980]); // 窗右
} }
module floorplane(){ color(C_FLOOR) translate([-5.087,-5.221,-0.03]) cube([9.124,10.785,0.03]); }
module blackboard(){
  color(C_BOARD) translate([-3.737,5.384,0.85]) cube([6.424,0.03,1.0]);
  color([0.75,0.6,0.4]) difference(){
    translate([-3.787,5.364,0.80]) cube([6.524,0.05,1.10]);
    translate([-3.737,5.334,0.85]) cube([6.424,0.06,1.0]);
  }
}
module skirting(){ color([0.5,0.48,0.45]) union(){
  translate([-4.937,-5.071,0]) cube([8.824,0.02,0.07]);
  translate([-4.937,5.394,0]) cube([8.824,0.02,0.07]);
  translate([-4.937,-5.071,0]) cube([0.02,10.485,0.07]);
  translate([3.867,-5.071,0]) cube([0.02,10.485,0.07]);
} }
module windetail(){
  // 窗 x0 -4.97--3.76m
  color([0.58,0.76,0.9]) translate([-5.022,-4.971,0.900]) cube([0.02,1.211,0.980]);
  color([0.92,0.92,0.92]) union(){
    translate([-5.042,-4.971,0.900]) cube([0.06,0.05,0.980]);
    translate([-5.042,-3.810,0.900]) cube([0.06,0.05,0.980]);
    translate([-5.042,-4.971,0.900]) cube([0.06,1.211,0.05]);
    translate([-5.042,-4.971,1.830]) cube([0.06,1.211,0.05]);
    translate([-5.042,-4.385,0.900]) cube([0.06,0.04,0.980]);
  }
  color([0.8,0.78,0.75]) translate([-4.937,-5.001,0.860]) cube([0.08,1.271,0.04]);
  // 窗 x0 0.26-5.31m
  color([0.58,0.76,0.9]) translate([-5.022,0.260,0.900]) cube([0.02,5.054,0.980]);
  color([0.92,0.92,0.92]) union(){
    translate([-5.042,0.260,0.900]) cube([0.06,0.05,0.980]);
    translate([-5.042,5.264,0.900]) cube([0.06,0.05,0.980]);
    translate([-5.042,0.260,0.900]) cube([0.06,5.054,0.05]);
    translate([-5.042,0.260,1.830]) cube([0.06,5.054,0.05]);
    translate([-5.042,1.251,0.900]) cube([0.06,0.04,0.980]);
    translate([-5.042,2.262,0.900]) cube([0.06,0.04,0.980]);
    translate([-5.042,3.273,0.900]) cube([0.06,0.04,0.980]);
    translate([-5.042,4.283,0.900]) cube([0.06,0.04,0.980]);
  }
  color([0.8,0.78,0.75]) translate([-4.937,0.230,0.860]) cube([0.08,5.114,0.04]);
  // 窗 x1 -4.97--1.14m
  color([0.58,0.76,0.9]) translate([3.802,-4.971,0.900]) cube([0.02,3.831,0.980]);
  color([0.92,0.92,0.92]) union(){
    translate([3.782,-4.971,0.900]) cube([0.06,0.05,0.980]);
    translate([3.782,-1.190,0.900]) cube([0.06,0.05,0.980]);
    translate([3.782,-4.971,0.900]) cube([0.06,3.831,0.05]);
    translate([3.782,-4.971,1.830]) cube([0.06,3.831,0.05]);
    translate([3.782,-4.033,0.900]) cube([0.06,0.04,0.980]);
    translate([3.782,-3.075,0.900]) cube([0.06,0.04,0.980]);
    translate([3.782,-2.118,0.900]) cube([0.06,0.04,0.980]);
  }
  color([0.8,0.78,0.75]) translate([3.807,-5.001,0.860]) cube([0.08,3.891,0.04]);
  // 窗 x1 1.31-2.88m
  color([0.58,0.76,0.9]) translate([3.802,1.310,0.900]) cube([0.02,1.570,0.980]);
  color([0.92,0.92,0.92]) union(){
    translate([3.782,1.310,0.900]) cube([0.06,0.05,0.980]);
    translate([3.782,2.830,0.900]) cube([0.06,0.05,0.980]);
    translate([3.782,1.310,0.900]) cube([0.06,1.570,0.05]);
    translate([3.782,1.310,1.830]) cube([0.06,1.570,0.05]);
    translate([3.782,2.075,0.900]) cube([0.06,0.04,0.980]);
  }
  color([0.8,0.78,0.75]) translate([3.807,1.280,0.860]) cube([0.08,1.630,0.04]);
}
module doordetail(){
  color([0.62,0.45,0.30]) union(){
    translate([-4.967,-4.571,0]) cube([0.210,0.05,1.930]);
    translate([-4.967,-3.621,0]) cube([0.210,0.05,1.930]);
    translate([-4.967,-4.571,1.930]) cube([0.210,1.000,0.05]);
  }
  color([0.72,0.55,0.38]) translate([-4.937,-4.521,0]) rotate([0,0,-42]) cube([0.04,0.900,1.930]);
  color([0.85,0.7,0.3]) translate([-4.937,-4.521,1.0]) rotate([0,0,-42]) translate([0.04,0.820,0]) sphere(r=0.03);
}
module furniture(){
  // #0 工作檯(連排) 7.57x1.91x1.37m [arch] -> bench
  translate([2.905,-0.645,0]) rotate([0,0,270.00]) color(C_KNOWN) bench(7.570,1.910,1.370);
  // #1 工作檯(連排) 7.13x2.39x1.13m [arch] -> bench
  translate([-3.722,-0.455,0]) rotate([0,0,270.00]) color(C_KNOWN) bench(7.130,2.390,1.130);
  // #2 工作檯(連排) 5.82x0.95x0.79m [arch] -> bench
  translate([0.565,4.784,0]) rotate([0,0,-2.41]) color(C_KNOWN) bench(5.816,0.951,0.790);
  // #3 工作桌 2.11x1.03x0.97m [arch] -> bench
  translate([-0.420,3.395,0]) rotate([0,0,-6.71]) color(C_KNOWN) bench(2.115,1.027,0.970);
  // #4 櫃 1.11x1.00x0.86m [arch] -> cabinet
  translate([-2.205,3.755,0]) rotate([0,0,-98.28]) color(C_KNOWN) cabinet(1.112,1.001,0.860);
  // #5 櫃 0.65x0.23x1.19m [arch] -> cabinet
  translate([-3.271,-4.178,0]) rotate([0,0,-18.69]) color(C_KNOWN) cabinet(0.650,0.227,1.190);
  // #6 櫃 1.24x0.80x1.02m [arch] -> cabinet
  translate([1.505,3.337,0]) rotate([0,0,-5.00]) color(C_KNOWN) cabinet(1.245,0.803,1.020);
  // #7 邊檯/櫃 2.14x0.57x1.60m [arch] -> cabinet
  translate([-0.340,-4.766,0]) rotate([0,0,180.00]) color(C_KNOWN) cabinet(2.140,0.570,1.600);
  // #8 器材(推定) 0.66x0.42x1.15m [discovered+vlm] -> genericbox
  translate([-1.577,-0.121,0]) rotate([0,0,90.00]) color(C_DISC) genericbox(0.660,0.420,1.150);
  // #9 空壓機 0.54x0.39x1.34m [discovered+vlm] -> compressor
  translate([-1.412,-2.281,0]) rotate([0,0,90.00]) color(C_DISC) compressor(0.540,0.390,1.340);
  // #10 木凳 0.63x0.33x0.81m [discovered+vlm] -> stool
  translate([0.868,-4.306,0]) rotate([0,0,0.00]) color(C_DISC) stool(0.630,0.330,0.810);
  // #11 木凳 0.36x0.30x1.50m [discovered+vlm] -> stool
  translate([1.333,-2.791,0]) rotate([0,0,0.00]) color(C_DISC) stool(0.360,0.300,1.500);
  // #12 器材(推定) 0.39x0.27x1.21m [discovered+vlm] -> genericbox
  translate([-1.502,-0.706,0]) rotate([0,0,0.00]) color(C_DISC) genericbox(0.390,0.270,1.210);
  // #13 木凳 0.30x0.27x1.45m [discovered+vlm] -> stool
  translate([1.138,-2.371,0]) rotate([0,0,90.00]) color(C_DISC) stool(0.300,0.270,1.450);
  // #14 鑽床 0.50x0.50x1.55m [vlm] -> drillpress
  translate([-2.250,-2.600,0]) rotate([0,0,0.00]) color(C_VLM) drillpress(0.500,0.500,1.550);
  // #15 鑽床 0.50x0.50x1.55m [vlm] -> drillpress
  translate([-2.250,-1.400,0]) rotate([0,0,0.00]) color(C_VLM) drillpress(0.500,0.500,1.550);
}
module lights(){
  translate([-1.970,-1.510,1.930]) rotate([0,0,173.8]) color(C_LIGHT) translate([-0.925,-0.06,0]) cube([1.850,0.12,0.05]);
  translate([3.400,0.200,1.930]) rotate([0,0,85.6]) color(C_LIGHT) translate([-0.630,-0.06,0]) cube([1.260,0.12,0.05]);
  translate([1.450,-0.140,1.930]) rotate([0,0,174.7]) color(C_LIGHT) translate([-0.665,-0.06,0]) cube([1.330,0.12,0.05]);
  translate([-0.510,0.060,1.930]) rotate([0,0,172.0]) color(C_LIGHT) translate([-0.670,-0.06,0]) cube([1.340,0.12,0.05]);
  translate([-2.490,0.260,1.930]) rotate([0,0,173.4]) color(C_LIGHT) translate([-0.650,-0.06,0]) cube([1.300,0.12,0.05]);
  translate([0.630,1.730,1.930]) rotate([0,0,172.4]) color(C_LIGHT) translate([-0.875,-0.06,0]) cube([1.750,0.12,0.05]);
  translate([-1.530,1.950,1.930]) rotate([0,0,174.0]) color(C_LIGHT) translate([-0.720,-0.06,0]) cube([1.440,0.12,0.05]);
  translate([-4.760,3.160,1.930]) rotate([0,0,91.4]) color(C_LIGHT) translate([-0.470,-0.06,0]) cube([0.940,0.12,0.05]);
  translate([1.860,3.340,1.930]) rotate([0,0,177.4]) color(C_LIGHT) translate([-0.630,-0.06,0]) cube([1.260,0.12,0.05]);
  translate([0.010,3.530,1.930]) rotate([0,0,-1.9]) color(C_LIGHT) translate([-0.580,-0.06,0]) cube([1.160,0.12,0.05]);
  translate([1.580,4.850,1.930]) rotate([0,0,171.0]) color(C_LIGHT) translate([-0.925,-0.06,0]) cube([1.850,0.12,0.05]);
  translate([-0.900,5.160,1.930]) rotate([0,0,174.2]) color(C_LIGHT) translate([-0.630,-0.06,0]) cube([1.260,0.12,0.05]);
}
module wallitems(){
  color(C_VLM) translate([-2.400,-5.071,0.600]) cube([2.000,0.040,1.700]); // 投影布幕[vlm]
  color(C_VLM) translate([-4.937,-4.600,0.900]) cube([0.050,1.700,1.400]); // 藍色公告欄[vlm]
  color(C_VLM) translate([3.667,-3.200,1.650]) cube([0.220,0.900,0.300]); // 牆掛冷氣[vlm]
  color(C_VLM) translate([0.600,5.194,1.650]) cube([0.900,0.220,0.300]); // 牆掛冷氣[vlm]
}
module ceilingitems(){
  color(C_VLM) translate([-1.300,-3.600,1.080]) cylinder(h=0.900,r=0.130); // 螺旋通風管[vlm]
}
color(C_WALL) walls();
floorplane();
skirting(); windetail();
doordetail();
blackboard();
furniture(); lights(); wallitems(); ceilingitems();
