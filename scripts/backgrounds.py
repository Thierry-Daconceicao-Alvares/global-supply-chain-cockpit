"""Draw the page backgrounds (2560x1440 PNG) with HTML and Chromium."""
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from layout import *
OUT = Path(__file__).resolve().parents[1] / 'build' / 'backgrounds'; OUT.mkdir(parents=True, exist_ok=True)
ICON = {
 'globe': '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c2.6 2.6 3.8 5.6 3.8 9s-1.2 6.4-3.8 9c-2.6-2.6-3.8-5.6-3.8-9S9.4 5.6 12 3z"/>',
 'truck': '<path d="M3 6h11v10H3z"/><path d="M14 9h4l3 3v4h-7"/><circle cx="7" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/>',
 'coins': '<ellipse cx="9" cy="7" rx="6" ry="2.6"/><path d="M3 7v5c0 1.4 2.7 2.6 6 2.6s6-1.2 6-2.6V7"/><path d="M9 14.6V17c0 1.4 2.7 2.6 6 2.6s6-1.2 6-2.6v-5c0-1.4-2.7-2.6-6-2.6"/>',
 'grid': '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
 'users': '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.6 3.4-5.5 6.5-5.5s5.7 1.9 6.5 5.5"/><circle cx="17" cy="9" r="2.6"/><path d="M16 14.6c2.6.1 4.6 1.8 5.3 4.6"/>',
 'tag': '<path d="M3 12V4a1 1 0 0 1 1-1h8l9 9-9 9z"/><circle cx="7.5" cy="7.5" r="1.6"/>',
 'shield': '<path d="M12 3l8 3v6c0 4.6-3.3 8.1-8 9-4.7-.9-8-4.4-8-9V6z"/><path d="M8.5 12l2.4 2.4 4.6-4.8"/>',
 'back': '<path d="M15 5l-7 7 7 7"/>',
}
def svg(name, color, size=18, sw=1.8):
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{ICON[name]}</svg>'

CSS = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;background:{BG};font-family:Inter,sans-serif;color:{INK};position:relative;overflow:hidden;font-feature-settings:'cv11','ss01'}}
body:before{{content:'';position:absolute;inset:0;background:
  radial-gradient(900px 520px at 78% -10%,rgba(123,140,255,.22),rgba(123,140,255,0) 60%),
  radial-gradient(700px 480px at 35% 115%,rgba(34,225,195,.14),rgba(34,225,195,0) 60%),
  radial-gradient(520px 360px at 105% 70%,rgba(181,123,255,.14),rgba(181,123,255,0) 60%)}}
