// ===== scan2cad 細緻家具參數化模組庫 =====
// 約定: 每個模組以原點為中心(XY), 底座在 Z=0, 頂在 Z=h。呼叫端負責 translate/rotate/color。

module _leg(x,y,z0,z1,t=0.055){ translate([x,y,z0]) cube([t,t,z1-z0],center=false); }

// 工作檯: 檯面 + 桌腳(長檯多對) + 下層板
module bench(w,d,h,top_t=0.045,leg=0.06){
  inset=0.06;
  // 檯面
  translate([-w/2,-d/2,h-top_t]) cube([w,d,top_t]);
  // 桌腳(每 ~1.4m 一對)
  npair=max(2,floor(w/1.4)+1);
  for(i=[0:npair-1]){
    lx=-w/2+inset+ i*(w-2*inset)/(npair-1);
    for(sy=[-1,1]){
      ly=sy*(d/2-inset)-leg/2;
      translate([lx-leg/2,ly,0]) cube([leg,leg,h-top_t]);
    }
  }
  // 下層板
  translate([-w/2+inset,-d/2+inset,0.12]) cube([w-2*inset,d-2*inset,0.02]);
}

// 櫃: 本體 + 抽屜/門縫 + 把手
module cabinet(w,d,h){
  difference(){
    translate([-w/2,-d/2,0]) cube([w,d,h]);
    // 正面(+Y)刻抽屜縫
    nd=max(2,round(h/0.32));
    for(i=[1:nd-1]) translate([-w/2+0.03, d/2-0.012, i*h/nd-0.006]) cube([w-0.06,0.02,0.012]);
  }
  // 把手(每格中央)
  nd=max(2,round(h/0.32));
  for(i=[0:nd-1]) translate([0, d/2+0.005, (i+0.5)*h/nd]) rotate([90,0,0]) cylinder(h=0.03,r=0.012,center=true);
}

// 木凳: 座面 + 四斜腳
module stool(w,d,h,seat_t=0.035){
  translate([0,0,h-seat_t/2]) cube([w,d,seat_t],center=true);
  for(sx=[-1,1]) for(sy=[-1,1])
    translate([sx*(w/2-0.04),sy*(d/2-0.04),0])
      cylinder(h=h-seat_t,r1=0.016,r2=0.013);
}

// 空壓機: 臥式氣瓶 + 馬達 + 輪 + 把手
module compressor(w,d,h){
  tr=min(d,h*0.55)/2;                       // 氣瓶半徑
  // 氣瓶(沿 w 軸)
  translate([-w/2+0.08,0,tr+0.06]) rotate([0,90,0]) cylinder(h=w-0.16,r=tr);
  for(e=[-1,1]) translate([e*(w/2-0.08),0,tr+0.06]) sphere(r=tr*0.98);
  // 馬達(上方)
  translate([-w*0.1,0,2*tr+0.06]) cube([w*0.4,d*0.6,h-2*tr-0.06],center=true);
  // 輪
  for(sy=[-1,1]) translate([-w/2+0.12,sy*(d/2-0.03),tr*0.5]) rotate([90,0,0]) cylinder(h=0.04,r=tr*0.5,center=true);
  // 把手
  translate([w/2-0.05,0,2*tr]) rotate([0,60,0]) cube([0.02,d*0.5,0.28],center=true);
}

// 立式鑽床(精密檢索件): 底座T槽+立柱+可調圓工作台+頭部鑄件+馬達+皮帶罩+主軸套筒+夾頭+三幅進給手輪+開關盒
module drillpress(w,d,h){
  rc=0.032; coly=-0.10;
  // 底座(圓角 + T槽 + 安裝孔)
  difference(){
    translate([0,coly,0]) hull() for(sx=[-0.15,0.15],sy=[-0.12,0.19]) translate([sx,sy,0]) cylinder(r=0.03,h=0.05);
    for(sx=[-0.07,0,0.07]) translate([sx,coly+0.04,0.036]) cube([0.016,0.30,0.03],center=true);
    for(sx=[-0.11,0.11]) translate([sx,coly-0.07,-0.01]) cylinder(r=0.011,h=0.08);
  }
  // 立柱
  translate([0,coly,0.05]) cylinder(r=rc,h=h-0.05);
  // 可調圓工作台 + 支臂套環 + 夾把
  tz=h*0.42;
  translate([0,0.07,tz]) difference(){ cylinder(r=0.14,h=0.028); translate([0,0,-0.01]) cylinder(r=0.018,h=0.05); }
  translate([0,coly,tz+0.014]) rotate([90,0,0]) cylinder(r=0.05,h=0.11,center=true);
  translate([0.13,0.03,tz+0.014]) rotate([0,90,0]) cylinder(r=0.008,h=0.10);
  translate([0.23,0.03,tz+0.014]) sphere(r=0.02);
  // 頭部鑄件(立柱→前 錐鼓)
  hz=h*0.80;
  hull(){
    translate([0,coly,hz]) rotate([90,0,0]) cylinder(r=0.10,h=0.14,center=true);
    translate([0,0.09,hz+0.01]) rotate([90,0,0]) cylinder(r=0.07,h=0.05,center=true);
  }
  // 馬達(後鼓) + 皮帶罩(頂蓋)
  translate([0,coly-0.10,hz+0.02]) rotate([90,0,0]) cylinder(r=0.085,h=0.15);
  translate([0,coly-0.01,hz+0.11]) scale([1,1.7,0.55]) sphere(r=0.085);
  // 主軸套筒 + 夾頭 + 鑽頭
  translate([0,0.09,hz-0.11]) cylinder(r=0.022,h=0.13);
  translate([0,0.09,hz-0.19]) cylinder(r1=0.031,r2=0.026,h=0.08);
  translate([0,0.09,hz-0.215]) cylinder(r=0.006,h=0.04);
  // 三幅進給手輪(右側)
  translate([0.10,0.02,hz-0.03]) rotate([0,90,0]) cylinder(r=0.022,h=0.03,center=true);
  for(a=[0:120:240]) translate([0.10,0.02,hz-0.03]) rotate([a,0,0]) { cylinder(r=0.007,h=0.11); translate([0,0,0.11]) sphere(r=0.015); }
  // 開關盒
  translate([-0.075,coly+0.02,h*0.5]) cube([0.05,0.035,0.075]);
}

// 層架: 立柱 + 層板
module shelving(w,d,h){
  for(sx=[-1,1]) for(sy=[-1,1]) translate([sx*(w/2-0.03),sy*(d/2-0.03),0]) cube([0.03,0.03,h]);
  ns=max(3,round(h/0.4));
  for(i=[0:ns]) translate([-w/2,-d/2,i*h/ns]) cube([w,d,0.02]);
}

// 通用箱(器材) — 稍作導角感: 主體 + 頂蓋線
module genericbox(w,d,h){
  translate([-w/2,-d/2,0]) cube([w,d,h]);
  translate([-w/2,-d/2,h-0.015]) cube([w,d,0.015]);
}
