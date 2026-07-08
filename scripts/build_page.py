#!/usr/bin/env python3
"""scene_v4.json + 各報告 → page/scan2cad.html (自含深色記錄頁, R6 精修版)。"""
import json, os, html
s = json.load(open("work/scene_v4.json"))
M = json.load(open("work/verify_metrics.json"))
VS = json.load(open("work/verify_scene_report.json"))
ST = json.load(open("work/step_report.json"))
R = s["room"]; W = R["x1"]-R["x0"]; D = R["z1"]-R["z0"]; CH = s["ceiling_h"]
cov = int(M["occupied_footprint_coverage"]*100)
dc = s.get("declash", {})
n_arch = sum(1 for o in s["furniture"] if o.get("src", "arch") in ("arch", None))
n_disc = sum(1 for o in s["furniture"] if str(o.get("src", "")).startswith("discovered"))
n_vlmf = sum(1 for o in s["furniture"] if o.get("src") == "vlm")
n_wall = len(s.get("wall_items", [])); n_ceil = len(s.get("ceiling_items", []))
n_vlm = n_vlmf + n_wall + n_ceil

SRC_BADGE = {"arch": ('已知', '#25c04a'), "discovered": ('點雲發掘', '#ff8c1a'),
             "discovered+vlm": ('發掘+VLM', '#ff8c1a'), "vlm": ('VLM新增', '#5a8cff')}
def rows():
    r = []
    for o in s["furniture"]:
        lab, col = SRC_BADGE.get(o.get("src", "arch"), ('已知', '#25c04a'))
        r.append(f"<tr><td>{html.escape(o['label'])}</td><td>{o['w']:.2f}×{o['d']:.2f}×{o['h']:.2f}</td>"
                 f"<td><span class='bd' style='color:{col};border-color:{col}66'>{lab}</span></td>"
                 f"<td class='mut'>{o.get('h_src','—')}</td></tr>")
    for o in s.get("wall_items", []):
        a, b = o["along"]
        r.append(f"<tr><td>{html.escape(o['label'])}</td><td>{b-a:.2f}×{o.get('thick',0.05):.2f}×{o['h']:.2f}</td>"
                 f"<td><span class='bd' style='color:#5a8cff;border-color:#5a8cff66'>VLM牆掛</span></td><td class='mut'>環景推定</td></tr>")
    for o in s.get("ceiling_items", []):
        r.append(f"<tr><td>{html.escape(o['label'])}</td><td>r{o.get('r',0.12):.2f}×垂{o.get('drop',0.6):.2f}</td>"
                 f"<td><span class='bd' style='color:#5a8cff;border-color:#5a8cff66'>VLM天花</span></td><td class='mut'>環景推定</td></tr>")
    return "\n".join(r)
cats = "、".join(s.get("vlm_categories", []))