body:after{{content:'';position:absolute;inset:0;background-image:radial-gradient(rgba(255,255,255,.05) 1px,transparent 1px);background-size:22px 22px;mask-image:linear-gradient(180deg,rgba(0,0,0,.9),rgba(0,0,0,.2))}}
.rail{{position:absolute;left:0;top:0;width:{RAIL}px;height:{H}px;background:linear-gradient(180deg,rgba(10,18,44,.92),rgba(6,11,26,.96));border-right:1px solid rgba(123,140,255,.16);color:#fff;z-index:2;overflow:hidden}}
.rail:after{{content:'';position:absolute;left:-80px;top:-90px;width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,rgba(123,140,255,.30),rgba(123,140,255,0) 65%)}}
.rail:before{{content:'';position:absolute;left:-60px;bottom:-120px;width:280px;height:280px;border-radius:50%;background:radial-gradient(circle,rgba(34,225,195,.16),rgba(34,225,195,0) 65%)}}
.brand{{position:absolute;left:20px;top:22px;display:flex;align-items:center;gap:10px;z-index:3}}
.logo{{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,{INDIGO},{TEAL});display:flex;align-items:center;justify-content:center;box-shadow:0 0 18px rgba(34,225,195,.45)}}
.bt1{{font-size:12.5px;font-weight:800;letter-spacing:1.6px}} .bt2{{font-size:10px;letter-spacing:2.4px;font-weight:700;margin-top:1px;background:linear-gradient(90deg,{TEAL},{INDIGO});-webkit-background-clip:text;color:transparent}}
.sect{{position:absolute;left:22px;top:92px;font-size:9px;letter-spacing:1.8px;color:#5E6C96;font-weight:700;z-index:3}}
.nav{{position:absolute;left:12px;width:176px;height:40px;border-radius:10px;display:flex;align-items:center;gap:11px;padding-left:12px;font-size:12.5px;white-space:nowrap;color:#A7B3D6;font-weight:500;z-index:3}}
.nav.on{{background:linear-gradient(90deg,rgba(34,225,195,.18),rgba(123,140,255,.10));color:#fff;font-weight:600;border:1px solid rgba(34,225,195,.28);box-shadow:0 0 22px -6px rgba(34,225,195,.5)}}
.nav.on:before{{content:'';position:absolute;left:-13px;top:9px;width:4px;height:22px;border-radius:0 3px 3px 0;background:{TEAL};box-shadow:0 0 10px {TEAL}}}
.hint{{position:absolute;left:20px;width:160px;font-size:10px;line-height:1.45;color:#7F8DB5;z-index:3}}
.hint b{{color:#E9EEFC;font-weight:600}}
.foot{{position:absolute;left:20px;bottom:18px;width:164px;font-size:8.5px;line-height:1.5;color:#5E6C96;z-index:3}}
.foot b{{color:#A7B3D6;font-weight:600}}
.h1{{position:absolute;left:{X0}px;top:14px;font-size:24px;font-weight:800;letter-spacing:-.4px;background:linear-gradient(90deg,#FFFFFF 30%,#B9C4FF);-webkit-background-clip:text;color:transparent;z-index:2}}
.h2{{position:absolute;left:{X0}px;top:47px;font-size:11.5px;color:{MUTED};z-index:2}}
.slab{{position:absolute;top:10px;font-size:9px;letter-spacing:1.2px;color:#6F7DA6;font-weight:700;z-index:2}}
.pill{{position:absolute;top:24px;height:34px;border-radius:9px;background:{CARD};border:1px solid rgba(123,140,255,.22);z-index:2}}
.card{{position:absolute;background:{CARD};border-radius:16px;border:1px solid rgba(140,160,255,.14);box-shadow:0 18px 40px -22px rgba(0,0,0,.8),inset 0 1px 0 rgba(255,255,255,.06);z-index:2;overflow:hidden}}
.card:after{{content:'';position:absolute;left:18px;right:18px;top:0;height:1px;background:linear-gradient(90deg,rgba(255,255,255,0),rgba(160,175,255,.45),rgba(255,255,255,0))}}
.kpi{{background:linear-gradient(160deg,rgba(24,38,74,.98),{CARD} 70%)}}
.kglow{{position:absolute;right:-40px;top:-50px;width:150px;height:150px;border-radius:50%;opacity:.28}}
.kbar{{position:absolute;left:0;top:14px;width:3px;height:22px;border-radius:0 3px 3px 0}}
.pt{{position:absolute;left:18px;top:13px;font-size:13px;font-weight:650;color:#F2F5FF}}
.ps{{position:absolute;left:18px;top:31px;font-size:10px;color:{MUTED}}}
.kl{{position:absolute;left:16px;top:13px;font-size:10px;letter-spacing:.9px;color:#9AA8D0;font-weight:700;text-transform:uppercase}}
.kdot{{position:absolute;right:14px;top:12px;width:24px;height:24px;border-radius:7px}}
"""
ACC = [INDIGO, TEAL, VIOLET, CORAL, AMBER]
def page_html(name):
    p = PAGES[name]
    h = [f'<div class="rail"><div class="brand"><div class="logo">{svg("globe","#fff",17,2.2)}</div><div><div class="bt1">{BRAND1}</div><div class="bt2">{BRAND2}</div></div></div>',
         '<div class="sect">DASHBOARD</div>']
    for i, (key, label, icon) in enumerate(NAV):
        on = key == name
        h.append(f'<div class="nav{" on" if on else ""}" style="top:{110+i*46}px">{svg(icon, "#fff" if on else "#9FB0D6")}<span>{label}</span></div>')
    if name == 'profile':
        h.append(f'<div class="nav on" style="top:{110+len(NAV)*46+18}px">{svg("globe","#fff")}<span>Country profile</span></div>')
    h.append(f'<div class="hint" style="top:{110+len(NAV)*46+(80 if name=="profile" else 26)}px">{HINT}</div>')
    h.append(f'<div class="foot">{FOOT}</div></div>')
    if p['title']: h.append(f'<div class="h1">{p["title"]}</div>')
    h.append(f'<div class="h2">{p["sub"]}</div>')
    if name != 'profile':
        for i, lab in enumerate(SLICER_LABELS):
            x = 760 + i * 172
            h.append(f'<div class="slab" style="left:{x+2}px">{lab}</div><div class="pill" style="left:{x}px;width:164px"></div>')
    else:
        h.append(f'<div class="pill" style="left:{X1-120}px;width:120px"></div>')
    if p['kpis']:
        for i, ((x, y, w, hh), lab) in enumerate(zip(tiles(len(p['kpis'])), p['kpis'])):
            c = ACC[i % len(ACC)]
            h.append(f'<div class="card kpi" style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px"><div class="kglow" style="background:radial-gradient(circle,{c},transparent 65%)"></div><div class="kbar" style="background:{c};box-shadow:0 0 10px {c}"></div><div class="kl">{lab}</div><div class="kdot" style="background:{c}22;border:1px solid {c}55"><div style="position:absolute;left:7px;top:7px;width:8px;height:8px;border-radius:50%;background:{c};box-shadow:0 0 8px {c}"></div></div></div>')
    for key, (x, y, w, hh, t, s) in p['panels'].items():
        h.append(f'<div class="card" style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px"><div class="pt">{t}</div><div class="ps">{s}</div></div>')
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(h)}</body></html>'

TOOLTIP_CSS = CSS.replace(f"width:{W}px;height:{H}px", "width:320px;height:200px")
def tooltip_html():
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{TOOLTIP_CSS} body{{background:#fff}}</style></head><body><div style="position:absolute;inset:0;background:linear-gradient(135deg,#0A1330,#121F4A)"></div><div style="position:absolute;right:-60px;top:-60px;width:200px;height:200px;border-radius:50%;background:radial-gradient(circle,rgba(34,225,195,.35),transparent 65%)"></div><div style="position:absolute;left:14px;top:54px;right:14px;bottom:12px;border-radius:10px;background:{CARD};border:1px solid rgba(140,160,255,.18)"></div></body></html>'

async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=2)
        for name in PAGES:
            await pg.set_content(page_html(name)); await pg.wait_for_timeout(200)
            await pg.screenshot(path=str(OUT / f'bg_{name}.png'))
        pg2 = await b.new_page(viewport={'width': 320, 'height': 200}, device_scale_factor=2)
        await pg2.set_content(tooltip_html()); await pg2.screenshot(path=str(OUT / 'bg_tooltip.png'))
        await b.close()
asyncio.run(main())
print('ok')