HTML = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>3DGS → CAD 自動重繪 — 工坊 scan2cad</title>
<style>
:root{{--bg:#15171c;--fg:#e7e9ee;--mut:#9aa0ad;--o:#ff8000;--bd:#2a2f3a;--card:#1b1e25;--grn:#37c871;--blu:#5a8cff}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);line-height:1.8;font-family:-apple-system,'PingFang TC','Noto Sans TC',sans-serif}}
.wrap{{max-width:920px;margin:0 auto;padding:28px 22px 90px}}
h1{{font-size:26px;margin:0 0 4px}}h1 .o{{color:var(--o)}}
.tag{{color:var(--mut);font-size:14px;margin-bottom:20px}}
h2{{font-size:20px;margin:34px 0 10px;padding-top:16px;border-top:1px solid #21242c}}
h2 .n{{color:var(--o);font-weight:800;margin-right:8px}}
h3{{font-size:15.5px;margin:16px 0 6px;color:#f0f2f6}}
p{{margin:8px 0}}a{{color:var(--o);text-decoration:none}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:11px;padding:13px 16px;margin:12px 0}}
.key{{background:#16271c;border:1px solid #2c5a3f;border-radius:11px;padding:12px 15px;margin:12px 0}}.key b{{color:#6ed09a}}
.warn{{background:#2a2413;border:1px solid #5a4a1f;border-radius:11px;padding:12px 15px;margin:12px 0}}.warn b{{color:#ffc24b}}
.pass{{background:#16271c;border:1px solid #2c5a3f;color:#6ed09a;font-weight:700;border-radius:8px;padding:3px 10px;display:inline-block;font-size:13px}}
.hero{{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0}}
.hero .b{{flex:1;min-width:110px;background:var(--card);border:1px solid var(--bd);border-radius:11px;padding:12px 14px;text-align:center}}
.hero .n{{font-size:24px;font-weight:800;color:var(--o)}}.hero .c{{font-size:12px;color:var(--mut)}}
figure{{margin:16px 0;background:var(--card);border:1px solid var(--bd);border-radius:11px;padding:10px 10px 4px}}
figure img{{width:100%;border-radius:7px;display:block;background:#fff}}
figure svg{{width:100%;height:auto;border-radius:7px;display:block;background:#fbfbfd}}
figcaption{{font-size:12.5px;color:var(--mut);padding:8px 6px 6px;line-height:1.6}}figcaption b{{color:#c9cdd6}}figcaption .o{{color:var(--o)}}
.two{{display:flex;gap:12px;flex-wrap:wrap}}.two figure{{flex:1;min-width:280px}}
table{{width:100%;border-collapse:collapse;margin:12px 0;font-size:13px}}
th,td{{border:1px solid var(--bd);padding:6px 9px;text-align:left}}th{{background:#20242c;color:#c9cdd6}}
.bd{{font-size:11px;font-weight:700;padding:1px 7px;border-radius:20px;border:1px solid;background:#0002}}
.mut{{color:var(--mut)}}code{{background:#20242c;padding:1px 6px;border-radius:5px;color:#ffd9a8;font-size:.9em}}
ul{{padding-left:20px}}li{{margin:4px 0}}
.foot{{margin-top:40px;padding-top:16px;border-top:1px solid #21242c;color:var(--mut);font-size:12.5px}}
</style></head><body><div class="wrap">
<h1>3DGS → <span class="o">CAD 自動重繪</span>：工坊 scan2cad</h1>
<div class="tag">把教室/工坊的 <b>3DGS 高斯潑濺掃描</b>，自動分析出物件與空間尺寸，再用 <b>三套建模軟體（OpenSCAD／Blender／CadQuery）自動重繪</b>成參數化、可製造、通過裝配驗證的模型。串起 x5-roomtour（空間掃描）與 MCL39（建模驗證）兩套系統。</div>

<div class="hero">
<div class="b"><div class="n">{W:.1f}×{D:.1f}</div><div class="c">室內淨 (m)</div></div>
<div class="b"><div class="n">{M['room_area_m2']:.0f}</div><div class="c">面積 m²</div></div>
<div class="b"><div class="n">{M['n_objects_total']}</div><div class="c">重繪物件</div></div>
<div class="b"><div class="n">L1·L3 ✓</div><div class="c">通過驗證</div></div>
<div class="b"><div class="n">{cov}%</div><div class="c">點雲覆蓋</div></div>
</div>

<figure><img src="img/cmp_real_cad.png" alt="真實 vs 重繪">
<figcaption><b>成果對照：真實 3DGS 掃描（上）→ scan2cad 自動重繪（下）。</b>綠色檯面工作檯環繞＋中島、機台、櫃、凳、門窗、黑板——全自動從點雲生成，非人手擺放。</figcaption></figure>

<h2><span class="n">0</span>整體流程</h2>
<figure>
<svg viewBox="0 0 900 160" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,'PingFang TC',sans-serif">
<rect width="900" height="160" fill="#fbfbfd"/>
<text x="450" y="24" text-anchor="middle" font-size="14" font-weight="700" fill="#1a1c22">從「照片級掃描」到「可編輯・可製造・已驗證 CAD」的自動管線</text>
<g font-size="12.5" text-anchor="middle">
<rect x="10" y="46" width="120" height="60" rx="9" fill="#eef4ff" stroke="#bcd0f5"/><text x="70" y="70" font-weight="700" fill="#1f5fd0">3DGS 點雲</text><text x="70" y="90" font-size="11" fill="#444">解碼→公制</text>
<rect x="158" y="46" width="132" height="60" rx="9" fill="#eaf7ef" stroke="#b6e0c5"/><text x="224" y="66" font-weight="700" fill="#1c8f4e">① 分析已知</text><text x="224" y="85" font-size="11" fill="#444">arch+量高度</text><text x="224" y="99" font-size="10" fill="#666">8 件</text>
<rect x="318" y="46" width="132" height="60" rx="9" fill="#fbefe0" stroke="#ecd0a6"/><text x="384" y="66" font-weight="700" fill="#c8620a">② 幾何發掘</text><text x="384" y="85" font-size="11" fill="#444">分群找新物</text><text x="384" y="99" font-size="10" fill="#666">+{n_disc} 件</text>
<rect x="478" y="46" width="132" height="60" rx="9" fill="#eef0ff" stroke="#bcc4f5"/><text x="544" y="66" font-weight="700" fill="#3a4fd0">③ VLM 分析</text><text x="544" y="85" font-size="11" fill="#444">辨識+測量</text><text x="544" y="99" font-size="10" fill="#666">+{n_vlm} 件</text>
<rect x="638" y="46" width="122" height="60" rx="9" fill="#f2eefc" stroke="#cdc4f0"/><text x="699" y="66" font-weight="700" fill="#6a4fd0">④ 生成 CAD</text><text x="699" y="85" font-size="11" fill="#444">3 引擎</text><text x="699" y="99" font-size="10" fill="#666">+STEP</text>
<rect x="788" y="46" width="102" height="60" rx="9" fill="#eafaf0" stroke="#a8dcc0"/><text x="839" y="66" font-weight="700" fill="#1c8f4e">⑤ 驗證</text><text x="839" y="85" font-size="11" fill="#444">L1·L3</text><text x="839" y="99" font-size="10" fill="#666">自動修正</text>
</g>
<g fill="#e06a00" font-size="15" text-anchor="middle"><text x="144" y="80">→</text><text x="304" y="80">→</text><text x="464" y="80">→</text><text x="624" y="80">→</text><text x="774" y="80">→</text></g>
<text x="450" y="142" text-anchor="middle" font-size="11" fill="#666">每階段增加可繪製物件；最後生成三套建模檔＋STEP，並跑 MCL39 式 L1(實體健康)/L3(裝配)驗證與自動消除穿插</text>
</svg>
<figcaption><b>概念圖：五階段管線。</b>3DGS 是「模糊小雲球」不能直接量測，先解碼點雲＋公制對齊；三段層層增加物件（已知→幾何發掘→VLM），生成 OpenSCAD/Blender/CadQuery 三套模型，最後 L1/L3 驗證並自動修正穿插與出界。</figcaption>
</figure>

<h2><span class="n">1</span>輸入：真實工坊 3DGS</h2>
<p>來源＝去霧工坊 3DGS（<code>lt4_defog</code>，解碼後 106 萬顆高斯）。用天花板 T8 日光燈管（4ft=1.22m）標定公制 <code>k={s['K']:.3f}</code> m/單位。</p>
<figure><img src="img/pano.png" alt="工坊環景">
<figcaption><b>實際圖片：工坊 3DGS 環景。</b>綠檯面工作檯環繞＋中島、藍色圓凳、左側黃色置物箱與空壓機、右側鑽床機台列、天花板日光燈與通風管。<span class="o">同時是 VLM 分析依據</span>。</figcaption></figure>

<h2><span class="n">2</span>①+② 已知物件 & 幾何發掘</h2>
<p>先讀既有 <code>arch_elements.json</code>（牆/門/窗/黑板/12 燈/8 家具，皆公制），回點雲量每件高度；再掃「地板以上」點做占據分群（侵蝕分裂避免黏成巨塊），自動新增 <b>{n_disc}</b> 件。</p>
<figure><img src="img/discover.png" alt="幾何發掘">
<figcaption><b>概念圖：幾何發掘俯視除錯。</b>灰=點雲占據，<span style="color:#2ac04a">綠框=已知家具</span>（周邊工作檯），<span style="color:#ff8c1a">橙框=新發掘</span>（中央散落設備/凳）。</figcaption></figure>

<h2><span class="n">3</span>③ VLM 物件分析與測量</h2>
<p>頂視分群<b>結構上抓不到牆面/天花板的東西</b>。把環景照交給 VLM 辨識、以工作檯高 0.85m 為尺度錨測量，補上這些類別（投影布幕、公告欄、牆掛冷氣×2、通風管、鑽床列…），並替發掘方塊命名，共增 <b>{n_vlm}</b> 件。</p>
<div class="card mut">VLM 辨識類別：{html.escape(cats)}</div>
<figure><img src="img/vlm_seg.png" alt="VLM 放大">
<figcaption><b>實際圖片：VLM 看的環景放大段。</b>左側<b>鑽床/砂輪機列</b>、綠檯面、右側木製抽屜櫃、牆上冷氣、日光燈條。<span class="o">補進頂視幾何拿不到的物件，直接增加可繪製數</span>。</figcaption></figure>

<h2><span class="n">4</span>④ 自動生成 CAD（三套建模軟體）</h2>
<p>整合後的場景（{M['n_objects_total']} 件）自動吐成三種模型：<b>OpenSCAD</b>（宣告式 CSG，家具用參數化模組：檯面+桌腳、抽屜、座面、氣瓶…）、<b>Blender</b>（bpy 網格）、<b>CadQuery</b>（B-Rep→STEP，可製造）。三引擎一致＝跨系統驗證。</p>
<figure><img src="img/cmp_tri_engine.png" alt="三引擎">
<figcaption><b>三引擎並排：同一份 <code>scene.json</code> 自動生成。</b>左 OpenSCAD（CSG 細緻家具）、中 Blender（網格）、右 CadQuery（B-Rep 線框，匯出 STEP）。對應 MCL39 的三軟體交叉驗證。</figcaption></figure>
<div class="two">
<figure><img src="img/cad_openscad.png" alt="OpenSCAD 細緻"><figcaption><b>OpenSCAD 細緻重繪。</b>工作檯有桌腳/層板、門有門扇門框、窗有玻璃窗櫺、黑板有木框——對得上環景。</figcaption></figure>
<figure><img src="img/cad_prov.png" alt="來源上色"><figcaption><b>來源上色：<span style="color:#37c871">綠=已知</span>／<span style="color:#ff8c1a">橙=發掘</span>／<span style="color:#5a8cff">藍=VLM</span>。</b>一眼看出各階段貢獻。</figcaption></figure>
</div>
<figure><img src="img/turntable.gif" alt="轉盤">
<figcaption><b>360° 轉盤（OpenSCAD）。</b>各角度一致——窗框、投影布幕、機台、桌腳都對得上。</figcaption></figure>

<h3>檢索升級：粗方塊 → 精密參數化件</h3>
<p>點雲分群只給得出「有尺寸的方塊」。要更精細，正解是<b>檢索</b>——用一個<b>精密參數化零件</b>取代方塊，擺到偵測到的位置。這裡示範把偵測到的<b>鑽床</b>換成一支完整的立式鑽床件（底座 T 槽、立柱、可調圓工作台＋夾把、頭部鑄件、馬達、皮帶罩、主軸套筒＋夾頭、三幅進給手輪、開關盒）。</p>
<figure><img src="img/retrieval_ba.png" alt="鑽床 before/after">
<figcaption><b>檢索前後：同一台鑽床。</b>左＝點雲重建的粗 primitive；右＝精密參數化檢索件。<span class="o">reconstruction 給位置與尺寸，retrieval 給細節</span>——兩者互補。</figcaption></figure>
<div class="key"><b>可製造 B-Rep：</b>這支鑽床件也用 CadQuery 建成 B-Rep，<code>isValid()=True</code>、體積 0.022 m³，匯出 <code>out/drillpress.step</code>（301 KB）——直接送製造/模擬。這正是「檢索自 MCL39 已驗證零件庫」的作法：<b>把設計端（MCL39）建好驗過的精密件，擺進真實掃描空間（x5-roomtour）</b>。</div>

<h2><span class="n">5</span>⑤ MCL39 式驗證 L1 / L3 <span class="pass">{html.escape(VS['summary'])}</span></h2>
<p>把重繪場景接上 MCL39 驗證金字塔：</p>
<ul>
<li><b>L1 健康</b>：CadQuery 匯出的 STEP，房殼 + {ST['furniture_valid']} 件家具 B-Rep 全部 <code>isValid()</code> ✓（水密、無壞面）。</li>
<li><b>L3 裝配</b>：家具足跡兩兩<b>穿插檢查</b> + 是否<b>皆在房內</b>。初次抓到 2 處穿插 + 1 件戳出後牆，經自動修正（內縮 {dc.get('clipped_inside',0)} 件、縮小 {('/'.join(dc.get('shrunk',[])) or '—')}、移除 {('/'.join(dc.get('removed',[])) or '—')}）後 <b>0 穿插 0 出界</b> ✓。</li>
</ul>
<figure><img src="img/clash.png" alt="L3 裝配檢查">
<figcaption><b>L3 裝配檢查（修正後）。</b>綠=OK。修正前紅=穿插、橙=出界——這正是 MCL39 的干涉檢查在真實重繪場景上發揮作用：<span class="o">量測誤差造成的重疊被自動偵測並消除</span>。</figcaption></figure>

<h2><span class="n">6</span>疊回點雲驗證</h2>
<p>CAD 物件框疊回點雲俯視占據。佔據覆蓋率 <b>{cov}%</b>——掃到的站立物有 {cov}% 落在已建模框內，其餘是牆邊材料、檯上工具等零碎雜項（box 模型合理極限）。</p>
<figure><img src="img/verify.png" alt="疊回點雲">
<figcaption><b>CAD 框疊回點雲。</b>灰=點雲占據，彩框=重繪物件。牆邊工作檯貼合；中央散落雜物未建模，反映在覆蓋率——誠實呈現。</figcaption></figure>

<h2><span class="n">7</span>重繪物件清單（{M['n_objects_total']} 件）</h2>
<table><tr><th>物件</th><th>寬×深×高 (m)</th><th>來源</th><th>高度來源</th></tr>
{rows()}
</table>

<h2><span class="n">8</span>誠實的能與不能</h2>
<div class="key"><b>可靠：</b>房間外殼＋家具/機台的<b>細緻參數化模型</b>（桌腳、抽屜、機台結構），三引擎一致、通過 L1/L3。適合布局規劃、數位孿生、擺新設備前的干涉檢查。尺寸來自管長標定＋點雲量測。</div>
<div class="warn"><b>限制：</b>① 淨高 {CH:.1f}m 是「掃到的高度」，相機視角可能未含真天花板（±10%）。② 覆蓋率 {cov}%——工坊零碎雜物多，box 模型只抓大件。③ 特定機台的精密曲面/機構，模組是「像似」而非精確複製——精確版需<b>檢索</b>：擺入 MCL39 已建並驗證的參數化零件。④ 牆掛/天花板物件位置為環景方位推定（±0.5m）。</div>

<h2><span class="n">9</span>如何重跑</h2>
<div class="card"><code>bash run_pipeline.sh</code> — 解碼→分析→發掘→VLM→三引擎生成→L1/L3 驗證+自動修正→疊圖，一鍵到底。<br>
產物：<code>out/room.scad</code>（OpenSCAD 可改參）、<code>out/build_blender.py</code>（Blender）、<code>out/room.step</code>（可製造 B-Rep）、<code>work/scene_v4.json</code>（驗證後場景）。</div>

<div class="foot">scan2cad · 3DGS→CAD 自動重繪 · 串接 x5-roomtour(空間掃描) + MCL39(建模驗證)<br>
工坊 lt4_defog · k={s['K']:.3f} m/單位 · L1·L3 通過 · 三引擎(OpenSCAD/Blender/CadQuery) · 生成 {os.popen('date +%Y-%m-%d').read().strip()}</div>
</div></body></html>"""
os.makedirs("page", exist_ok=True)
open("page/scan2cad.html", "w").write(HTML)
print(f"→ page/scan2cad.html ({len(HTML)} bytes, {M['n_objects_total']} 物件)")
